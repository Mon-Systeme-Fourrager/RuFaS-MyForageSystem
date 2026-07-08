"""Per-file ``mypy --strict`` pass closing the count-based ratchet hole.

The existing CI ratchet compares the *total* mypy error count against the base branch,
so newly added untyped code inside an already-error-carrying module slips through. This
runs mypy on the changed files and reports errors on added lines only.
"""

from __future__ import annotations

import re
import subprocess

from .violation import Violation

MYPY_ROOTS: tuple[str, ...] = ("RUFAS/", "tests/")
MYPY_LINE = re.compile(r"^(?P<file>[^:]+):(?P<line>\d+):(?:\d+:)?\s*error:\s*(?P<msg>.*?)(?:\s*\[(?P<code>[^\]]+)\])?$")


def mypy_available() -> bool:
    """Return whether a ``mypy`` executable is on PATH.

    Returns
    -------
    bool
        ``True`` when ``mypy --version`` succeeds.
    """
    try:
        subprocess.run(["mypy", "--version"], capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return False
    return True


def _eligible(paths: list[str]) -> list[str]:
    return [p for p in paths if p.endswith(".py") and (p == "main.py" or p.startswith(MYPY_ROOTS))]


def run_mypy(paths: list[str]) -> list[Violation]:
    """Type-check changed model/test files and return per-line errors.

    Parameters
    ----------
    paths : list of str
        Changed files; only ``main.py`` and files under ``RUFAS/``/``tests/`` are
        checked (mirroring the project's mypy scope).

    Returns
    -------
    list of Violation
        One finding per mypy error line; empty when nothing is eligible.
    """
    targets = _eligible(paths)
    if not targets:
        return []
    result = subprocess.run(
        ["mypy", "--follow-imports=silent", *targets],
        capture_output=True,
        text=True,
        check=False,
    )
    return _parse_mypy_output(result.stdout)


def _parse_mypy_output(raw: str) -> list[Violation]:
    findings: list[Violation] = []
    for line in raw.splitlines():
        match = MYPY_LINE.match(line)
        if match is None:
            continue
        code = match.group("code") or "error"
        findings.append(
            Violation(match.group("file"), int(match.group("line")), f"mypy:{code}", match.group("msg").strip(), "mypy")
        )
    return findings
