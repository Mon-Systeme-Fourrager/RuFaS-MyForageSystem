"""Render style-gate findings in human, JSON, and GitHub-annotation formats."""

from __future__ import annotations

import json
from collections.abc import Iterable

from .violation import Violation


def sort_violations(violations: Iterable[Violation]) -> list[Violation]:
    """Return findings ordered by (path, line, code) for stable output.

    Parameters
    ----------
    violations : iterable of Violation
        Findings to order.

    Returns
    -------
    list of Violation
        Deterministically sorted findings.
    """
    return sorted(violations, key=Violation.sort_key)


def render_human(violations: list[Violation]) -> str:
    """Render findings as a grouped, path-first text report.

    Parameters
    ----------
    violations : list of Violation
        Findings to render.

    Returns
    -------
    str
        Multi-line report, or a success line when there are no findings.
    """
    if not violations:
        return "MSF style gate: no new-code violations."
    lines = [f"MSF style gate: {len(violations)} new-code violation(s):", ""]
    current_path = ""
    for violation in violations:
        if violation.path != current_path:
            current_path = violation.path
            lines.append(current_path)
        lines.append(f"  {violation.line:>5}  {violation.code:<10} {violation.message}")
    lines.append("")
    lines.append("These apply to added/changed lines only. Fix them or, if genuinely a false")
    lines.append("positive, discuss before suppressing (see tools/msf_style/STYLE_RULES.md).")
    return "\n".join(lines)


def render_github(violations: list[Violation]) -> str:
    """Render findings as GitHub Actions ``::error`` workflow annotations.

    Parameters
    ----------
    violations : list of Violation
        Findings to render.

    Returns
    -------
    str
        One annotation command per finding.
    """
    out = []
    for violation in violations:
        message = violation.message.replace("\n", " ")
        out.append(f"::error file={violation.path},line={violation.line}::[{violation.code}] {message}")
    return "\n".join(out)


def render_json(violations: list[Violation]) -> str:
    """Render findings as a JSON array.

    Parameters
    ----------
    violations : list of Violation
        Findings to render.

    Returns
    -------
    str
        JSON document with one object per finding.
    """
    payload = [
        {"path": v.path, "line": v.line, "code": v.code, "message": v.message, "source": v.source} for v in violations
    ]
    return json.dumps(payload, indent=2)


def render(violations: list[Violation], fmt: str) -> str:
    """Dispatch to the renderer named by ``fmt``.

    Parameters
    ----------
    violations : list of Violation
        Findings to render.
    fmt : str
        One of ``"human"``, ``"github"``, ``"json"``. Any other value falls back to
        the human renderer.

    Returns
    -------
    str
        The rendered report.
    """
    if fmt == "github":
        return render_github(violations)
    if fmt == "json":
        return render_json(violations)
    return render_human(violations)
