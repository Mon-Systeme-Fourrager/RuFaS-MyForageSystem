# Known issues

Defects confirmed in this fork and not fixed yet. Each entry says what is
wrong, what it affects, where it came from, and what has been done about it so
far.

---

## 1. Hargreaves potential ET uses surface instead of extraterrestrial radiation

**Status: open in this fork and upstream. Documented only; no upstream report and no fix.**

### In plain terms

The field module estimates how much water the atmosphere can draw from a field
each day (potential evapotranspiration, ET) with the Hargreaves equation. That
equation needs the radiation arriving at the top of the atmosphere
(extraterrestrial radiation). RuFaS gives it the radiation measured at the
ground instead, which is roughly half as large. Potential ET therefore comes
out at about half its intended value, and everything computed from it follows:
crop transpiration demand, water stress, the soil water balance, and through
them yields and the response to nitrogen.

### What is wrong

`RUFAS/biophysical/field/field/field.py:1611-1612` passes the day's incoming
light as the first argument:

```python
full_evapotranspirative_demand = self._determine_potential_evapotranspiration(
    current_conditions.incoming_light,
```

That parameter is named and used as extraterrestrial radiation
(`field.py:1823`, documented at `:1833` as "Radiation from sunlight (MJ per
square meter per day)"; reference `SWAT Reference: 2:2.2.24` at `:1848`):

```python
avg_air_temp = avg_air_temp if avg_air_temp else (max_air_temp + min_air_temp) / 2
latent_heat_vaporization = Field._determine_latent_heat_vaporization(avg_air_temp)
potential_evapotranspiration: float = (
    0.0023 * extraterrestrial_radiation * ((max_air_temp - min_air_temp) ** 0.5) * (avg_air_temp + 17.8)
) / latent_heat_vaporization
return max(0.0, potential_evapotranspiration)
```

(`field.py:1859-1864`; latent heat `2.501 - 0.002361 * avg_air_temp` MJ/kg at
`:1885`.) `incoming_light` is the weather file's `Hday` column
(`RUFAS/weather.py:68`), the daily **surface** shortwave radiation. No code in
`RUFAS/` computes extraterrestrial radiation, and latitude does not enter
potential ET. The coefficient (0.0023), the constant (17.8), the exponent
(0.5) and the temperatures match the published equation; only the radiation
term differs.

### What the references say

- **SWAT 2:2.2.24** (SWAT+ theoretical documentation), the reference the
  docstring cites: H0 is "extraterrestrial radiation (MJ m-2 d-1)".
- **FAO-56 Eq. 52** (Hargreaves & Samani 1985):
  `ET0 = 0.0023 (Tmean + 17.8) (Tmax − Tmin)^0.5 Ra`, with Ra in mm/day
  (0.408 × Ra in MJ m-2 d-1) and Ra the extraterrestrial radiation of FAO-56
  Eq. 21, from latitude and day of year.

Two Hargreaves forms exist. Hargreaves (1975):
`ET0 = 0.0135 · Rs · (T + 17.8)`, with surface solar radiation Rs and no
temperature range. Hargreaves & Samani (1985):
`ET0 = 0.0023 · Ra · (T + 17.8) · (Tmax − Tmin)^0.5`, with extraterrestrial Ra;
`0.0023 ≈ 0.0135 × KT` (KT = 0.17), where `KT · (Tmax − Tmin)^0.5` estimates
Rs/Ra. RuFaS uses the 1985 coefficient and temperature-range term with Rs, so
the cloud effect enters twice. Source: Shahidian et al., "Hargreaves and Other
Reduced-Set Methods for Calculating Evapotranspiration", in *Evapotranspiration
– Remote Sensing and Modeling* (InTech), Eq. 5 and 7.

### Upstream and origin

Present upstream: `RuminantFarmSystems/RuFaS` `dev` (`9af6eca23`) makes the same call at
`field.py:1597-1598` (`current_conditions.incoming_light,`) and has the same
formula at `:1848`.

Unchanged since the call was added at this path, in commit `162aa7b89`
(2023-08-03, as `current_weather.incoming_light`). Later commits renamed the
object to `current_conditions` (`aaa8d09ec`, 2023-10-27) and reformatted the
lines (`b83ed1f14`, 2024-02-12; `f55db5268`, 2024-02-13); none changed which
radiation is passed.

### Numbers: Sainte-Anne-de-Bellevue (45.41 N), 2013, days 130-263

Daily weather from the Open-Meteo archive, the same file for every row.

