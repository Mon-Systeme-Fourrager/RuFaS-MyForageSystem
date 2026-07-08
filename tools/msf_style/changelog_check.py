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
