"""Unit tests for the project-specific AST/text checks."""

from __future__ import annotations

from tools.msf_style import custom_checks


def _codes(path: str, text: str) -> list[str]:
    return [v.code for v in custom_checks.check_python_file(path, text)]


def test_magic_float_flagged_in_domain_module() -> None:
    """A bare float coefficient in a biophysical module raises MSF001."""
    source = "def calc(bw: float) -> float:\n    return bw * 0.62\n"
    assert "MSF001" in _codes("RUFAS/biophysical/animal/growth.py", source)


def test_numeric_get_default_flagged_in_domain_module() -> None:
    """A numeric ``.get`` default in a domain module raises MSF002."""
    source = "def read(cfg: dict) -> int:\n    return cfg.get('days', 45)\n"
    assert "MSF002" in _codes("RUFAS/biophysical/animal/animal.py", source)


def test_allowed_floats_not_flagged() -> None:
    """The neutral floats 0.0 and 1.0 never raise MSF001 (edge case)."""
    source = "def scale(x: float) -> float:\n    return x * 1.0 + 0.0\n"
    assert "MSF001" not in _codes("RUFAS/biophysical/animal/growth.py", source)


def test_constants_module_is_exempt_from_magic_numbers() -> None:
    """Coefficients living in a ``*_constants.py`` are exempt (edge case)."""
    source = "AGE_FACTOR: float = 0.85\nBEEF_HCW: float = 0.62\n"
    assert _codes("RUFAS/biophysical/animal/animal_constants.py", source) == []


def test_named_module_constant_not_flagged() -> None:
    """An UPPER_SNAKE assignment of a float is a named constant, not magic."""
    source = "THRESHOLD = 0.62\n"
    assert "MSF001" not in _codes("RUFAS/biophysical/field/soil.py", source)


def test_non_domain_module_floats_not_flagged() -> None:
    """Floats outside biophysical/EEE are out of MSF001 scope (invalid target)."""
    source = "def f() -> float:\n    return 0.62\n"
    assert "MSF001" not in _codes("RUFAS/util.py", source)


def test_get_or_default_flagged() -> None:
    """``config.get(key) or default`` raises MSF010."""
    source = "def read(cfg: dict) -> int:\n    return cfg.get('n') or 10\n"
    assert "MSF010" in _codes("RUFAS/input_manager.py", source)


def test_int_on_possibly_none_get_flagged() -> None:
    """``int(cfg.get(key))`` without a guard raises MSF011."""
    source = "def read(cfg: dict) -> int:\n    return int(cfg.get('n'))\n"
    assert "MSF011" in _codes("RUFAS/input_manager.py", source)


def test_int_on_get_with_none_default_flagged() -> None:
    """``int(cfg.get(key, None))`` still can be None so raises MSF011 (edge case)."""
    source = "def read(cfg: dict) -> int:\n    return int(cfg.get('n', None))\n"
    assert "MSF011" in _codes("RUFAS/input_manager.py", source)


def test_int_on_get_with_numeric_default_not_flagged() -> None:
    """``int(cfg.get(key, 0))`` is None-safe and does not raise MSF011."""
    codes = _codes("RUFAS/input_manager.py", "def read(cfg: dict) -> int:\n    return int(cfg.get('n', 0))\n")
    assert "MSF011" not in codes


def test_mutable_classvar_return_flagged() -> None:
    """Returning a class-level dict without copy raises MSF030."""
    source = (
        "class RationManager:\n"
        "    RATIONS = {'a': 1}\n"
        "    @classmethod\n"
        "    def all_rations(cls) -> dict:\n"
        "        return cls.RATIONS\n"
    )
    assert "MSF030" in _codes("RUFAS/biophysical/animal/ration/ration_manager.py", source)


