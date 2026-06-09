# RUFAS/biophysical/animal/ — animal subsystem

Models the dairy herd. Entry/orchestration:

- `herd_manager.py` — owns the herd's daily step and state.
- `herd_factory.py` — builds the herd from parsed inputs.
- `pen.py` — pen-level grouping; `animal.py` — individual animal model.
- `animal_config.py`, `animal_grouping_scenarios.py` — configuration.
- `animal_module_reporter.py` — subsystem reporting hooks.
- Constants: `animal_constants.py`, `animal_module_constants.py`.

## Biological sub-packages

- `digestive_system/` — intake & digestion.
- `nutrients/` — nutrient pools/requirements.
- `ration/` — feed ration formulation/allocation.
- `growth/` — body growth.
- `milk/` — milk production.
- `reproduction/` — breeding/gestation cycle.
- `animal_health/` — health states.
- `animal_genetics/` — genetic parameters.
- `bedding/` — bedding use (feeds into manure).
- `data_types/` — animal-specific typed structures.

## Notes

- Inputs come from `input/data/animal/*.json` plus
  `input/data/animal_genetics/` and `input/data/animal_health/` (validated in
  `RUFAS/data_validator.py`). Several are CI-protected — see
  `.claude/rules/protected-inputs.md`.
- Feed arrives via the feed_storage→animal connection; manure/bedding leave via
  the animal→manure connection (`RUFAS/data_structures/`).
- Tests mirror this tree under `tests/test_biophysical/test_animal/`.
