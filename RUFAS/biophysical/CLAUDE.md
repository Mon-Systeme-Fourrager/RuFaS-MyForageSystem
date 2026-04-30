# CLAUDE.md — RUFAS/biophysical/

Guidance for stateful biophysical manager classes. See `RUFAS/CLAUDE.md` for module-level rules.

## Role

Biophysical managers own simulation state across the daily loop. They are instantiated once per simulation run and driven by `SimulationEngine`. They delegate calculations to `RUFAS/routines/`.

## Class Design Rules

- **No base class** — managers are standalone classes, not subclasses of a framework base.
- **Dependency injection in `__init__`**: receive config dicts or typed objects as constructor arguments. Pull shared config from `InputManager()` inside `__init__` when needed.
- **Private state**: use `self._name` (single underscore) for protected attributes, `self.__name` (double underscore) for truly private state. Expose via `@property` when read access is needed externally.
- **No cross-manager imports**: managers communicate exclusively through `data_structures/` objects, never by importing each other.

## Receiving and Returning Data

- **Receive**: typed objects from `data_structures/` or primitive types. Never accept raw `dict` at a public method boundary — wrap it in a typed structure first.
- **Return**: dataclasses or TypedDicts from `data_structures/`, or primitives (`float`, `int`, `bool`). Side effects (logging, output) go through `OutputManager()`.

## Calling Routines

Instantiate routine classes inside the manager method that needs them, or once in `__init__` if reused across calls:

```python
from RUFAS.routines.manure.emissions import EmissionsEstimator

class ManureManager:
    def __init__(self, ...) -> None:
        self._estimator = EmissionsEstimator(config)

    def run_daily_update(self, ...) -> None:
        self._estimator.estimate_emissions()
```

Never call routine classes from inside other routine classes — that belongs in `biophysical/`.

## State Storage Patterns

| Pattern | When to use |
|---|---|
| Instance vars (`self._x`) | Mutable simulation state (counters, current values) |
| Mutable `@dataclass` | Grouped related state passed to/from routines |
| `@dataclass(frozen=True)` | Immutable snapshots returned as output |
| `dict[EnumKey, Object]` | Collections keyed by a categorical type (e.g., `dict[StorageType, Storage]`) |

## Singleton Reset in Tests

When testing a manager that uses `InputManager`, reset the singleton in the fixture:

```python
@pytest.fixture
def fresh_input_manager() -> InputManager:
    InputManager._InputManager__instance = None  # name-mangled reset
    return InputManager()
```
