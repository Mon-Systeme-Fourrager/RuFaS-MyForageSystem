# Known issues

Defects confirmed in this fork and not fixed yet. Each entry says what is
wrong, what it affects, where it came from, and what has been done about it so
far.

---

## 1. Water density evaluates to 0.000997 instead of 997 kg/m³

**Status: open in this fork. Upstream report drafted, not posted.**

### In plain terms

The constant that stands for the density of water is a million times too
small. Wherever the code turns a volume of water in m³ into a mass in kg, it
gets a mass a million times too light. Only the manure module reads this
constant, so only manure runs are affected: the water, and therefore the total
mass, of a manure stream comes out far too small. The nitrogen, phosphorus and
potassium applied to a field are **not** affected — that calculation cancels
the error out. Field-only and silage runs never touch the constant.

### What is wrong

`RUFAS/user_constants.py:36-37`:

```python
WATER_DENSITY_KG_PER_LITER = 0.997
WATER_DENSITY_KG_PER_M3 = WATER_DENSITY_KG_PER_LITER * GeneralConstants.LITERS_TO_CUBIC_METERS
```

`GeneralConstants.LITERS_TO_CUBIC_METERS` is `0.001`
(`RUFAS/general_constants.py:117`), so the product is **0.000997**, not 997.
Converting kg/L to kg/m³ divides by m³/L; multiplying gives kg·m³/L², which is
not a density at all:

```
0.997 kg/L / 0.001 m³/L = 997 kg/m³          (correct)
0.997 kg/L * 0.001 m³/L = 0.000997           (current)
```

The file records the intended unit right next to the value that contradicts
it: `user_constants.py:55` maps `"WATER_DENSITY_KG_PER_M3"` to
`MeasurementUnits.KILOGRAMS_PER_CUBIC_METER`.

### Where it is read

Three production call sites, all in the manure module. Every argument is in
m³, so all three are wrong by a factor of 10⁶.

| file:line | what it computes |
|---|---|
| `RUFAS/biophysical/manure/handler/handler.py:337` | `determine_manure_water` — the water mass (kg) added to a manure stream by parlour cleaning and milking water. Its caller (`:165`) passes the m³ value returned by `determine_total_cleaning_water_volume` (`:299`) |
| `RUFAS/biophysical/manure/storage/slurry_storage_outdoor.py:60` | the water mass (kg) added to an uncovered or crusted outdoor slurry store by precipitation — `precipitation (mm) × MM_TO_M × surface_area (m²)` |
| `RUFAS/biophysical/manure/storage/anaerobic_lagoon.py:76` | the same, for an anaerobic lagoon |

The two precipitation sites are unambiguous: the same `precipitation_volume`
is added to `_received_manure.volume` as m³ on the line above and to
`_received_manure.water` as kg on the line below, so two attributes of one
`ManureStream` currently disagree by 10⁶. A 1 000 m² uncovered store receiving
10 mm of rain gains 10 m³ of volume and 0.00997 kg of water, an implied
density of about 0.001 kg/m³; it should gain 9 970 kg.

### Which simulations are affected

- **Affected: `FULL_FARM`.** `SimulationType._manure_simulation_types`
  (`RUFAS/simulation_engine.py:84-88`) returns that type alone in this fork;
  upstream the same set also contains `MANURE_ONLY`. `simulate_manure` gates
  every manure code path.
- **Not affected: `FIELD_ONLY`, `FIELD_AND_FEED`, `ANIMALS_ONLY`** — the
  three other types this fork defines (`simulation_engine.py:51-54`).
  They never instantiate `ManureManager`, and when a field
  requests manure nutrients the engine routes to
  `FieldManureSupplier.request_nutrients`, which does not read this constant.
- **Not affected: feed storage / silage.** Grepping the tree for
  `WATER_DENSITY_KG_PER_M3` returns the three manure call sites above and
  nothing else, so no feed, crop, soil, animal or economics code reads it.

### What the wrong value does and does not change

- **Wrong:** the `water` attribute, and therefore the total mass, of every
  manure stream that passes through a parlour handler or an uncovered outdoor
  store. Downstream, anything derived from manure mass or from its dry-matter
  fraction — storage filling, emptying schedules, and the water credited to
  the soil when liquid manure is applied (`field.py:_add_manure_water`, which
  uses `total_manure_mass × (1 − dry_matter_fraction)`).
- **Not wrong, because the error cancels:** the nutrient mass applied to a
  field. The projected mass is derived as *requested nutrient / nutrient
  composition fraction*, and both scale with `total_manure_mass`, so a manure
  mass too small by 10⁶ still delivers the requested N, P and K.

This has **not** been measured on a full-farm run. The two lists above say
which quantities are wrong and why, not by how much any reported output moves.

### Two places that agree with the wrong value

- `handler.py:330` — the docstring of `determine_manure_water` declares
  `total_cleaning_water_volume` as `(L)`, but the only caller (`:165`) passes
  m³, and `determine_total_cleaning_water_volume`'s own docstring says m³. The
  parameter is m³; the docstring is wrong, and it is what makes the
  multiplication look right.
- `tests/test_biophysical/test_manure/test_handler/test_handler.py:325`
  asserts `handler.determine_manure_water(100000, 20000) == 100019.94`.
  `100019.94 = 100000 + 20000 × 0.000997`, so the expected value was computed
  from the wrong constant rather than from the physics. It is the only place
  in the suite that hardcodes the number; the five other tests that touch the
  constant (`test_handler.py:71`, `:134`,
  `test_single_stream_handler.py:118`, `test_anaerobic_lagoon.py:146`,
  `test_slurry_storage_outdoor.py:124`) reference
  `UserConstants.WATER_DENSITY_KG_PER_M3` symbolically.

### Origin

Introduced with the constant itself, in upstream commit `e784d9ad0`
(2022-09-16, "Added classes for manure data, constants, extended enum"). The
expression has not been edited since; the 2026-06-03 commit that touched the
file only reformatted it.

### Status and next step

Not fixed here, and no code or test has been changed. The fix is one line —
divide instead of multiply, and `0.997 / 0.001` is exactly `997.0` in
IEEE-754 double, so it needs no literal — but it cannot land alone:
`test_handler.py:325` and the `handler.py:330` docstring have to change with
it. An upstream issue is drafted and **not posted**; this entry records the
defect in the fork in the meantime.
