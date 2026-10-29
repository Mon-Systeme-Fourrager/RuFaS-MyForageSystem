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

`RUFAS/biophysical/field/field/field.py:1522-1523` passes the day's incoming
light as the first argument:

```python
full_evapotranspirative_demand = self._determine_potential_evapotranspiration(
    current_conditions.incoming_light,
```

That parameter is named and used as extraterrestrial radiation
(`field.py:1734`, documented at `:1744` as "Radiation from sunlight (MJ per
square meter per day)"; reference `SWAT Reference: 2:2.2.24` at `:1759`):

```python
avg_air_temp = avg_air_temp if avg_air_temp else (max_air_temp + min_air_temp) / 2
latent_heat_vaporization = Field._determine_latent_heat_vaporization(avg_air_temp)
potential_evapotranspiration: float = (
    0.0023 * extraterrestrial_radiation * ((max_air_temp - min_air_temp) ** 0.5) * (avg_air_temp + 17.8)
) / latent_heat_vaporization
return max(0.0, potential_evapotranspiration)
```

(`field.py:1770-1775`; latent heat `2.501 - 0.002361 * avg_air_temp` MJ/kg at
`:1796`.) `incoming_light` is the weather file's `Hday` column
(`RUFAS/weather.py:74`), the daily **surface** shortwave radiation. No code in
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

Present upstream: `RuminantFarmSystems/RuFaS` `dev` makes the same call at
`field.py:1582-1583` (`current_conditions.incoming_light,`) and has the same
formula at `:1833`.

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
MJ/m²). A reimplementation of `field.py:1770-1775` reproduces RuFaS's daily
output exactly.

### Effect on results (sensitivity test, not upstream code)

A throwaway copy of RuFaS with `field.py:1523` passing FAO-56 Ra (Eq. 21, 23,
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
