# RUFAS/biophysical/ — biophysical model

The physical farm model, driven day-by-day by `RUFAS/simulation_engine.py`.
Four domains, each a manager-led subsystem:

- `animal/` — herd, pens, digestion, growth, milk, reproduction, health,
  rations, bedding. Largest subsystem (~24k LOC). Own `CLAUDE.md`.
- `field/` — fields, soil (C/N/P cycling), crops, field operations. (~22k LOC).
  Own `CLAUDE.md`.
- `manure/` — manure handling, storage, separators, digesters, processors,
  nutrient tracking (`manure_manager.py`, `manure_nutrient_manager.py`). Own
  `CLAUDE.md`.
- `feed_storage/` — silage, hay, baleage, grain, purchased feed; `feed_manager.py`
  + `storage.py` base. `feed_storage_enum.py` enumerates storage types. Own
  `CLAUDE.md`.

## Pattern

Each domain exposes a **`*_manager.py`** that owns the subsystem's daily step
and holds its state. Material crosses domains through typed objects in
`RUFAS/data_structures/` (e.g. field→feed_storage, feed_storage→animal,
animal→manure, manure→crop_soil) — don't pass raw dicts between subsystems.

Constants live in dedicated `*_constants.py` modules per domain; don't inline
magic numbers — add or reuse a constant.
