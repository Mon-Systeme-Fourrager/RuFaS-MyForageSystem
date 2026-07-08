"""Run Ruff with the dedicated MSF config and adapt its JSON output.

Ruff is not diff-aware, so it lints whole files; the caller filters findings to the
new-code perimeter. The narrow rule set lives in ``ruff_msf.toml`` beside this module.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .violation import Violation

CONFIG_PATH = Path(__file__).with_name("ruff_msf.toml")


def ruff_available() -> bool:
    """Return whether a ``ruff`` executable is on PATH.

    Returns
    -------
    bool
        ``True`` when ``ruff --version`` succeeds.
    """
    try:
        subprocess.run(["ruff", "--version"], capture_output=True, text=True, check=True, timeout=10)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False
    return True


def run_ruff(paths: list[str]) -> list[Violation]:
    """Lint ``paths`` with the MSF Ruff config and return findings.

    Parameters
    ----------
    paths : list of str
        Python files to lint (already restricted to changed files by the caller).

    Returns
    -------
    list of Violation
        One finding per Ruff diagnostic; empty when there are no Python paths.
    """
    python_paths = [p for p in paths if p.endswith(".py")]
    if not python_paths:
        return []
    try:
        result = subprocess.run(
            [
                "ruff",
                "check",
                "--config",
                str(CONFIG_PATH),
                "--output-format",
                "json",
                "--force-exclude",
                *python_paths,
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return []
    return _parse_ruff_json(result.stdout)


def _parse_ruff_json(raw: str) -> list[Violation]:
    """Convert Ruff's JSON diagnostics into :class:`Violation` objects.

    Parameters
    ----------
    raw : str
        Raw stdout from ``ruff check --output-format json``.

    Returns
    -------
    list of Violation
        One finding per well-formed diagnostic; empty on blank or malformed output.
    """
    if not raw.strip():
        return []
    try:
        diagnostics = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(diagnostics, list):
        return []
    findings: list[Violation] = []
    for item in diagnostics:
        violation = _to_violation(item)
        if violation is not None:
            findings.append(violation)
    return findings


def _to_violation(item: object) -> Violation | None:
    """Map one Ruff diagnostic dict to a :class:`Violation`.

    Parameters
    ----------
    item : object
        A single decoded diagnostic (expected to be a dict with a ``location``).

    Returns
    -------
    Violation or None
        The finding, or ``None`` when the item lacks a usable location.
    """
    if not isinstance(item, dict):
        return None
    location = item.get("location")
    if not isinstance(location, dict) or "row" not in location:
        return None
    row = int(location["row"])
    code = str(item.get("code") or "RUFF")
    message = str(item.get("message") or "")
    filename = str(item.get("filename") or "")
    return Violation(_relativize(filename), row, code, message, "ruff")


def _relativize(filename: str) -> str:
    """Return ``filename`` relative to the working directory, using forward slashes.

    Parameters
    ----------
    filename : str
        Absolute or relative path reported by Ruff.

    Returns
    -------
    str
        A repository-relative, forward-slash path (unchanged when it is outside the
        working directory).
    """
    try:
        relative = str(Path(filename).resolve().relative_to(Path.cwd()))
    except ValueError:
        relative = filename
    return relative.replace("\\", "/")
