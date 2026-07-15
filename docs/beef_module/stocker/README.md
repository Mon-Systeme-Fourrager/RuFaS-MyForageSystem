# Beef Stocker/Backgrounding Module — Scope Boundaries

## Named Scope Boundaries

The following features are explicitly not implemented in the native RuFaS stocker module.
They belong to the BeefGEM management layer and will be addressed in separate, later work.

1. **No compensatory gain** — daily body-weight gain uses the linear `AnimalConfig.stocker_target_adg`
   throughout the stocker phase. Dynamic compensatory gain modeling (accelerated gain following a
   nutritional restriction period) belongs to BeefGEM Phase D.

2. **No limit-feeding diet system** — `stocker_diet_system` accepts only `'pasture'` and
   `'drylot_forage'`. Precise bunk management with voluntary-intake restriction belongs to
   BeefGEM Phase B.

3. **No heat stress (THI-based) adjustment** — stocker DMI and performance are not adjusted for
   temperature-humidity index. Heat stress integration belongs to BeefGEM Phase D.

4. **No pasture growth model** — forage quality is a static user config input regardless of
   `stocker_diet_system`. Dynamic forage availability from a pasture growth or field subsystem
   is not modeled; the field subsystem integration is a future-PR candidate.

5. **No sexed-pen management** — `BEEF_STOCKER_STEER` and `BEEF_STOCKER_HEIFER` are maintained as
   two separate cohort lists but share a single `BEEF_STOCKER` animal combination and pen pool.
   Separate pen allocation by sex, or different target ADG and exit weights per sex, is not
   implemented.

## Diet System Valid Values

`stocker_diet_system` (validated by `DataValidator.validate_beef_stocker_config`):

| Value | Description |
|---|---|
| `'pasture'` | Grazed pasture; forage quality set by static config |
| `'drylot_forage'` | Dry-lot forage feeding; no grazing activity modeled |

## Reference Sources

- NRC 2016 *Nutrient Requirements of Beef Cattle* (9th rev.) — Chapters 10–12, 19–20
- `NRC2016_Beef_Requirements_Calculator_Inventory_Final.xlsx` — verified equation inventory
- `NRC2016_BeefCattle_FeedLibrary_Complete.xlsx` — feed compositions (Table 18-1), Feed IDs 301–305
