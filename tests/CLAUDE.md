# CLAUDE.md — tests/

Guidance for writing and organizing tests. See root `CLAUDE.md` for test commands.

## File Naming

| Pattern | Status |
|---|---|
| `test_*.py` | **Active** — discovered and run by pytest |
| `_test_*.py` | **Disabled** — legacy files, not run (leading underscore hides from pytest) |

New tests must use the `test_*.py` prefix. Do not add to `_test_*.py` files.

## Directory Structure

Mirror the source tree under `tests/`:
- `tests/test_input_manager.py` → tests for `RUFAS/input_manager.py`
- `tests/animal_module_tests/` → tests for `RUFAS/biophysical/animal/` and `RUFAS/routines/animal/`

## Style

Pure pytest — no `unittest.TestCase` subclasses. Use:
- `@pytest.fixture` for setup
- `pytest.raises()` for expected exceptions
- `mocker: MockerFixture` from `pytest-mock` for patching
- Direct `assert` statements (not `self.assert*`)

## Singleton Reset Pattern

Tests that use `InputManager` or `OutputManager` must reset the singleton before each test. There is no shared `conftest.py` — define the fixture locally in the test file:

```python
@pytest.fixture
def fresh_input_manager() -> InputManager:
    InputManager._InputManager__instance = None  # reset name-mangled __instance
    return InputManager()
```

Never rely on singleton state left over from a previous test — always reset explicitly.

## Mocking Pattern

```python
from unittest.mock import MagicMock, Mock, patch

def test_something(mocker: MockerFixture) -> None:
    mocker.patch("RUFAS.input_manager.InputManager.get_data", return_value={...})
    ...
```

Use `mocker.patch()` (pytest-mock) for simple patches. Use `patch()` as a context manager when patching across module boundaries.

## Coverage Target

Coverage target is ~96%. Run with:
```bash
coverage run --rcfile=.github/.coveragerc
coverage report --rcfile=.github/.coveragerc
```

New code in `RUFAS/` must include tests. PRs that drop coverage below the target will be flagged in review.
