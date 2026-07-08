"""Unit tests for output parsing (Ruff, mypy) and rendering."""

from __future__ import annotations

from tools.msf_style import mypy_checker, reporting, ruff_checker
from tools.msf_style.violation import Violation


def test_ruff_json_parsed_to_violations() -> None:
    """Valid Ruff JSON becomes Violation objects with row and code."""
    raw = (
        '[{"code": "UP037", "message": "Remove quotes", '
        '"filename": "RUFAS/x.py", "location": {"row": 12, "column": 5}}]'
    )
    violations = ruff_checker._parse_ruff_json(raw)
    assert len(violations) == 1
    assert violations[0].code == "UP037"
    assert violations[0].line == 12
    assert violations[0].source == "ruff"


def test_ruff_empty_output_is_empty_list() -> None:
    """Empty Ruff output yields no findings (edge case)."""
    assert ruff_checker._parse_ruff_json("") == []


def test_ruff_malformed_json_is_empty_list() -> None:
    """Malformed Ruff output is tolerated and yields nothing (invalid input)."""
    assert ruff_checker._parse_ruff_json("not json") == []


def test_ruff_item_without_location_skipped() -> None:
    """A diagnostic missing a location is skipped (invalid input)."""
    assert ruff_checker._parse_ruff_json('[{"code": "X", "message": "m"}]') == []


def test_mypy_error_line_parsed() -> None:
    """A mypy error line becomes a Violation with the pinned code."""
    raw = "RUFAS/x.py:42:5: error: Incompatible return value type  [return-value]\n"
    violations = mypy_checker._parse_mypy_output(raw)
    assert len(violations) == 1
    assert violations[0].line == 42
    assert violations[0].code == "mypy:return-value"


def test_mypy_note_lines_ignored() -> None:
    """Non-error mypy lines (notes, summaries) are ignored (edge case)."""
    raw = "RUFAS/x.py:1:1: note: some note\nFound 0 errors\n"
    assert mypy_checker._parse_mypy_output(raw) == []


def test_render_human_reports_success_when_empty() -> None:
    """The human renderer states success on an empty finding list."""
    assert "no new-code violations" in reporting.render_human([])


def test_render_github_emits_error_annotations() -> None:
    """The GitHub renderer emits an ``::error`` command per finding."""
    violation = Violation("RUFAS/x.py", 3, "MSF001", "bare coefficient", "custom")
    out = reporting.render_github([violation])
    assert out.startswith("::error file=RUFAS/x.py,line=3::")
    assert "MSF001" in out


def test_sort_violations_orders_by_path_line_code() -> None:
    """Findings sort deterministically by (path, line, code)."""
    first = Violation("a.py", 5, "MSF001", "m", "custom")
    second = Violation("a.py", 2, "MSF010", "m", "custom")
    third = Violation("b.py", 1, "MSF001", "m", "custom")
    ordered = reporting.sort_violations([first, third, second])
    assert [v.line for v in ordered] == [2, 5, 1]


def test_render_json_roundtrips_fields() -> None:
    """The JSON renderer includes every finding field."""
    violation = Violation("RUFAS/x.py", 7, "MSF011", "guard None", "custom")
    payload = reporting.render_json([violation])
    assert '"code": "MSF011"' in payload
    assert '"line": 7' in payload
