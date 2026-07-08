"""Format checks for ``changelog.md`` entries added by a branch.

RuFaS requires a changelog entry on every PR; CI already fails when the file is
untouched. These checks catch the *content* mistakes reviewers repeatedly flag:
``TBD`` placeholders, a single PR tagged both ``[OutputChange]`` and
``[NoOutputChange]``, and duplicate bullets for the same PR number.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

from .diff_scope import FileScope
from .violation import Violation

CHANGELOG_NAME = "changelog.md"
PR_BULLET = re.compile(r"^\s*[-*]\s*\[(\d+)\]\(")
TBD_TOKEN = re.compile(r"\bTBD\b|\(TBD\)|\[TBD\]")


def check_changelog(path: str, text: str, scope: FileScope) -> list[Violation]:
    """Validate changelog bullets that the branch adds or changes.

    Parameters
    ----------
    path : str
        Path of the changelog file (only ``changelog.md`` is processed).
    text : str
        Full file text.
    scope : FileScope
        New-code perimeter; only added/changed lines are judged, except duplicate
        detection which scans the whole file but reports at the added occurrence.

    Returns
    -------
    list of Violation
        Changelog format findings.
    """
    path = path.replace("\\", "/")
    if path.rsplit("/", 1)[-1] != CHANGELOG_NAME:
        return []
    lines = text.splitlines()
    findings = list(_line_level_checks(path, lines, scope))
    findings.extend(_duplicate_pr_numbers(path, lines, scope))
    return findings


def _line_level_checks(path: str, lines: list[str], scope: FileScope) -> Iterator[Violation]:
    """Yield per-line changelog findings (TBD placeholder, contradictory tags).

    Parameters
    ----------
    path : str
        Changelog path (stamped onto findings).
    lines : list of str
        The changelog's lines.
    scope : FileScope
        New-code perimeter; only added/changed lines are judged.

    Yields
    ------
    Violation
        ``MSF050`` for a TBD placeholder, ``MSF051`` for both output tags on one line.
    """
    for index, line in enumerate(lines, start=1):
        if not scope.in_scope(index):
            continue
        if TBD_TOKEN.search(line):
            yield Violation(
                path,
                index,
                "MSF050",
                "Replace the 'TBD' placeholder with the real PR number and link before merge.",
                "changelog",
            )
        if "[OutputChange]" in line and "[NoOutputChange]" in line:
            yield Violation(
                path,
                index,
                "MSF051",
                "A changelog entry tags the PR both [OutputChange] and [NoOutputChange] — keep exactly one.",
                "changelog",
            )


def _duplicate_pr_numbers(path: str, lines: list[str], scope: FileScope) -> Iterator[Violation]:
    """Yield ``MSF052`` when a PR number appears in more than one changelog bullet.

    Parameters
    ----------
    path : str
        Changelog path (stamped onto findings).
    lines : list of str
        The changelog's lines.
    scope : FileScope
        New-code perimeter; a duplicate is reported only when its second occurrence
        falls on an added/changed line.

    Yields
    ------
    Violation
        ``MSF052`` for each in-scope duplicate PR bullet.
    """
    seen: dict[str, int] = {}
    for index, line in enumerate(lines, start=1):
        match = PR_BULLET.match(line)
        if not match:
            continue
        pr_number = match.group(1)
        if pr_number in seen and scope.in_scope(index):
            yield Violation(
                path,
                index,
                "MSF052",
                f"Duplicate changelog bullet for PR #{pr_number} (first at line "
                f"{seen[pr_number]}) — keep a single entry per PR.",
                "changelog",
            )
        seen.setdefault(pr_number, index)
