# RUFAS hydrological architecture — components, SWAT lineage, and extension points

**Repository:** `C:\Proyectos\RuFaS-MyForageSystem`
**Branch / commit:** `research/andrea-msf-prototype` @ `ef1f22e`
**Method:** AST parsing, Python tokenizer analysis, and targeted reads. No RUFAS module imported,
no RUFAS code executed.
**Companions:** `docs/rufas_architecture_map.md`, `docs/rufas_phosphorus_deep_dive.md`,
`docs/rufas_plant_growth_analysis.md`

> **Headline finding, stated up front:** RUFAS does not integrate with SWAT+. It contains **zero**
> SWAT references in executable code — no import, no call, no file exchange, no process
> invocation, no dependency. All 231 SWAT occurrences in `RUFAS/` are prose citations in
> docstrings and comments. RUFAS is a Python **reimplementation** of SWAT/SWAT+ equations, not a
> client of SWAT+. §2 gives the proof.

---

## 1. Hydrological components

### 1.1 Where they live

| Process | File | LOC | Algorithm | Primary citation |
| --- | --- | ---: | --- | --- |
| **Runoff + infiltration** | `field/soil/infiltration.py` | 361 | **SCS Curve Number** | SWAT 2:1.1, eqns 2:1.1.1–11 |
| **Percolation** | `field/soil/percolation.py` | 288 | storage-routing travel time | SWAT 2:3.2, eqns 2:3.2.3–4 |
| **Soil evaporation** | `field/soil/evaporation.py` | 245 | depth-distributed evaporative demand | SWAT 2:2.3.3.2, eqns 2:2.3.16–20 |
| **Erosion / sediment** | `field/soil/soil_erosion.py` | 749 | **MUSLE** + peak runoff rate | SWAT 4:1.1; peak runoff 2:1.3 |
| **Snow** | `field/soil/snow.py` | 227 | degree-day melt, pack temperature | SWAT 1:2.5 (2009); sublimation 2:2.3.3.1 |
| **Soil temperature** | `field/soil/soil_temp.py` | 366 | damping-depth | SWAT 1:1.3, eqns 1:1.3.3–12 |
| **Plant water uptake** | `field/crop/water_uptake.py` | 453 | layer-wise uptake vs. potential | pseudocode C.5.x |
| **Canopy water** | `field/crop/water_dynamics.py` | 195 | interception / canopy storage | — |
| **PET + orchestration** | `field/field/field.py` | 1,928 | **Hargreaves** PET; `_cycle_water` | Hargreaves noted at `field.py:1749` |
| **Weather inputs** | `RUFAS/weather.py`, `RUFAS/current_day_conditions.py` | — | daily driver variables | SWAT 1:1.1.x; `readwgn.f` port note |

### 1.2 Which methods are implemented — and which are not

Verified by name search across `RUFAS/**/*.py`:

| Method | Present? | Where |
| --- | --- | --- |
| SCS Curve Number | **yes** | `soil/infiltration.py` |
| MUSLE / USLE | **yes** | `soil/soil_erosion.py` |
| Hargreaves PET | **yes** | `field/field/field.py:1749` |
| Storage-routing percolation | **yes** | `soil/percolation.py` |
| Degree-day snowmelt | **yes** | `soil/snow.py` |
| Damping-depth soil temperature | **yes** | `soil/soil_temp.py` |
| **Green-Ampt** | **absent** | no occurrence anywhere |
| **Priestley-Taylor** | **absent** | — |
| **Penman / Penman-Monteith** | **absent** | the only "penman" match is `PenManureData`, a false positive |
| **Muskingum** routing | **absent** | — |
| **Mualem–van Genuchten** | **absent** in RUFAS | (it exists in the *Terranimo* API, not here) |
| **Ritchie** evaporation | **absent** | — |

**There is exactly one runoff method and one PET method.** SWAT offers Green-Ampt as an
alternative to SCS-CN and three PET options; RUFAS implements one of each, with no switch.

### 1.3 Non-SWAT lineage cited

