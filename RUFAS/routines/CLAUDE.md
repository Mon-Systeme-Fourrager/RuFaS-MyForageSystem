# CLAUDE.md — RUFAS/routines/

Guidance for calculation classes in `routines/`. See `RUFAS/CLAUDE.md` for module-level rules.

## Role

Routines are **stateless calculation classes**. They receive all inputs as parameters and return results. They do not hold simulation state across calls and do not import from `RUFAS/biophysical/`.

> **Known exception**: `RUFAS/routines/animal/ration/user_defined_ration.py` imports `AnimalCombination` from `RUFAS.biophysical.animal.data_types.animal_combination`. This type should be migrated to `RUFAS/data_structures/` in a future cleanup PR.

## Class Design Rules

- Organize related calculations into a class (e.g., `EmissionsEstimator`, `RationManager`).
- One-time config loaded in `__init__` is acceptable (e.g., reading constants from `InputManager()`). Simulation-state must not be stored.
- All public methods must be fully type-hinted — parameters and return types.
- Private helper methods use a leading underscore: `_calculate_purchased_feed_emissions()`.
- Descriptive method names, no mandatory prefix. Use what best describes the operation: `estimate_emissions()`, `run_daily_update()`, `receive_crop()`.

## Type Hints

Always import types from `data_structures/` — never use bare `dict` or `Any` at a public boundary:

```python
from RUFAS.data_structures.animal_to_manure_connection import ManureStream
from RUFAS.data_structures.rufas_time import RufasTime

def run_daily_update(
    self,
    manure_streams: dict[str, ManureStream],
    time: RufasTime,
) -> None:
    ...
```

## What Belongs Here vs biophysical/

A calculation belongs in `routines/` if:
- It can be fully tested by passing typed inputs and asserting on the return value.
- It does not need to read `self.*` state accumulated over multiple simulation days.

If either condition fails → it belongs in `biophysical/`.

## `__init__.py` Re-exports

`RUFAS/routines/__init__.py` uses wildcard re-exports (`from .animal import *`). Add new submodule packages to that file with `# noqa: F401, F403`. Do not wildcard-import inside routine modules themselves.
