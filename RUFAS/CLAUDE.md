# CLAUDE.md — RUFAS/

Module-specific guidance for the `RUFAS/` package. The root `CLAUDE.md` covers project-wide conventions (commands, CI, Graphify, slash commands).

## Module Structure

```
RUFAS/
├── biophysical/      # Stateful manager classes (own state, drive the simulation)
├── routines/         # Pure calculation classes (stateless, called by biophysical/)
├── data_structures/  # Typed contracts between modules (dataclasses, Enums, TypedDicts)
├── simulation_engine.py  # Imports biophysical managers, drives the daily loop
├── input_manager.py  # Singleton — reads JSON/CSV inputs
└── output_manager.py # Singleton — logging pools, CSV/JSON output
```

**Direction of dependency**: `simulation_engine` → `biophysical/` → `routines/` + `data_structures/`. Never import biophysical managers inside routines/.

## Singleton Pattern

`InputManager` and `OutputManager` are `__new__`-based singletons. Use them anywhere by calling the constructor — you always get the shared instance:

```python
im = InputManager()
data = im.get_data("manure_management")
```

Implementation rules (do not deviate):
- Must return a single shared instance and ensure `__init__` logic runs only once
- Private state via name-mangling (`self.__pool`), exposed via `@property`
- Never pass the instance around — just call `InputManager()` at the call site

## biophysical/ vs routines/

| Layer | Rules |
|---|---|
| `biophysical/` | Holds state; instantiated once per simulation run; calls into `routines/` |
| `routines/` | No instance state that persists across calls; receives all inputs as parameters |

When adding logic: if it requires reading `self.*` simulation state → `biophysical/`. If it is a calculation that could be tested with pure inputs → `routines/`.

## `__init__.py` Convention

- `RUFAS/__init__.py` — keep empty.
- `RUFAS/routines/__init__.py` — wildcard re-exports with `# noqa: F401, F403` are accepted here only.
- All other `__init__.py` files — keep empty unless there is an explicit re-export need.
