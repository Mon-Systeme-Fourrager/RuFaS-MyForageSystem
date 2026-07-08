"""Unit tests for the diff/new-code perimeter parsing."""

from __future__ import annotations

import pytest

from tools.msf_style import diff_scope
from tools.msf_style.diff_scope import FileScope

NEW_FILE_DIFF = """diff --git a/RUFAS/new_mod.py b/RUFAS/new_mod.py
new file mode 100644
--- /dev/null
+++ b/RUFAS/new_mod.py
@@ -0,0 +3 @@
+line one
+line two
+line three
"""

EDIT_DIFF = """diff --git a/RUFAS/existing.py b/RUFAS/existing.py
--- a/RUFAS/existing.py
+++ b/RUFAS/existing.py
@@ -10,0 +11,2 @@ def f():
+added_a
+added_b
@@ -20 +22 @@ def g():
+changed_line
"""


def test_new_file_scope_is_entirely_in_scope() -> None:
    """A file added against /dev/null is marked new and matches any line."""
    scopes = diff_scope._parse_unified_diff(NEW_FILE_DIFF)
    scope = scopes["RUFAS/new_mod.py"]
    assert scope.is_new is True
    assert scope.in_scope(999) is True


def test_edited_file_scopes_only_added_lines() -> None:
    """An edited file marks exactly the added line numbers."""
    scopes = diff_scope._parse_unified_diff(EDIT_DIFF)
    scope = scopes["RUFAS/existing.py"]
    assert scope.is_new is False
    assert scope.added_lines == {11, 12, 22}
    assert scope.in_scope(11) is True
    assert scope.in_scope(13) is False


def test_added_range_defaults_count_to_one() -> None:
    """A hunk header without an explicit count spans a single line (edge case)."""
    assert list(diff_scope._added_range("@@ -20 +22 @@")) == [22]


def test_added_range_uses_explicit_count() -> None:
    """A hunk header with a count spans that many lines."""
    assert list(diff_scope._added_range("@@ -10,0 +11,2 @@")) == [11, 12]


def test_deleted_file_is_absent() -> None:
    """A file deleted (``+++ /dev/null``) produces no scope (invalid target)."""
    deletion = "diff --git a/x.py b/x.py\n--- a/x.py\n+++ /dev/null\n@@ -1 +0,0 @@\n-gone\n"
    assert diff_scope._parse_unified_diff(deletion) == {}


def test_file_scope_in_scope_for_edited_file() -> None:
    """FileScope.in_scope only accepts registered added lines when not new."""
    scope = FileScope(path="a.py", is_new=False, added_lines={5, 6})
    assert scope.in_scope(5) is True
    assert scope.in_scope(7) is False


def test_resolve_base_prefers_first_existing_ref(monkeypatch: pytest.MonkeyPatch) -> None:
    """resolve_base returns the first candidate that git can verify."""
    monkeypatch.setattr(diff_scope, "_rev_parse_ok", lambda ref: ref == "dev-msf")
    assert diff_scope.resolve_base() == "dev-msf"


def test_resolve_base_honours_explicit_ref(monkeypatch: pytest.MonkeyPatch) -> None:
    """An explicit, existing ref wins over the default candidates."""
    monkeypatch.setattr(diff_scope, "_rev_parse_ok", lambda ref: True)
    assert diff_scope.resolve_base("origin/feature") == "origin/feature"


def test_resolve_base_returns_none_when_nothing_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    """resolve_base returns None when no candidate resolves (invalid environment)."""
    monkeypatch.setattr(diff_scope, "_rev_parse_ok", lambda ref: False)
    assert diff_scope.resolve_base() is None


def test_compute_scopes_wires_helpers_and_merges_untracked(monkeypatch: pytest.MonkeyPatch) -> None:
    """compute_scopes parses the diff and adds untracked files as new scopes."""
    diff = "diff --git a/RUFAS/x.py b/RUFAS/x.py\n--- a/RUFAS/x.py\n+++ b/RUFAS/x.py\n@@ -1 +1,2 @@\n+added\n"
    monkeypatch.setattr(diff_scope, "_merge_base", lambda base: "MERGEBASE")
    monkeypatch.setattr(diff_scope, "_raw_diff", lambda against: diff if against == "MERGEBASE" else "")
    monkeypatch.setattr(diff_scope, "_untracked_files", lambda: ["RUFAS/new.py"])
    scopes = diff_scope.compute_scopes("dev-msf")
    assert scopes["RUFAS/x.py"].added_lines == {1, 2}
    assert scopes["RUFAS/new.py"].is_new is True


def test_compute_scopes_untracked_does_not_override_tracked(monkeypatch: pytest.MonkeyPatch) -> None:
    """An untracked entry never overrides a file already parsed from the diff (edge case)."""
    diff = "diff --git a/RUFAS/x.py b/RUFAS/x.py\n--- a/RUFAS/x.py\n+++ b/RUFAS/x.py\n@@ -1 +1,2 @@\n+added\n"
    monkeypatch.setattr(diff_scope, "_merge_base", lambda base: "MB")
    monkeypatch.setattr(diff_scope, "_raw_diff", lambda against: diff)
    monkeypatch.setattr(diff_scope, "_untracked_files", lambda: ["RUFAS/x.py"])
    scopes = diff_scope.compute_scopes("dev-msf")
    assert scopes["RUFAS/x.py"].is_new is False
    assert scopes["RUFAS/x.py"].added_lines == {1, 2}