def test_mutable_classvar_return_with_copy_not_flagged() -> None:
    """Returning ``.copy()`` of the class dict is safe (edge case)."""
    source = (
        "class RationManager:\n"
        "    RATIONS = {'a': 1}\n"
        "    @classmethod\n"
        "    def all_rations(cls) -> dict:\n"
        "        return cls.RATIONS.copy()\n"
    )
    assert "MSF030" not in _codes("RUFAS/biophysical/animal/ration/ration_manager.py", source)


def test_test_class_attr_mock_assignment_flagged() -> None:
    """Direct class-attribute mock assignment in a test raises MSF020."""
    source = "def test_it() -> None:\n    HerdManager.update = MagicMock()\n"
    assert "MSF020" in _codes("tests/test_biophysical/test_animal/test_herd.py", source)


def test_class_attr_mock_outside_tests_not_flagged() -> None:
    """MSF020 is scoped to tests; production code is out of scope (invalid target)."""
    source = "def wire() -> None:\n    HerdManager.update = MagicMock()\n"
    assert "MSF020" not in _codes("RUFAS/simulation_engine.py", source)


def test_noqa_c901_comment_flagged() -> None:
    """A new ``# noqa: C901`` comment raises MSF040."""
    source = "def big():  # noqa: C901\n    pass\n"
    assert "MSF040" in _codes("RUFAS/output_manager.py", source)


def test_noqa_c901_inside_string_not_flagged() -> None:
    """The token inside a string literal is not a real suppression (edge case)."""
    source = 'MESSAGE = "avoid # noqa: C901 here"\n'
    assert "MSF040" not in _codes("RUFAS/output_manager.py", source)


def test_bare_type_ignore_flagged() -> None:
    """A bare ``# type: ignore`` comment raises MSF042."""
    source = "x = untyped()  # type: ignore\n"
    assert "MSF042" in _codes("RUFAS/util.py", source)


def test_coded_type_ignore_not_flagged() -> None:
    """``# type: ignore[code]`` with a specific code is acceptable (edge case)."""
    source = "x = untyped()  # type: ignore[assignment]\n"
    assert "MSF042" not in _codes("RUFAS/util.py", source)


def test_lesson_reference_flagged() -> None:
    """A ``Lesson N`` scaffolding reference raises MSF041."""
    source = "# Lesson 3 taught us to guard this\nx = 1\n"
    assert "MSF041" in _codes("RUFAS/util.py", source)


def test_negative_numeric_get_default_flagged() -> None:
    """A negative ``.get(key, -1)`` default (ast.UnaryOp) still raises MSF002."""
    source = "def read(cfg: dict) -> int:\n    return cfg.get('n', -45)\n"
    assert "MSF002" in _codes("RUFAS/biophysical/animal/animal.py", source)


def test_get_or_default_not_first_in_chain_flagged() -> None:
    """A get call anywhere but last in an ``or`` chain raises MSF010 (edge case)."""
    source = "def read(cfg: dict, x: int) -> int:\n    return x or cfg.get('n') or 10\n"
    assert "MSF010" in _codes("RUFAS/input_manager.py", source)


def test_async_method_mutable_classvar_return_flagged() -> None:
    """An async method returning a class-level dict raw raises MSF030 (edge case)."""
    source = (
        "class RationManager:\n"
        "    RATIONS = {'a': 1}\n"
        "    async def all_rations(self) -> dict:\n"
        "        return self.RATIONS\n"
    )
    assert "MSF030" in _codes("RUFAS/biophysical/animal/ration/ration_manager.py", source)


def test_backslash_path_is_normalized() -> None:
    """A Windows-style backslash path still resolves directory-scoped checks."""
    source = "def calc(bw: float) -> float:\n    return bw * 0.62\n"
    assert "MSF001" in _codes("RUFAS\\biophysical\\animal\\growth.py", source)


def test_syntax_error_still_runs_text_checks() -> None:
    """Invalid Python skips AST checks but still runs comment checks (invalid input)."""
    source = "def broken(:\n    # noqa: C901\n"
    codes = _codes("RUFAS/util.py", source)
    assert "MSF040" in codes
    assert "MSF001" not in codes
