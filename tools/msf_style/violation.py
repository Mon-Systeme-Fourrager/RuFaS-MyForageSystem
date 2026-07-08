"""Shared value object emitted by every checker."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Violation:
    """A single style-gate finding anchored to a file and line.

    Parameters
    ----------
    path : str
        Repository-relative path of the offending file.
    line : int
        1-indexed line the finding anchors to.
    code : str
        Machine-readable rule identifier (e.g. ``"MSF001"`` or a Ruff code like
        ``"UP037"``).
    message : str
        Human-readable, actionable description of the problem and its fix.
    source : str
        Which checker produced the finding: ``"ruff"``, ``"custom"``,
        ``"changelog"`` or ``"mypy"``.
    """

    path: str
    line: int
    code: str
    message: str
    source: str

    def sort_key(self) -> tuple[str, int, str]:
        """Return a stable ordering key (path, line, code).

        Returns
        -------
        tuple of (str, int, str)
            Tuple used to sort findings deterministically for display.
        """
        return (self.path, self.line, self.code)
