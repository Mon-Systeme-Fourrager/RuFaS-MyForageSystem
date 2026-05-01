# CLAUDE.md — RUFAS/biophysical/

Guidance for stateful biophysical manager classes. See `RUFAS/CLAUDE.md` for module-level rules.

## Role

Biophysical managers own simulation state across the daily loop. They are instantiated once per simulation run and driven by `SimulationEngine`. They delegate calculations to `RUFAS/routines/`.

## Class Design Rules

- **No base class** — managers are standalone classes, not subclasses of a framework base.
- **Dependency injection in `__init__`**: constructors may accept config dicts or typed objects. For new or modified managers, any raw `dict` received in `__init__` must be immediately converted into a typed config object (from `data_structures/` or `InputManager()`) and stored as protected state (`self._config`). Legacy managers (e.g., `FeedManager`) should be migrated incrementally and may document temporary exceptions inline. All public methods must receive/return typed objects or primitives only — never raw `dict`.
- **Private state**: use `self._name` (single underscore) for protected attributes, `self.__name` (double underscore) for truly private state. Expose via `@property` when read access is needed externally.
- **Cross-manager imports**: avoid importing managers from other domains. Managers within the same domain subdirectory (e.g., `biophysical/manure/`) may compose each other directly (e.g., `ManureManager` instantiates `ManureNutrientManager`). Cross-domain interactions must go through `data_structures/` objects.

## Receiving and Returning Data

- **Receive**: public methods accept typed objects from `data_structures/` or primitives only. The constructor (`__init__`) is the sole exception where config dicts are allowed (converted immediately — see above).
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
    InputManager._InputManager__instance = None  # reset name-mangled singleton storage
    if hasattr(InputManager, "instance"):
        delattr(InputManager, "instance")  # reset __new__ singleton storage
    return InputManager()
```
