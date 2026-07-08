"""Unit tests for the changelog format checks."""

from __future__ import annotations

from tools.msf_style.changelog_check import check_changelog
from tools.msf_style.diff_scope import FileScope


def _all_new(path: str) -> FileScope:
    return FileScope(path=path, is_new=True)


def test_tbd_placeholder_flagged() -> None:
    """A TBD placeholder link raises MSF050."""
    text = "- [TBD](TBD) - [minor change] [Animal Module] Something.\n"
    codes = [v.code for v in check_changelog("changelog.md", text, _all_new("changelog.md"))]
    assert "MSF050" in codes


def test_contradictory_output_tags_flagged() -> None:
    """One bullet tagged both output states raises MSF051."""
    text = "- [40](url) - [minor change] [OutputChange] [NoOutputChange] Something.\n"
    codes = [v.code for v in check_changelog("changelog.md", text, _all_new("changelog.md"))]
    assert "MSF051" in codes


def test_duplicate_pr_bullets_flagged() -> None:
    """Two bullets for the same PR number raise MSF052."""
    text = "- [41](https://x/41) - first entry.\n- [41](https://x/41) - duplicate entry.\n"
    codes = [v.code for v in check_changelog("changelog.md", text, _all_new("changelog.md"))]
    assert "MSF052" in codes


def test_clean_entry_has_no_findings() -> None:
    """A well-formed single entry produces no findings (normal case)."""
    text = "- [42](https://x/42) - [minor change] [Animal Module] [NoOutputChange] Add beef ration.\n"
    assert check_changelog("changelog.md", text, _all_new("changelog.md")) == []


def test_non_changelog_file_ignored() -> None:
    """The checker only processes ``changelog.md`` (invalid target)."""
    text = "- [TBD](TBD) still here\n"
    assert check_changelog("README.md", text, _all_new("README.md")) == []


def test_out_of_scope_lines_ignored() -> None:
    """A TBD on a legacy (out-of-scope) line is not flagged (edge case)."""
    text = "- [TBD](TBD) legacy line\n"
    scope = FileScope(path="changelog.md", is_new=False, added_lines=set())
    assert check_changelog("changelog.md", text, scope) == []
