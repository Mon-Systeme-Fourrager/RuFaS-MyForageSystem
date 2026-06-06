# RUFAS/ — package conventions

Core simulation package. See the repo-root `CLAUDE.md` for tooling, commands,
and CI gotchas (changelog, protected inputs, mypy ratchet).

## Top-level modules (orchestration)

- `task_manager.py` — `TaskManager.start(...)`; runs one or more tasks from the
  metadata JSON. Main entry from `main.py`.
- `input_manager.py` — parses the nested input JSON tree into model objects.
  Has a configurable metadata depth limit. **Large (~80 KB)** — read targeted.
- `simulation_engine.py` — day-by-day simulation loop wiring the subsystems.
- `output_manager.py` — log/data pools + `LogVerbosity`; `add_error`,
  dump helpers. **Large (~127 KB)** — read targeted.
- `data_validator.py` — input validation. **Large (~99 KB)** — read targeted.
- `report_generator.py` / `graph_generator.py` — reports & graphics from output.
- `e2e_test_results_handler.py` — end-to-end test result comparison helpers.
- `data_collection_app_updater.py` — syncs schema for `DataCollectionApp/`.

## Support modules

`rufas_time.py` (sim calendar/time), `units.py` (unit handling), `weather.py`,
`current_day_conditions.py`, `general_constants.py`, `user_constants.py`,
`util.py` (broad helpers, ~45 KB).

## Subpackages

- `biophysical/` — the physical model (animal, field, manure, feed_storage).
- `EEE/` — Economics, Energy, Emissions.
- `data_structures/` — typed objects connecting subsystems.

Each has its own `CLAUDE.md`.

## Conventions

- Full type annotations (mypy strict). New public methods get docstrings
  matching the existing Sphinx-documented style.
- Constructors are commonly parameterless then configured (e.g.
  `InputManager()`, `OutputManager()`); follow the surrounding pattern.
- Keep functions under flake8 complexity 10 — these modules are already large,
  so prefer extracting helpers over growing a method.

## Reference docs (RuFaS wiki)

Deep per-module write-ups live on the wiki (too large to inline — read on demand):

- [Output-Manager](https://github.com/RuminantFarmSystems/RuFaS/wiki/Output-Manager)
  (log/data pools, filters, verbosity) ·
  [Chunkification](https://github.com/RuminantFarmSystems/RuFaS/wiki/Chunkification)
  (periodic pool dumps to cap memory — `chunkification` task flag,
  `save_chunk_threshold_call_count` / `maximum_memory_usage`)
- [Input-Manager](https://github.com/RuminantFarmSystems/RuFaS/wiki/Input-Manager) ·
  [Task-Manager](https://github.com/RuminantFarmSystems/RuFaS/wiki/Task-Manager) ·
  [Report-Generator](https://github.com/RuminantFarmSystems/RuFaS/wiki/Report-Generator) ·
  [Graph-Generator](https://github.com/RuminantFarmSystems/RuFaS/wiki/Graph-Generator)
- [Data-Origins](https://github.com/RuminantFarmSystems/RuFaS/wiki/Data-Origins) ·
  [Command-Line Arguments](https://github.com/RuminantFarmSystems/RuFaS/wiki/RuFaS-Command-Line-Arguments)