- **SurPhos** (Vadas) — phosphorus, cited in `field/fertilizer_application.py:69,160` and
  `field/manure_application.py:10,16,86,172`. `docs/scientific/crop_and_soil.tex:721` states:
  _"Carbon and nitrogen nutrient cycling and hydrology are based on the SWAT+ model and phosphorus
  nutrient cycling on the SurPhos model."_
- **Williams 1975** (MUSLE) and **Neitsch 2011** (SWAT soil-water) — cited in
  `openspec/changes/integrate-slope-aspect-api/proposal.md:191-192` as the bases of RUFAS sediment
  and SCS-CN runoff respectively.
- `RUFAS/weather.py` cites the **SWAT Fortran source file `readwgn.f`** — a porting reference, not
  a runtime link.

---

## 2. SWAT references, categorised

Method: every `.py` file under `RUFAS/` was tokenized; comments and string literals were removed;
the residue was searched for `swat` case-insensitively.

### 2.1 Live code that calls or references SWAT

**ZERO.** No import, no identifier, no call, no attribute, no string used as a path or format key.

Additional negative checks, all clean:

| Check | Result |
| --- | --- |
| SWAT file-format artefacts (`.hru`, `.bsn`, `.sol`, `.cio`, `.sub`, `.rte`, `.swt`, `TxtInOut`) | none found in repo |
| `subprocess` / `Popen` / `os.system` / `.exe` invocation | none (all `execute*` hits are RUFAS's own methods) |
| SWAT in declared dependencies (`pyproject.toml`) | none — deps are matplotlib, numpy, pandas, scipy, typing_extensions, salib, tqdm, deepdiff, psutil, numba |

### 2.2 Comments and docstrings citing SWAT as source

**35 files, 231 occurrences** — 220 in docstrings, 11 in `#` comments.

| Occurrences | File |
| ---: | --- |
| 21 | `field/soil/soil_erosion.py` |
| 15 | `field/soil/nitrogen_cycling/nitrification_volatilization.py` |
| 14 | `field/soil/layer_data.py` |
| 13 | `field/crop/crop_data.py` |
| 12 | `field/soil/infiltration.py` |
| 12 | `field/soil/soil_temp.py` |
| 10 | `field/crop/non_water_uptake.py` |
| 10 | `field/soil/soil_data.py` |

Citations follow the SWAT Theoretical Documentation `chapter:section.equation` scheme. Distribution
by chapter across 152 parsed citations:

| Chapter | Citations | Topic |
| ---: | ---: | --- |
| 5 | 50 | plant growth |
| 2 | 39 | **hydrology / soil water** |
| 3 | 30 | nutrients |
| 1 | 15 | climate / soil temperature |
| 4 | 14 | erosion |
| 6 | 4 | pesticides / other |

### 2.3 "SWAT+" specifically

Only **two** occurrences in the whole repository, both prose:

- `field/soil/nitrogen_cycling/leaching_runoff_erosion.py:347` — _"This method is described for
  nitrate in the SWAT+ documentation Equation 4:2.1.2."_
- `docs/scientific/crop_and_soil.tex:721` — the lineage sentence quoted in §1.3.

Everything else says "SWAT", not "SWAT+".

### 2.4 Documentation files

| File | Nature |
| --- | --- |
| `docs/scientific/crop_and_soil.tex` | scientific write-up; states the SWAT+ / SurPhos lineage |
| `docs/scientific/resources/crop_and_soil.bib`, `docs/scientific/rufas.bib` | bibliography entries |
| `docs/_src/_wiki/onboarding.rst` | onboarding prose |
| `openspec/changes/integrate-slope-aspect-api/proposal.md` | cites Neitsch 2011 as basis of RUFAS SCS-CN |
| `graphify-out/GRAPH_REPORT.md` | generated graph report |
| `docs/rufas_architecture_map.md`, `rufas_phosphorus_deep_dive.md`, `rufas_plant_growth_analysis.md` | this analysis series |

### 2.5 Test files

**ZERO.** No file under `tests/` mentions SWAT in any form. The equations are verified against
expected numbers, not against SWAT itself.

### 2.6 Data files and examples

| File | Nature |
| --- | --- |
| `input/metadata/properties/default.json` | parameter descriptions citing SWAT **input-file** names — `.BSN - CMN`, `.BSN - CDN`, `.BSN - SDNCO`, `.HRU - HRU_SLP`, `.HRU - OV_N`, `.HRU - SLSUBBSN` |

This is the **closest thing to a shared interface**: a common *parameter vocabulary*. RUFAS input
parameters are documented by reference to the SWAT input file and variable that inspired them
(`average_subbasin_slope` ↔ `HRU_SLP`, `manning` ↔ `OV_N`, `slope_length` ↔ `SLSUBBSN`). It is
documentation lineage, not a data exchange format.

### 2.7 Generated / non-source

- `output/logs/*.csv` — **44 files**, InputManager metadata dumps echoing the parameter
  descriptions above. `output/*` is gitignored (`.gitignore:30`), so these are run artefacts.
- `helpful_scripts/emissions_interpolation/geonames_US.csv` — **false positive**: the US place
  name *Swatara*.

---

## 3. Hydrological data flow

### 3.1 Orchestrator

`Field._cycle_water(current_conditions, time)` — `field/field/field.py:1466`. Its docstring states
the design intent explicitly (`field.py:1491-1493`):

> _"while this method is more messy and complex than it could be, this is a conscious design choice
> that will allow for SMEs to more easily and freely experiment with different orders of processes.
> This is necessary because there is not necessarily one correct order for processes to run in."_

**The flat, un-abstracted structure is deliberate.** That is the single most important architectural
fact in this document.

### 3.2 Inputs

| Input | Source | Used for |
| --- | --- | --- |
| `rainfall`, `irrigation` | `CurrentDayConditions` (from `Weather`) | total water |
| `max/min/mean_air_temperature` | `CurrentDayConditions` | Hargreaves PET, snow, soil temperature |
| `incoming_light` | `CurrentDayConditions` | PET, biomass |
| `daylength` | `Weather.get_current_day_conditions(time, latitude)` | dormancy |
| manure water | `Field._get_manure_water()` | total water |
| `field_size`, `seasonal_high_water_table`, irrigation settings, `absolute_latitude` | `FieldData` | percolation, watering, PET |
| `soil_layers[]` physical properties (bulk density, thickness, clay/sand/silt, `average_subbasin_slope`, `slope_length`, `manning`, `second_moisture_condition_parameter`, albedo) | `SoilData` / `LayerData`, from `input/data/soil/*.json` | all routines |
| `snow_melt_amount` | `SoilData` (written by `Snow`) | water reaching soil |

### 3.3 Execution sequence (`field.py:1496-1539`)

```
1496  manure_water            = _get_manure_water()
1497  watering_amount         = _determine_watering_amount(rainfall, manure_water, year, day, irrigation)
1504  total_water             = rainfall + watering_amount + manure_water
1505  precipitation_reaching_soil = _handle_water_in_crop_canopies(total_water)
1506  water_reaching_soil     = precipitation_reaching_soil + soil.data.snow_melt_amount
1508  full_evapotranspirative_demand = _determine_potential_evapotranspiration(...)   # Hargreaves
1516  remaining_demand        = _evaporate_from_crop_canopies(full_evapotranspirative_demand)
1518  soil.percolation.percolate(seasonal_high_water_table)
1519  soil.infiltration.infiltrate(water_reaching_soil)                                # SCS-CN
1520  soil.percolation.percolate_infiltrated_water()
1522  soil.soil_erosion.erode(field_size, 0.02, current_residue, total_water)          # MUSLE
1528  soil.phosphorus_cycling.cycle_phosphorus(...)
1534  soil.carbon_cycling.cycle_carbon(...)
1539  soil.nitrogen_cycling.cycle_nitrogen(field_size)
```

Note `field.py:1524` passes a **hardcoded `0.02`** as the minimum cover-management factor to
`erode(...)`, rather than a crop- or field-derived value.

### 3.4 Outputs

All routines return `None` and mutate `SoilData` / `LayerData` in place:

| Output | Written by | Held on |
| --- | --- | --- |
| `accumulated_runoff`, retention parameter, adjusted curve number | `Infiltration` | `SoilData` |
| layer `water_content`, `percolated_water` | `Percolation`, `Infiltration` | `LayerData` |
| sediment yield, peak runoff rate | `SoilErosion` | `SoilData` |
| `snow_melt_amount`, snow pack water content | `Snow` | `SoilData` |
| layer `temperature` | `SoilTemp` | `LayerData` |
| `transpiration`, `max_transpiration`, `max_evapotranspiration` | `WaterUptake`, `Field` | `FieldData`, `CropData` |

### 3.5 Consumers of hydrological output

| Consumer | Reads | Coupling |
| --- | --- | --- |
| `soil/phosphorus_cycling/**` | `accumulated_runoff`, percolated water | **tight** — runoff is a direct argument to `cycle_phosphorus` |
| `soil/nitrogen_cycling/leaching_runoff_erosion.py` | runoff, percolation, erosion | **tight** |
| `soil/carbon_cycling/**` | soil water factor, temperature | **medium** |
| `crop/growth_constraints.py` | `water_uptake` vs `max_transpiration` → water stress | **tight** |
| `crop/water_uptake.py`, `water_dynamics.py` | layer water content | **tight** |
| `soil/soil_erosion.py` | `accumulated_runoff` from infiltration | **tight**, same-step ordering dependency |
| `field/manager/field_data_reporter.py` | everything, for reporting | **loose** — read-only, no feedback |
| `RUFAS/EEE/**` | nothing hydrological | **none** |

---

## 4. Extension points

### 4.1 Abstract classes and protocols

RUFAS contains **exactly three** ABCs:

| ABC | File | Abstract methods | Hydrology-relevant? |
| --- | --- | ---: | --- |
| `NutrientUptake` | `field/crop/nutrient_uptake.py:6` | 1 (`uptake`) | **partially** — `WaterUptake` inherits from it |
| `Disease` | `animal/animal_health/disease.py:7` | 7 | no |
| `Processor` | `manure/processor.py:14` | 2 | no |

**`typing.Protocol` is used nowhere** in RUFAS — there is no structural typing anywhere in the
codebase.

So the only declared abstraction touching hydrology is `NutrientUptake`, and it covers **plant
water uptake only**:

```
NutrientUptake (ABC)          nutrient_uptake.py:6, one @abstractmethod: uptake(soil_data)
├── WaterUptake               water_uptake.py:9      <-- the sole hydrology implementer
└── NonWaterUptake            non_water_uptake.py:10
    ├── NitrogenUptake
    └── PhosphorusUptake
```

**The soil-side hydrology has no abstract base at all.** `Infiltration`, `Percolation`,
`Evaporation`, `SoilErosion`, `Snow`, and `SoilTemp` are plain classes with no shared parent and no
declared interface. They share only an undeclared convention: `__init__(self, soil_data, field_size=None)`
storing `self.data`, and a public method that returns `None` and mutates `self.data`.

### 4.2 Configuration flags for model selection

**None.** There is no config key that selects a hydrological method — no runoff-method switch, no
PET-method switch, no alternative percolation. The only related flags are the four crop stress
toggles (`simulate_water_stress`, `simulate_temp_stress`, `simulate_nitrogen_stress`,
`simulate_phosphorus_stress`), which disable *stress effects on growth*, not the hydrology itself.

### 4.3 "TODO: add SWAT+" or similar markers

**None.** No `TODO` or `FIXME` in `RUFAS/**/*.py` mentions SWAT, hydrology, runoff, percolation, or
infiltration. There is no in-code signal that a SWAT+ integration was ever planned or started.

The only in-flight related work found is
`openspec/changes/integrate-slope-aspect-api/proposal.md`, which concerns sourcing slope and aspect
from an external API — feeding `average_subbasin_slope` / `slope_length`, i.e. **MUSLE inputs**,
not a hydrology engine swap.

---

## 5. Architectural findings

### 5.1 Is the hydrology abstracted or tightly coupled?

**Tightly coupled through shared mutable state, but weakly coupled by import.** The two are
different axes and they point in opposite directions.

| Axis | Assessment |
| --- | --- |
| Import coupling | **loose** — each routine imports only `SoilData` (some also `LayerData`, `GeneralConstants`). Substituting one is a one-line change at the construction site. |
| State coupling | **tight** — every routine mutates the shared `SoilData` in place and returns `None`. There is no data contract saying which fields a routine may touch. |
| Ordering coupling | **tight and implicit** — `SoilErosion` needs `accumulated_runoff` written by `Infiltration` in the same step; `cycle_phosphorus` takes it as an argument. Order exists only as statement order in `_cycle_water`. |
| Interface coupling | **none declared** — no ABC, no Protocol. Substitution works by duck typing. |

### 5.2 Would replacing or extending the hydrology require deep changes?

Cost depends entirely on which axis you touch:

| Change | Cost | Why |
| --- | --- | --- |
| Swap one routine for a same-signature alternative (e.g. Green-Ampt for SCS-CN) | **low** | one construction line in `Soil.__init__` (`soil.py:57-66`) plus one call line in `_cycle_water`; no interface to satisfy |
| Add a config flag to choose between two implementations | **low–medium** | no precedent exists; would need a new input key, `SoilConfigFactory`-style dispatch, and metadata schema entry |
| Introduce an ABC for soil hydrology routines | **medium** | six classes already share the constructor convention; formalising it is mechanical, but mypy strict and the flake8 complexity ceiling apply |
| Replace the water-balance *state model* (e.g. different layer discretisation) | **high** | `SoilData` is imported by 34 of 173 biophysical modules — the widest blast radius in the codebase |
| Delegate hydrology to an external engine (SWAT+ or other) | **high** | nothing exists to build on: no serialisation, no adapter, no file format, no process boundary, no dependency. It would be new construction, not integration. |

The `_cycle_water` docstring's "conscious design choice" note means the flat structure is a
**maintained position, not neglect** — a proposal to abstract it should expect to argue against
that stated intent.

### 5.3 Dead code in the hydrology path

| Item | Status |
| --- | --- |
| `Soil.daily_soil_water_routine` (`soil.py:109`) | **dead and broken** — no production caller; calls `infiltrate()` with 3 args against a 1-arg signature, so it raises `TypeError`. Production drives components directly from `Field._cycle_water`. Its test masks this with a bare `MagicMock()`. |
| `Soil.daily_soil_routine` (`soil.py:68`) | **dead** — no production caller; soil temperature is driven elsewhere |
| `SoilConfigFactory` / `SoilConfiguration` (`soil/soil_config_factory.py`) | **dead** — no caller anywhere; duplicates `FieldManager._setup_soil` inline logic |
| `Snow.sublimate` | referenced by the `_cycle_water` docstring as _"not implemented in V1"_ — the method exists; whether it is reached in the live path was not traced here |
| Alternative hydrology implementations | **none** — no superseded runoff/PET/percolation code was found. There is no archaeological layer of an older model. |

### 5.4 Bottom line for the decision

- There is **no SWAT+ integration to extend, and no interface to reuse**. The relationship is
  scientific provenance: RUFAS reimplements SWAT equations in Python and cites them in docstrings.
- The nearest thing to a shared contract is the **input parameter vocabulary** documented against
  SWAT input files (`.BSN`, `.HRU`) in `input/metadata/properties/default.json`. If interoperability
  with SWAT+ is ever wanted, that vocabulary — not the code — is the existing common ground.
- Swapping an individual routine is cheap and unblocked. Delegating hydrology wholesale to an
  external engine is new construction with no existing scaffolding.
- Any such proposal must contend with the explicit design statement at `field.py:1491-1493` that
  the flat, reorderable structure is intentional.

---

## Provenance

Produced at commit `ef1f22e` by AST parsing, Python `tokenize`-based comment/string stripping, and
targeted reads of the files cited. Every line number, signature, and quotation is verbatim from
source. No RUFAS module was imported and no RUFAS code was executed. Negative findings ("absent",
"zero") are name-based across `RUFAS/**/*.py` and the repository tree; dynamic dispatch or
runtime-constructed names would not be visible to this method.
