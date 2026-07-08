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
        subprocess.run(["ruff", "--version"], capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
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
    result = subprocess.run(
        ["ruff", "check", "--config", str(CONFIG_PATH), "--output-format", "json", "--force-exclude", *python_paths],
        capture_output=True,
        text=True,
        check=False,
    )
    return _parse_ruff_json(result.stdout)


def _parse_ruff_json(raw: str) -> list[Violation]:
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
    try:
        relative = str(Path(filename).resolve().relative_to(Path.cwd()))
    except ValueError:
        relative = filename
    return relative.replace("\\", "/")