| Potential / reference ET | mm |
|---|---|
| RuFaS `max_evapotranspiration` (Hargreaves with `Hday`) | 234.7 |
| FAO-56 Eq. 52 Hargreaves with Ra (Eq. 21), computed independently | 463.7 |
| Open-Meteo `et0_fao_evapotranspiration` (FAO-56 Penman-Monteith) | 465.4 |

Summed over those days, `Hday` is 0.485 of Ra (2,448.6 against 5,045.9
MJ/m²). A reimplementation of `field.py:1859-1864` reproduces RuFaS's daily
output exactly.

### Effect on results (sensitivity test, not upstream code)

A throwaway copy of RuFaS with `field.py:1523` (at `bb3d412c0`; now `:1612`) passing FAO-56 Ra (Eq. 21, 23,
24, 25; latitude from the field, day of year from the simulation) instead of
`incoming_light`. Everything else is identical between the two runs:
`FIELD_ONLY`, corn silage 2013 at the site above, sown day 130, harvested day
263, soil water from Saxton & Rawls (2006), and the example farm's management.

| N dose (kg/ha) | Dry yield, as shipped (kg/ha) | Dry yield, with Ra (kg/ha) | Change |
|---|---|---|---|
| 0 | 9,283.60 | 9,631.09 | +3.7 % |
| 25 | 11,120.16 | 11,369.56 | +2.2 % |
| 50 | 12,916.30 | 12,897.96 | -0.1 % |
| 100 | 16,288.18 | 14,629.74 | -10.2 % |
| 0 -> 100 response | +7,004.58 | +4,998.65 | |

Potential ET (days 130-263) 234.7 -> 461.5 mm; corn maximum transpiration
142-144 -> 294-297 mm; water uptake 133-134 -> 185-187 mm; water stress
4.7-4.9 -> 34.6-34.8 stress-days (22 -> 85-86 days with stress).

Why yields rise at low N and fall at high N is **inferred, not tested**:
nitrate leaching falls (13.8-14.8 -> 7.8-8.3 kg N/ha) and N uptake rises by
about 3.5 kg N/ha, which may help at low doses, while the added water stress
may cap yield at 100 kg N/ha.

### Status and next step

Documented only; no upstream report and no fix until decided with the PO.
Until then, every RuFaS output for the site above (yields, dose response,
water balance) carries potential ET at about half the FAO-56 value.

---

## 2. Water density evaluates to 0.000997 instead of 997 kg/m³

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

`RUFAS/user_constants.py:37-38`:

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
it: `user_constants.py:56` maps `"WATER_DENSITY_KG_PER_M3"` to
`MeasurementUnits.KILOGRAMS_PER_CUBIC_METER`.

### Where it is read

Three production call sites, all in the manure module. Every argument is in
m³, so all three are wrong by a factor of 10⁶.

| file:line | what it computes |
|---|---|
| `RUFAS/biophysical/manure/handler/handler.py:342` | `determine_manure_water` — the water mass (kg) added to a manure stream by parlour cleaning and milking water. Its caller (`:165`) passes the m³ value returned by `determine_total_cleaning_water_volume` (`:303`) |
| `RUFAS/biophysical/manure/storage/slurry_storage_outdoor.py:76` | the water mass (kg) added to an uncovered or crusted outdoor slurry store by precipitation — `precipitation (mm) × MM_TO_M × surface_area (m²)` |
| `RUFAS/biophysical/manure/storage/anaerobic_lagoon.py:77` | the same, for an anaerobic lagoon |

The two precipitation sites are unambiguous: the same `precipitation_volume`
is added to `_received_manure.volume` as m³ on the line above and to
`_received_manure.water` as kg on the line below, so two attributes of one
`ManureStream` currently disagree by 10⁶. A 1 000 m² uncovered store receiving
10 mm of rain gains 10 m³ of volume and 0.00997 kg of water, an implied
density of about 0.001 kg/m³; it should gain 9 970 kg.

### Which simulations are affected

- **Affected: `FULL_FARM` and `MANURE_ONLY`.**
  `SimulationType._manure_simulation_types` (`RUFAS/simulation_engine.py:88-92`)
  returns these two types. `simulate_manure` gates every manure code path.
- **Not affected: `FIELD_ONLY`, `FIELD_AND_FEED`, `ANIMALS_ONLY`, `FEED_ONLY`** —
  the four other types this fork defines (`simulation_engine.py:52-57`).
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

- `handler.py:334` — the docstring of `determine_manure_water` declares
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
`test_handler.py:325` and the `handler.py:334` docstring have to change with
it. An upstream issue is drafted and **not posted**; this entry records the
defect in the fork in the meantime.
