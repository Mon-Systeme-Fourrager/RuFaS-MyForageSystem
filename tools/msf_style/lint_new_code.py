"""Diff-aware MSF style gate — command-line entry point.

Runs Ruff (narrow config), the project-specific AST/text checks, changelog format
checks and (optionally) a per-file ``mypy`` pass, then keeps only the findings that
fall on lines the branch added or changed versus its integration branch.

Examples
--------
Gate the whole branch against ``origin/dev-msf`` including the mypy pass::

    python -m tools.msf_style.lint_new_code --base origin/dev-msf --mypy

Fast in-session check of a single just-edited file (used by the hook)::

    python -m tools.msf_style.lint_new_code --paths RUFAS/biophysical/animal/pen.py --no-mypy
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import changelog_check, custom_checks, mypy_checker, reporting, ruff_checker
from .diff_scope import FileScope, compute_scopes, resolve_base
from .violation import Violation


def _read_text(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _select_scopes(scopes: dict[str, FileScope], only: list[str] | None) -> dict[str, FileScope]:
    if not only:
        return scopes
    wanted = {_normalize_only(p) for p in only}
    return {path: scope for path, scope in scopes.items() if path in wanted}


def _normalize_only(path: str) -> str:
    """Normalize a ``--paths`` entry for comparison against diff-scope keys.

    Parameters
    ----------
    path : str
        A raw entry from ``--paths``.

    Returns
    -------
    str
        The path with backslashes converted to forward slashes and a leading
        ``"./"`` (but not a leading ``"."`` from a dotfile) removed.
    """
    normalized = path.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _collect_ruff(python_paths: list[str]) -> list[Violation]:
    if not python_paths or not ruff_checker.ruff_available():
        return []
    return ruff_checker.run_ruff(python_paths)


def _collect_custom(scopes: dict[str, FileScope]) -> list[Violation]:
    findings: list[Violation] = []
    for path in scopes:
        if not path.endswith(".py"):
            continue
        text = _read_text(path)
        if text is not None:
            findings.extend(custom_checks.check_python_file(path, text))
    return findings


def _collect_changelog(scopes: dict[str, FileScope]) -> list[Violation]:
    findings: list[Violation] = []
    for path, scope in scopes.items():
        if path.rsplit("/", 1)[-1] != changelog_check.CHANGELOG_NAME:
            continue
        text = _read_text(path)
        if text is not None:
            findings.extend(changelog_check.check_changelog(path, text, scope))
    return findings


def _collect_mypy(python_paths: list[str], enabled: bool) -> list[Violation]:
    if not enabled or not python_paths or not mypy_checker.mypy_available():
        return []
    return mypy_checker.run_mypy(python_paths)


def _gather(scopes: dict[str, FileScope], run_mypy: bool) -> list[Violation]:
    python_paths = [p for p in scopes if p.endswith(".py")]
    findings = _collect_ruff(python_paths)
    findings += _collect_custom(scopes)
    findings += _collect_changelog(scopes)
    findings += _collect_mypy(python_paths, run_mypy)
    return findings


def _filter_to_scope(findings: list[Violation], scopes: dict[str, FileScope]) -> list[Violation]:
    kept: list[Violation] = []
    for finding in findings:
        scope = scopes.get(finding.path)
        if scope is not None and scope.in_scope(finding.line):
            kept.append(finding)
    return kept


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="msf-style-gate", description="Diff-aware RuFaS style gate.")
    parser.add_argument("--base", default=None, help="Base ref to diff against (default: auto-detect dev-msf/dev).")
    parser.add_argument("--paths", nargs="*", default=None, help="Restrict to these changed files (hook use).")
    parser.add_argument("--format", default="human", choices=["human", "github", "json"], help="Output format.")
    mypy_group = parser.add_mutually_exclusive_group()
    mypy_group.add_argument("--mypy", dest="mypy", action="store_true", help="Run the per-file mypy pass.")
    mypy_group.add_argument("--no-mypy", dest="mypy", action="store_false", help="Skip the per-file mypy pass.")
    parser.set_defaults(mypy=True)
    return parser


def run(argv: list[str] | None = None) -> int:
    """Execute the gate and return a process exit code.

    Parameters
    ----------
    argv : list of str or None, optional
        Argument vector (defaults to ``sys.argv`` when ``None``).

    Returns
    -------
    int
        ``0`` when there are no in-scope findings, ``1`` when there are, ``2`` when no
        base ref could be resolved.
    """
    args = _build_parser().parse_args(argv)
    base = resolve_base(args.base)
    if base is None:
        sys.stderr.write("MSF style gate: no base ref (tried dev-msf/dev). Nothing to compare.\n")
        return 2
    scopes = _select_scopes(compute_scopes(base), args.paths)
    if not scopes:
        sys.stdout.write(reporting.render([], args.format) + "\n")
        return 0
    findings = _filter_to_scope(_gather(scopes, args.mypy), scopes)
    ordered = reporting.sort_violations(findings)
    stream = sys.stderr if ordered else sys.stdout
    stream.write(reporting.render(ordered, args.format) + "\n")
    return 1 if ordered else 0


def main() -> None:
    """Console entry point that exits with the gate's status code."""
    raise SystemExit(run())


if __name__ == "__main__":
    main()
