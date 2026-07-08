"""Resolve the "new code" perimeter from ``git diff`` output.

The gate never judges legacy lines. For an existing file only the lines a branch adds
or changes (versus the merge-base with its integration branch) are in scope; a brand
new file is entirely in scope.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field

DEFAULT_BASE_CANDIDATES: tuple[str, ...] = ("origin/dev-msf", "dev-msf", "origin/dev", "dev")


@dataclass
class FileScope:
    """The in-scope (added/changed) lines of one changed file.

    Parameters
    ----------
    path : str
        Repository-relative path of the file.
    is_new : bool
        ``True`` when the file is added by the branch (every line is in scope).
    added_lines : set of int
        1-indexed lines the branch adds or changes (ignored when ``is_new``).
    """

    path: str
    is_new: bool
    added_lines: set[int] = field(default_factory=set)

    def in_scope(self, line: int) -> bool:
        """Return whether ``line`` belongs to the new-code perimeter.

        Parameters
        ----------
        line : int
            1-indexed line number to test.

        Returns
        -------
        bool
            ``True`` for a new file or a line the branch added/changed.
        """
        return self.is_new or line in self.added_lines


def _rev_parse_ok(ref: str) -> bool:
    """Return whether ``ref`` resolves to an existing git object.

    Parameters
    ----------
    ref : str
        A git ref (branch, tag, or SHA) to verify.

    Returns
    -------
    bool
        ``True`` when ``git rev-parse --verify`` succeeds.
    """
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def resolve_base(explicit: str | None = None) -> str | None:
    """Pick the first existing base ref to diff against.

    Parameters
    ----------
    explicit : str or None, optional
        A caller-supplied ref (from ``--base`` or CI ``github.base_ref``). When it
        exists it wins; otherwise a short list of fork/upstream integration branches
        is tried in order.

    Returns
    -------
    str or None
        The resolved ref, or ``None`` when nothing usable exists (the caller should
        then treat the diff as empty rather than scan the whole repository).
    """
    candidates = [explicit, *DEFAULT_BASE_CANDIDATES] if explicit else list(DEFAULT_BASE_CANDIDATES)
    for candidate in candidates:
        if candidate and _rev_parse_ok(candidate):
            return candidate
    return None


def _merge_base(base: str) -> str:
    """Return the merge-base of ``base`` and ``HEAD`` (or ``base`` on failure).

    Parameters
    ----------
    base : str
        The base ref to fork from.

    Returns
    -------
    str
        The merge-base SHA, or ``base`` itself when git cannot compute one.
    """
    result = subprocess.run(
        ["git", "merge-base", base, "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    resolved = result.stdout.strip()
    return resolved if result.returncode == 0 and resolved else base


def _raw_diff(against: str) -> str:
    """Return the zero-context unified diff of the working tree versus ``against``.

    Parameters
    ----------
    against : str
        The ref (typically a merge-base) to diff against, limited to ``*.py``/``*.md``.

    Returns
    -------
    str
        Raw ``git diff`` output.
    """
    result = subprocess.run(
        ["git", "diff", "--unified=0", "--no-color", against, "--", "*.py", "*.md"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout


def _untracked_files() -> list[str]:
    """Return not-yet-staged ``*.py``/``*.md`` files, honouring ``.gitignore``.

    Returns
    -------
    list of str
        Repository-relative paths of untracked, non-ignored files.
    """
    result = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "--", "*.py", "*.md"],
        capture_output=True,
        text=True,
        check=False,
    )
    return [line for line in result.stdout.splitlines() if line]


def _added_range(hunk_header: str) -> range:
    """Return the added-line numbers encoded in a unified-diff hunk header.

    Parameters
    ----------
    hunk_header : str
        A ``@@ -a,b +c,d @@`` header line.

    Returns
    -------
    range
        The ``c .. c+d-1`` range of lines the hunk adds (``d`` defaults to 1).
    """
    plus = hunk_header.split("+", 1)[1].split(" ", 1)[0]
    start_str, _, count_str = plus.partition(",")
    start = int(start_str)
    count = int(count_str) if count_str else 1
    return range(start, start + count)


def _strip_prefix(diff_path: str) -> str:
    """Remove a leading ``a/`` or ``b/`` diff prefix from a path.

    Parameters
    ----------
    diff_path : str
        A path as it appears in a diff header.

    Returns
    -------
    str
        The path without its diff prefix.
    """
    if diff_path.startswith(("a/", "b/")):
        return diff_path[2:]
    return diff_path


def _parse_unified_diff(raw: str) -> dict[str, FileScope]:
    """Parse unified-diff text into per-file added-line scopes.

    Parameters
    ----------
    raw : str
        Zero-context unified-diff output.

    Returns
    -------
    dict of str to FileScope
        One scope per changed file; deleted files (``+++ /dev/null``) are omitted.
    """
    scopes: dict[str, FileScope] = {}
    current: FileScope | None = None
    minus_is_devnull = False
    for line in raw.splitlines():
        if line.startswith("--- "):
            minus_is_devnull = line[4:] == "/dev/null"
        elif line.startswith("+++ "):
            current = _open_file_scope(line[4:], minus_is_devnull, scopes)
        elif line.startswith("@@") and current is not None:
            current.added_lines.update(_added_range(line))
    return scopes


def _open_file_scope(plus_path: str, is_new: bool, scopes: dict[str, FileScope]) -> FileScope | None:
    """Register and return a fresh :class:`FileScope` for a diff's ``+++`` path.

    Parameters
    ----------
    plus_path : str
        The ``+++`` path (with its ``b/`` prefix, or ``/dev/null`` for a deletion).
    is_new : bool
        Whether the preceding ``---`` line was ``/dev/null`` (an added file).
    scopes : dict of str to FileScope
        Accumulator the new scope is inserted into.

    Returns
    -------
    FileScope or None
        The registered scope, or ``None`` for a deleted file.
    """
    if plus_path == "/dev/null":
        return None
    path = _strip_prefix(plus_path)
    scope = FileScope(path=path, is_new=is_new)
    scopes[path] = scope
    return scope


def compute_scopes(base: str) -> dict[str, FileScope]:
    """Return the per-file new-code perimeter for the working tree versus ``base``.

    The diff is taken against ``merge-base(base, HEAD)`` so that commits which only
    advanced ``base`` are not miscounted, while uncommitted edits (the in-session hook
    case) are still included.

    Parameters
    ----------
    base : str
        An existing git ref (see :func:`resolve_base`).

    Returns
    -------
    dict of str to FileScope
        Mapping of repository-relative path to its scope. Deleted files are absent;
        untracked (not-yet-staged) files are included as fully new so the in-session
        hook catches them before they are committed.
    """
    scopes = _parse_unified_diff(_raw_diff(_merge_base(base)))
    for path in _untracked_files():
        scopes.setdefault(path, FileScope(path=path, is_new=True))
    return scopes
