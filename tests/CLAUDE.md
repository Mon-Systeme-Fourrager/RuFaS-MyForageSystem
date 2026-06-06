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
  imported explicitly into test files. `pytest-lazy-fixtures` is available — use
  `from pytest_lazy_fixtures import lf` to reference a fixture inside
  `@pytest.mark.parametrize` (the maintained successor of `pytest-lazy-fixture`,
  which broke on pytest ≥ 8).
- **Time**: freeze with `freezegun` when exercising `RUFAS/rufas_time.py` or
  date-dependent logic.
- Tests commonly build real `InputManager()` / `OutputManager()` and patch the
  unit under test.
- Full type annotations on test functions and fixtures (mypy strict applies to
  `tests/` too — see `pyproject.toml` mypy `exclude`).

## What to cover (RuFaS code-review rule)

- **Every modified/added function needs a unit test** + a NumPy-style docstring.
- The suite must cover **normal operation, edge cases, AND invalid inputs** — not
  just the happy path. See the
  [Code review](https://github.com/RuminantFarmSystems/RuFaS/wiki/Code-review) wiki.
- **Patch via `mocker` / `with patch(...)`, never `Class.method = MagicMock()`** —
  direct class-attribute assignment leaks across tests (no teardown) and breaks
  under pytest's collection order. `mocker.patch.object` auto-restores.

## End-to-end (E2E) tests

Beyond unit tests, RuFaS freezes expected model outputs per domain and compares
on each run (guards against unintended output changes). Run:

```
python main.py -p input/metadata/end_to_end_testing_tm_metadata.json
```

Setting up a new domain or updating expected results has a human-in-the-loop
guard — use the **`rufas-e2e-testing`** skill (it mirrors the wiki procedure).
A deliberate output change → mark the PR `[OutputChange]`.

## Running

```
pytest                                   # all unit/integration
pytest tests/test_EEE/test_energy.py     # one file
pytest tests/test_units.py::test_x       # one test
coverage run --rcfile=.github/.coveragerc && coverage report
```

Don't lower coverage or add new mypy errors — CI ratchets both against `dev`.
