# tests/ — pytest conventions

`pytest` (config in `pyproject.toml`: `testpaths = ["tests"]`). Coverage via
`.github/.coveragerc` (omits `__init__.py`).

## Layout — mirror `RUFAS/`

- Root modules → `tests/test_<module>.py`
  (e.g. `RUFAS/simulation_engine.py` → `tests/test_simulation_engine.py`).
- Packages → `tests/test_<package>/` mirroring the source tree:
  - `tests/test_biophysical/` → `test_animal/`, `test_crop_soil_field/`,
    `test_feed_storage/`, `test_manure/`
  - `tests/test_EEE/`, `tests/test_data_structures/`
- Note `RUFAS/rufas_time.py` → `tests/test_time.py` (name differs).

## Patterns

- **Mocking**: `pytest-mock` (`mocker.patch.object(...)`). Prefer patching
  estimator/manager methods over rewiring whole objects.
- **Fixtures**: per-package fixture modules (e.g. `tests/test_EEE/fixtures.py`),
  imported explicitly into test files. `pytest-lazy-fixture` is available.
- **Time**: freeze with `freezegun` when exercising `RUFAS/rufas_time.py` or
  date-dependent logic.
- Tests commonly build real `InputManager()` / `OutputManager()` and patch the
  unit under test.
- Full type annotations on test functions and fixtures (mypy strict applies to
  `tests/` too — see `pyproject.toml` mypy `exclude`).

## Running

```
pytest                                   # all
pytest tests/test_EEE/test_energy.py     # one file
pytest tests/test_units.py::test_x       # one test
coverage run --rcfile=.github/.coveragerc && coverage report
```

Don't lower coverage or add new mypy errors — CI ratchets both against `dev`.
