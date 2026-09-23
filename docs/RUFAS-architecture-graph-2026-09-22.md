# RUFAS — architecture graph

**Repository:** `C:\Proyectos\RuFaS-MyForageSystem` (MSF fork of RuFaS)
**Branch / commit:** `research/andrea-msf-prototype` @ `49118c2` (2026-09-16)
**Scope read:** 206 `.py` files under `RUFAS/`, plus `prototype_msf/`, `input/metadata/`, `docs/scientific/`, `tests/`
**Method:** static reads and greps only. No RUFAS module was imported or executed.
**Generated:** 2026-09-22
**Purpose:** source material for a figure of the RUFAS data-flow architecture.

## Ground rules applied throughout

1. Every claim carries a `file:line` reference.
2. Anything not found in the code is written **NOT FOUND IN CODE** — never filled in from expectation.
3. Where the code does not declare a unit, the entry reads **unit not declared**. No unit is inferred
   from a variable name.
4. Where two code paths are possible, **both are reported** and neither is chosen.
5. Three perimeters are kept distinct and never merged:
   - **RUFAS upstream** — code under `RUFAS/`, inherited from upstream RuFaS.
   - **MSF fork** — what is specific to this branch (chiefly `prototype_msf/` and `openspec/`).
   - **`spatializer_v2`** — MSF code that is **not part of RUFAS**; it lives in
     `C:\Proyectos\terranimo-test\` with a copy under
     `prototype_msf/spatializer_workspace/spatializer_v2/`, and reaches RUFAS only through an
     adapter. See §6.4.

---

## 1. Module inventory

Classification used: `orchestrator` (calls other modules, computes no biophysical process),
`biophysical core` (computes a process), `data structure` (carries state), `helper` (cross-cutting
service).

### 1.1 Top level `RUFAS/`

| Module | `file:line` (class) | What it computes | Class |
|---|---|---|---|
| simulation_engine | `RUFAS/simulation_engine.py:124` `SimulationEngine`; `:36` `SimulationType` | Annual/daily loop, dispatch to the 4 managers | orchestrator |
| rufas_time | `RUFAS/rufas_time.py:11` `RufasTime` | Current date, Julian day, `simulation_day`, `advance()` `:30`, `record_time()` `:107` | data structure |
| weather | `RUFAS/weather.py:12` `Weather` | Serves the day's weather (`get_current_day_conditions`, called at `simulation_engine.py:550`) | helper |
| current_day_conditions | `RUFAS/current_day_conditions.py:10` `CurrentDayConditions` | Per-day weather bundle | data structure |
| input_manager | `RUFAS/input_manager.py:60` `InputManager` | Loads/validates inputs into a pool (`:97`, `:790`); singleton `__new__` `:67` | helper |
| output_manager | `RUFAS/output_manager.py:100` `OutputManager` (+ `:28` `LogVerbosity`, `:78` `OriginLabel`) | Variable/log/error recording | helper |
| general_constants | `RUFAS/general_constants.py:4` `GeneralConstants` | Constants and conversion factors | data structure |
| user_constants | `RUFAS/user_constants.py:5` `UserConstants` | User-overridable constants | data structure |
| util | `RUFAS/util.py:19` `Utility`, `:1118` `Aggregator` | Generic utilities / aggregation | helper |
| units | `RUFAS/units.py:6` `MeasurementUnits` | Unit enum | data structure |
| data_validator | `RUFAS/data_validator.py:24,44,151` | Input schema validation | helper |
| graph_generator | `RUFAS/graph_generator.py:126` | Plots — **not opened in detail** | helper |
| report_generator | `RUFAS/report_generator.py:22` (`generate_report` `:48`) | Aggregated reports — **not opened in detail** | helper |
| task_manager | `RUFAS/task_manager.py:70` | CLI/tasks — **not opened in detail** | helper |
| e2e_test_results_handler | `RUFAS/e2e_test_results_handler.py:20` | E2E results — **not opened in detail** | helper |
| data_collection_app_updater | `RUFAS/data_collection_app_updater.py:38` | Collection-app update — **not opened in detail** | helper |

### 1.2 `RUFAS/EEE/`

| Module | `file:line` | Role | Class |
|---|---|---|---|
| EEE_manager | `RUFAS/EEE/EEE_manager.py:7` `EEEManager` (`estimate_all` `:11`, staticmethod) | Triggers post-simulation estimation | orchestrator |
| emissions | `RUFAS/EEE/emissions.py:77` `EmissionsEstimator` (`estimate_farmgrown_feed_emissions` `:261`, `calculate_purchased_feed_emissions` `:178`) | Emissions | biophysical core |
| energy | `RUFAS/EEE/energy.py:128` `EnergyEstimator` (`estimate_all` `:132`) | Energy use | biophysical core |
| tractor / tractor_implement | `RUFAS/EEE/tractor.py:23` `Tractor`; `RUFAS/EEE/tractor_implement.py:13` `TractorImplement` | Machinery specs | data structure |

### 1.3 `RUFAS/data_structures/` — all `data structure`

`animal_to_manure_connection.py:9` `StreamType`, `:26` `PenManureData`, `:135` `ManureStream` ·
`crop_soil_to_feed_storage_connection.py:12` `HarvestedCrop` ·
`events.py:10` `BaseFieldManagementEvent`, `:74` `PlantingEvent`, `:120` `HarvestEvent`, `:170`
`TillageEvent`, `:237` `ManureEvent`, `:334` `FertilizerEvent` ·
`feed_storage_to_animal_connection.py:59` `Feed`, `:179` `NASEMFeed`, `:365` `NRCFeed`, `:501`
`RequestedFeed`, `:538` `FeedFulfillmentResults` ·
`manure_nutrients.py:11` `ManureNutrients` ·
`manure_to_crop_soil_connection.py:42` `NutrientRequest`, `:86` `NutrientRequestResults`, `:247`
`ManureEventNutrientRequest`, `:255` `ManureEventNutrientRequestResults`, `:263` `FieldManureSupplier` ·
`manure_types.py:4` `ManureType` · `manure_supplement_methods.py:4` · `tillage_implements.py:4,9,18`.

### 1.4 `RUFAS/biophysical/field/soil/` — separable submodules

| Submodule | Class(es) | What it computes | Class |
|---|---|---|---|
| `soil.py:16` | `Soil` | Composer: instantiates the 9 components (`:57-66`); exposes `daily_soil_routine` (`:68`) and `daily_soil_water_routine` (`:109`) — **see the ambiguity in §3.4** | orchestrator |
| `soil_data.py:13` | `SoilData` | Profile state + aggregates (`profile_*`, `:461-711`), `do_annual_reset` (`:426`) | data structure |
| `layer_data.py:10` | `LayerData` | Per-layer state + T/water factors (`:791`, `:814`), `do_annual_reset` (`:1015`) | data structure |
| `infiltration.py:6` | `Infiltration` | `infiltrate` (`:29`) | biophysical core |
| `percolation.py:8` | `Percolation` | `percolate` (`:32`), `percolate_infiltrated_water` (`:89`) | biophysical core |
| `evaporation.py:7` | `Evaporation` | `evaporate` (`:30`), per-layer loop (`:49`) | biophysical core |
| `snow.py:8` | `Snow` | `update_snow` (`:141`), `sublimate` (`:202`) | biophysical core |
| `soil_temp.py:6` | `SoilTemp` | `daily_soil_temperature_update` (`:25`), per-layer loop (`:86`) | biophysical core |
| `soil_erosion.py:12` | `SoilErosion` | `erode` (`:44`) | biophysical core |
| `manure_pool.py:7` | `ManurePool` | Surface manure pool: `daily_manure_update` (`:85`), `runoff_reset` (`:208`), `leach_phosphorus_pools` (`:213`) | biophysical core + state |
| `soil_config_factory.py:9,15` | `SoilConfiguration`, `SoilConfigFactory` | `create_soil_data` (`:23`) | helper / factory |

**Carbon cycling** `soil/carbon_cycling/`: `carbon_cycle.py:8` `CarbonCycling` (`cycle_carbon` `:48`;
internal orchestrator) · `decomposition.py:6` `Decomposition` (`:41`) · `residue_partition.py:7`
`ResiduePartition` (`:35`, `:59`) · `pool_gas_partition.py:4` `PoolGasPartition` (`:33`) — all
`biophysical core`.

**Nitrogen cycling** `soil/nitrogen_cycling/`: `nitrogen_cycling.py:9` `NitrogenCycling` (`:48`) ·
`leaching_runoff_erosion.py:14` (`:50`) · `nitrification_volatilization.py:6` (`:35`) ·
`denitrification.py:8` (`:35`) · `mineralization_decomp.py:6` (`:28`) · `humus_mineralization.py:5`
(`:33`) — all `biophysical core`.

**Phosphorus cycling** `soil/phosphorus_cycling/`: `phosphorus_cycling.py:8` `PhosphorusCycling`
(`:44`) · `manure.py:4` `Manure` (`:27`) · `fertilizer.py:7` `Fertilizer` (`:31`, `:140`) ·
`phosphorus_mineralization.py:6` (`:29`) · `soluble_phosphorus.py:8` (`:44`) — all `biophysical core`.

### 1.5 `field/crop/`, `field/field/`, `field/manager/`

**Crop** (`biophysical core` unless noted): `crop.py:26` `Crop` (`perform_daily_crop_update` `:127`,
`cycle_water_for_crop` `:165`) · `crop_data.py:43` `CropData` (*data structure*) + `:6` `PlantCategory` ·
`crop_data_factory.py:52` (*helper*) · `heat_units.py:4` · `root_development.py:9` ·
`nitrogen_uptake.py:7` · `phosphorus_uptake.py:10` · `non_water_uptake.py:10` · `nutrient_uptake.py:6`
(ABC) · `growth_constraints.py:6` · `leaf_area_index.py:7` · `biomass_allocation.py:6` ·
`water_uptake.py:9` · `water_dynamics.py:4` · `dormancy.py:5` · `crop_management.py:14` ·
`harvest_operations.py:4` (enum).

**Field**: `field.py:37` `Field` (`manage_field` `:143` — field-level orchestrator) · `field_data.py:9`
`FieldData` (*data structure*, `perform_annual_field_reset` `:144`) · `fertilizer_application.py:4` ·
`manure_application.py:13` · `tillage_application.py:9`.

**Manager**: `field_manager.py:31` `FieldManager` (*orchestrator*; `daily_update_routine` `:65`,
`annual_update_routine` `:113`, `check_manure_schedules` `:633`) · `schedule.py:8` `Schedule` +
`crop_schedule.py:8`, `fertilizer_schedule.py:8`, `manure_schedule.py:11`, `tillage_schedule.py:10`
(*data structure*) · `field_data_reporter.py:9` (*helper*).

### 1.6 `biophysical/animal/`

*Orchestrators*: `herd_manager.py:55` `HerdManager` · `pen.py:41` `Pen` · `herd_factory.py:36` `HerdFactory`.

*Biophysical core*: `animal.py:73` `Animal` (`daily_routines` `:1871`) · `growth/growth.py:16` ·
`milk/milk_production.py:16`, `milk/lactation_curve.py:53` · `nutrients/nutrients.py:8` and the
calculators `nasem_requirements_calculator.py:16`, `nrc_requirements_calculator.py:12`,
`beef_nrc_requirements_calculator.py:20`, `beef_cow_calf_requirements_calculator.py:79`,
`nutrition_supply_calculator.py:27`, `nutrition_evaluator.py:10` ·
`digestive_system/digestive_system.py:12`, `enteric_methane_calculator.py:11`,
`manure_excretion_calculator.py:14`, `methane_mitigation_calculator.py:1` ·
`reproduction/reproduction.py:45`, `repro_state_manager.py:5`, `hormone_delivery_schedule.py:14` ·
`animal_genetics/animal_genetics.py:37` · `animal_health/animal_health.py:7`, `disease.py:7`
(**orphan — see §9**) · `bedding/bedding.py:4`.

*Helpers*: `ration/ration_manager.py:19`, `ration_optimizer.py:106`, `calf_ration_manager.py:21`,
`amino_acid.py:171`, `animal_module_reporter.py:36`, `animal_config.py:20`,
`animal_module_constants.py:6`. `data_types/*` = data structures.

### 1.7 `biophysical/manure/`

*Orchestrator*: `manure_manager.py:46` `ManureManager`.
*Biophysical core*: `processor.py:14` `Processor` (ABC) · `handler/handler.py:13`,
`parlor_cleaning.py:9`, `single_stream_handler.py:9` · `separator/separator.py:10` ·
`digester/digester.py:4`, `continuous_mix.py:12` · `storage/storage.py:32` `Storage`,
`anaerobic_lagoon.py:14`, `bedded_pack.py:42`, `composting.py:53`, `daily_spread.py:10`,
`open_lot.py:15`, `slurry_storage_outdoor.py:16`, `slurry_storage_underfloor.py:14`,
`solids_storage_calculator.py:9`.
*Helper / state*: `manure_nutrient_manager.py:12`.
*Data structure*: `manure_constants.py:4`, `processor_enum.py:19`, `composting_type.py:4`,
`storage_cover.py:4`.

### 1.8 `biophysical/feed_storage/`

`feed_manager.py:32` `FeedManager` (*orchestrator*) · `storage.py:55` `Storage` (base) + `hay.py:29`,
`silage.py:18`, `baleage.py:11`, `grain.py:4`, `purchased_feed_storage.py:34` (*biophysical core*) ·
`feed_storage_enum.py:11` (*data structure*).

---
## 2. Data-flow edge graph

**219 edges**, each one anchored to a `file:line` that was opened. The same 219 edges are repeated
verbatim at the end of this document (§11) as a flat pipe-separated list, for import into a graph
tool.

**Column meaning** (header names as requested):

- `origen` / `destino` — module or state object at each end.
- `variable` — short description of what travels. **These descriptions are in Spanish**, kept exactly
  as produced during the code walk; translating them would have meant re-deriving 219 rows and
  risking drift. Every other column is language-neutral.
- `nombre_codigo` — the identifier as spelled in the source.
- `unidad` — the unit **as declared in a docstring or a `MeasurementUnits` argument**. Where the code
  declares none, the cell reads `unidad no declarada` — **73 of 219 edges (33 %)** are in that state.
  No unit was inferred from a variable name.
- `timestep` — `daily`, `per-event`, `init`, `annual`, or `annual (post-simulación)`.
- `tipo` — Python type carried.
- `via_estado` — **the key column.** `arg` means the value is passed as a function argument.
  `estado: X` means the value never appears in a signature: the producer writes attribute `X` of a
  shared object and the consumer reads it later. These are the edges that an architecture figure
  usually misses.

### 2.1 Three transport mechanisms, not one

The graph has three distinct kinds of edge, and they behave differently:

1. **Argument passing** — scalars pulled out of `CurrentDayConditions` and handed down. Visible in
   signatures, easy to trace.
2. **Shared-state mutation (aliasing)** — the dominant pattern inside the field. `SoilData`,
   `LayerData`, `CropData`, `FieldData`, `ManureStream.pen_manure_data` and
   `Weather.weather_data[date]` are mutated in place by modules that received them as arguments.
   The full list of these aliasing edges is §2.4.
3. **`OutputManager` as a deferred channel** — EEE does not receive data from the field modules. It
   **reads back**, after the simulation, variables that Field / CropManagement / TillageApplication /
   FeedManager wrote into the output pool during the run, via `filter_variables_pool`
   (`RUFAS/EEE/energy.py:288`). This is a real data dependency that no call graph shows: 13 edges,
   §2.3.11.

**Asymmetry worth noting:** the biophysical modules (field, soil, crop, animal, manure) never read
from `OutputManager`. EEE is the only module that reads the pool back — verified by grep, reported
as a finding rather than an absence.

### 2.2 Ambiguity carried, not resolved

The manure nutrient request resolves through **one of two suppliers**, selected at runtime by the
`simulate_manure` flag:

```
RUFAS/simulation_engine.py:439-442
    if self.simulate_manure:
        manure_request_results = self.manure_manager.request_nutrients(manure_request, self.time)
    else:
        manure_request_results = FieldManureSupplier.request_nutrients(manure_request)
```

Both edges are present in the list and both are tagged `arg — AMBIGÜEDAD`. Neither was chosen.

### 2.3 Edges grouped by originating subsystem

##### 2.3.1 Configuration load — 1 edge

| origen | destino | variable | nombre_codigo | unidad | timestep | tipo | archivo:linea | via_estado |
|---|---|---|---|---|---|---|---|---|
| `input_manager` | `weather` | datos meteorológicos crudos | `weather_data` | unidad no declarada | init | dict | `RUFAS\simulation_engine.py:207` | arg |

##### 2.3.2 Weather — 24 edges

| origen | destino | variable | nombre_codigo | unidad | timestep | tipo | archivo:linea | via_estado |
|---|---|---|---|---|---|---|---|---|
| `weather` | `weather` | condiciones diarias indexadas por fecha | `weather_data[date_key]` | unidad no declarada | init | dict[date, CurrentDayConditions] | `RUFAS\weather.py:90` | estado: Weather.weather_data |
| `weather` | `weather` | precipitación repartida a lluvia o nieve | `snowfall / rainfall` | mm | init (post_init del dataclass) | escalar | `RUFAS\current_day_conditions.py:60-62` | estado: CurrentDayConditions.snowfall/.rainfall |
| `weather` | `weather` | duración del día para la latitud del campo | `daylength` | hours | daily | escalar | `RUFAS\weather.py:177` | estado: Weather.weather_data[date].daylength |
| `weather` | `weather` | temperatura media anual del aire | `annual_mean_air_temperature` | degrees C | daily | escalar | `RUFAS\weather.py:178` | estado: Weather.weather_data[date].annual_mean_air_temperature |
| `weather` | `weather` | temperatura media anual de toda la simulación | `mean_annual_temperature` | degrees C | init | escalar | `RUFAS\weather.py:92` | estado: Weather.mean_annual_temperature |
| `weather` | `manure.ManureManager` | intercepto/desfase/amplitud de la curva sinusoidal de temperatura | `intercept_mean_temp, phase_shift, amplitude` | degrees C (intercept, amplitude) / days (phase_shift) - unidad no declarada en código | init | escalar | `RUFAS\simulation_engine.py:258` | arg |
| `weather` | `field.manager.FieldManager` | condiciones del día para la latitud del campo | `current_conditions` | unidad no declarada | daily | dataclass CurrentDayConditions | `RUFAS\biophysical\field\manager\field_manager.py:94` | arg |
| `weather` | `field.field.Field` | lluvia del día para el riego | `current_conditions.rainfall` | mm | daily | escalar | `RUFAS\biophysical\field\field\field.py:1498` | arg |
| `weather` | `field.field.Field` | riego prefijado en el archivo meteorológico | `current_conditions.irrigation` | mm | daily | escalar | `RUFAS\biophysical\field\field\field.py:1502` | arg |
| `weather` | `feed_storage.FeedManager` | condiciones meteorológicas para degradación de forrajes | `weather` | unidad no declarada | per-event (intervalo de 30 días) | objeto Weather | `RUFAS\simulation_engine.py:519 → feed_manager.py:349` | arg |
| `weather` | `feed_storage.FeedManager` | meteorología para proyectar inventario | `weather` | unidad no declarada | daily | objeto Weather | `RUFAS\simulation_engine.py:504 → feed_manager.py:532` | arg |
| `weather` | `animal.HerdManager` | temperatura media del aire para formular raciones | `current_temperature` | degrees C | per-event (intervalo de ración) | escalar | `RUFAS\simulation_engine.py:550-556` | arg |
| `weather` | `animal.HerdManager` | temperatura media para requisitos nutricionales de los corrales | `weather.get_current_day_conditions(time).mean_air_temperature` | degrees C | daily | escalar | `RUFAS\biophysical\animal\herd_manager.py:1657-1659` | arg |
| `weather` | `animal.HerdManager` | condiciones del día para reestructurar el rebaño | `current_day_conditions` | unidad no declarada | daily | dataclass CurrentDayConditions | `RUFAS\biophysical\animal\herd_manager.py:743` | arg |
| `weather` | `animal.Pen` | temperatura media para requisitos nutricionales al insertar animal | `current_day_conditions.mean_air_temperature` | degrees C | per-event | escalar | `RUFAS\biophysical\animal\herd_manager.py:1219` | arg |
| `weather` | `animal.HerdManager` | temperatura media para reformular la ración de un corral | `current_temperature` | degrees C | per-event | escalar | `RUFAS\biophysical\animal\herd_manager.py:1232` | arg |
| `weather` | `manure.handler.Handler` | temperatura media del aire → temperatura del establo | `conditions.mean_air_temperature` | degrees C | daily | escalar | `RUFAS\biophysical\manure\handler\handler.py:125` | arg |
| `weather` | `manure.storage.SlurryStorageOutdoor` | precipitación añadida al volumen y agua del depósito | `current_day_conditions.precipitation` | mm (convertido a m) | daily | escalar | `RUFAS\biophysical\manure\storage\slurry_storage_outdoor.py:58-60` | estado: Storage._received_manure.volume/.water |
| `weather` | `manure.storage.AnaerobicLagoon` | precipitación añadida al volumen del lagunaje | `current_day_conditions.precipitation` | mm (convertido a m) | daily | escalar | `RUFAS\biophysical\manure\storage\anaerobic_lagoon.py:74` | estado: Storage._received_manure |
| `weather` | `manure.storage.Composting` | temperatura media anual del aire | `current_day_conditions.annual_mean_air_temperature` | degrees C | daily | escalar | `RUFAS\biophysical\manure\storage\composting.py:107` | arg |
| `weather` | `manure.storage.Composting` | temperatura media del aire del día | `current_day_conditions.mean_air_temperature` | degrees C | daily | escalar | `RUFAS\biophysical\manure\storage\composting.py:108` | arg |
| `weather` | `manure.storage.OpenLot` | temperatura media del aire para emisión de metano | `current_day_conditions.mean_air_temperature` | degrees C | daily | escalar | `RUFAS\biophysical\manure\storage\open_lot.py:52` | arg |
| `weather` | `manure.storage.BeddedPack` | temperatura media anual del aire | `current_day_conditions.annual_mean_air_temperature` | degrees C | daily | escalar | `RUFAS\biophysical\manure\storage\bedded_pack.py:80` | arg |
| `weather` | `OutputManager` | precipitación, lluvia, nieve, temperaturas, radiación, riego | `precipitation, rainfall, snowfall, maximum/minimum/average_temperature, radiation, irrigation` | MILLIMETERS / DEGREES_CELSIUS / MEGAJOULES_PER_SQUARE_METER | daily | escalar | `RUFAS\weather.py:241-274` | estado: OutputManager |

##### 2.3.3 Field manager — 11 edges

| origen | destino | variable | nombre_codigo | unidad | timestep | tipo | archivo:linea | via_estado |
|---|---|---|---|---|---|---|---|---|
| `field.manager.FieldManager` | `OutputManager` | duración del día | `daylength` | HOURS | daily | escalar | `RUFAS\biophysical\field\manager\field_manager.py:101` | estado: OutputManager |
| `field.manager.FieldManager` | `field.field.Field` | condiciones del día | `current_conditions` | unidad no declarada | daily | dataclass CurrentDayConditions | `RUFAS\biophysical\field\manager\field_manager.py:105-106` | arg |
| `field.manager.FieldManager` | `simulation_engine` | cultivos cosechados de todos los campos | `harvested_crops` | unidad no declarada | daily | list[HarvestedCrop] | `RUFAS\biophysical\field\manager\field_manager.py:108,111` | arg |
| `field.manager.FieldManager` | `simulation_engine` | próximas fechas de cosecha por cultivo | `next_harvest_dates` | unidad no declarada (date) | daily | dict[str, date] | `RUFAS\biophysical\field\manager\field_manager.py:147` | arg |
| `field.manager.FieldManager` | `simulation_engine` | peticiones de estiércol del campo | `manure_requests` | unidad no declarada | daily | list[ManureEventNutrientRequest] | `RUFAS\biophysical\field\manager\field_manager.py:643-644` | arg |
| `field.manager.FieldManager` | `field.field.Field` | aplicaciones de estiércol filtradas para ese campo | `manure_applications_for_field` | unidad no declarada | daily | list[ManureEventNutrientRequestResults] | `RUFAS\biophysical\field\manager\field_manager.py:102-106` | arg |
| `field.manager.FieldDataReporter` | `OutputManager` | emisiones de óxido nitroso por capa | `nitrous_oxide_emissions` | KILOGRAMS_PER_HECTARE | daily | escalar (por capa) | `RUFAS\biophysical\field\manager\field_data_reporter.py:1184-1192` | estado: OutputManager |
| `field.manager.FieldDataReporter` | `OutputManager` | emisiones de amoníaco por capa | `ammonia_emissions` | KILOGRAMS_PER_HECTARE | daily | escalar (por capa) | `RUFAS\biophysical\field\manager\field_data_reporter.py:1206-1214` | estado: OutputManager |
| `field.manager.FieldManager` | `field.soil (SoilData/LayerData)` | configuración inicial del perfil de suelo (capas, pH, densidad, C org., N inicial…) | `LayerData(**config_dictionary), SoilData(field_size, **config_dictionary)` | mm (bottom_depth), ha (field_size); resto unidad no declarada | init | dataclass LayerData / SoilData | `RUFAS\biophysical\field\manager\field_manager.py:558,630` | arg |
| `field.manager.FieldManager` | `field.field.Field` | datos del campo, suelo y calendarios de eventos | `FieldData, Soil, PlantingEvent, HarvestEvent, TillageEvent, FertilizerEvent, ManureEvent` | ha (field_size), degrees (latitude) | init | dataclass + list | `RUFAS\biophysical\field\manager\field_manager.py:190-199` | arg |
| `field.manager.FieldManager` | `field.field.Field` | residuo inicial del suelo | `initial_residue` | kg / ha | init | escalar | `RUFAS\biophysical\field\manager\field_manager.py:523,628` | arg |

##### 2.3.4 Field — 53 edges

| origen | destino | variable | nombre_codigo | unidad | timestep | tipo | archivo:linea | via_estado |
|---|---|---|---|---|---|---|---|---|
| `field.field.Field` | `field.soil.snow.Snow` | condiciones del día (nevada, temp. media) | `current_day_conditions` | mm / degrees C | daily | dataclass CurrentDayConditions | `RUFAS\biophysical\field\field\field.py:1448` | arg |
| `field.field.Field` | `field.soil.snow.Snow` | demanda máxima de sublimación | `maximum_sublimation` | mm | daily | escalar | `RUFAS\biophysical\field\field\field.py:1565` | arg |
| `field.field.Field` | `field.soil.soil_temp.SoilTemp` | radiación solar incidente | `current_conditions.incoming_light` | MJ/m^2 | daily | escalar | `RUFAS\biophysical\field\field\field.py:1452` | arg |
| `field.field.Field` | `field.soil.soil_temp.SoilTemp` | temperatura media/mínima/máxima del aire | `mean_air_temperature, min_air_temperature, max_air_temperature` | degrees C | daily | escalar | `RUFAS\biophysical\field\field\field.py:1453-1455` | arg |
| `field.field.Field` | `field.soil.soil_temp.SoilTemp` | cobertura total de planta más residuo | `total_plant_cover` | kg per hectare | daily | escalar | `RUFAS\biophysical\field\field\field.py:1450,1456` | arg |
| `field.field.Field` | `field.soil.soil_temp.SoilTemp` | temperatura media anual del aire | `annual_mean_air_temperature` | degrees C | daily | escalar | `RUFAS\biophysical\field\field\field.py:1458` | arg |
| `field.field.Field` | `field.field.Field` | agua de aplicación de purín acumulada | `field_data.manure_water` | mm | per-event | escalar | `RUFAS\biophysical\field\field\field.py:953` | estado: FieldData.manure_water |
| `field.field.Field` | `field.field.Field` | agua de purín consumida y reseteada | `field_data.manure_water` | mm | daily | escalar | `RUFAS\biophysical\field\field\field.py:1646,1656` | estado: FieldData.manure_water |
| `field.field.Field` | `OutputManager` | agua aportada por purín | `manure_water` | MILLIMETERS | daily | escalar | `RUFAS\biophysical\field\field\field.py:1654` | estado: OutputManager |
| `field.field.Field` | `field.field.Field` | déficit hídrico del intervalo de riego | `field_data.current_water_deficit` | mm | daily | escalar | `RUFAS\biophysical\field\field\field.py:1616-1623` | estado: FieldData.current_water_deficit |
| `field.field.Field` | `field.field.Field` | riego anual acumulado | `field_data.annual_irrigation_water_use_total` | mm | daily | escalar | `RUFAS\biophysical\field\field\field.py:1624,1630` | estado: FieldData.annual_irrigation_water_use_total |
| `field.field.Field` | `OutputManager` | riego aplicado | `field_watering` | MILLIMETERS | per-event | escalar | `RUFAS\biophysical\field\field\field.py:1926` | estado: OutputManager |
| `field.field.Field` | `field.crop.Crop` | precipitación disponible para el dosel | `precipitation_reaching_soil` | mm | daily | escalar | `RUFAS\biophysical\field\field\field.py:1683` | arg |
| `field.field.Field` | `field.field.Field` | evapotranspiración potencial del día | `field_data.max_evapotranspiration` | mm | daily | escalar | `RUFAS\biophysical\field\field\field.py:1514` | estado: FieldData.max_evapotranspiration |
| `field.field.Field` | `field.crop.WaterDynamics` | demanda evapotranspirativa restante para el dosel | `evapotranspirative_demand` | mm | daily | escalar | `RUFAS\biophysical\field\field\field.py:1704` | arg |
| `field.field.Field` | `field.soil.percolation.Percolation` | presencia de nivel freático estacional alto | `field_data.seasonal_high_water_table` | unidad no declarada (bool) | daily | escalar | `RUFAS\biophysical\field\field\field.py:1518` | arg |
| `field.field.Field` | `field.soil.infiltration.Infiltration` | agua que alcanza la superficie del suelo | `water_reaching_soil` | mm | daily | escalar | `RUFAS\biophysical\field\field\field.py:1519` | arg |
| `field.field.Field` | `field.soil.soil_erosion.SoilErosion` | tamaño del campo, factor C mínimo, residuo y agua total | `field_size, 0.02, current_residue, total_water` | ha / unitless / kg per hectare / mm | daily | escalar | `RUFAS\biophysical\field\field\field.py:1522-1527` | arg |
| `field.field.Field` | `field.soil.phosphorus_cycling.PhosphorusCycling` | agua que llega al suelo, escorrentía, tamaño de campo, temperatura media | `water_reaching_soil, accumulated_runoff, field_size, mean_air_temperature` | mm / mm / ha / °C | daily | escalar | `RUFAS\biophysical\field\field\field.py:1528-1533` | arg |
| `field.field.Field` | `field.soil.carbon_cycling.CarbonCycling` | agua que llega al suelo, temperatura media, tamaño de campo | `water_reaching_soil, mean_air_temperature, field_size` | mm / °C / ha | daily | escalar | `RUFAS\biophysical\field\field\field.py:1534-1538` | arg |
| `field.field.Field` | `field.soil.nitrogen_cycling.NitrogenCycling` | tamaño del campo | `field_size` | ha | daily | escalar | `RUFAS\biophysical\field\field\field.py:1539` | arg |
| `field.field.Field` | `field.soil.evaporation.Evaporation` | evaporación máxima del suelo | `max_soil_evaporation` | mm | daily | escalar | `RUFAS\biophysical\field\field\field.py:1570` | arg |
| `field.field.Field` | `field.crop.WaterDynamics` | transpiración máxima del cultivo | `max_transpiration` | mm | daily | escalar | `RUFAS\biophysical\field\field\field.py:1544 → crop.py:262` | estado: CropData.max_transpiration |
| `field.field.Field` | `field.crop.Crop` | evaporación real y demanda evapotranspirativa total | `actual_evaporation, full_evapotranspirative_demand` | mm | daily | escalar | `RUFAS\biophysical\field\field\field.py:1576` | arg |
| `field.field.Field` | `field.crop.Crop` | condiciones del día, datos de campo y datos de suelo | `current_conditions, field_data, soil_data` | unidad no declarada | daily | dataclass CurrentDayConditions / FieldData / SoilData | `RUFAS\biophysical\field\field\field.py:1464` | arg |
| `field.field.Field` | `field.crop.Crop` | profundidad del fondo del perfil de suelo | `bottom_layer_depth` | mm | per-event (siembra) | escalar | `RUFAS\biophysical\field\field\field.py:1264-1265` | arg |
| `field.field.Field` | `field.crop.Crop` | proporción de campo por cultivo | `crop.data.field_proportion` | unidad no declarada | daily | escalar | `RUFAS\biophysical\field\field\field.py:1411` | estado: CropData.field_proportion |
| `field.field.Field` | `field.crop.Crop` | duración del día, umbral de dormancia, lluvia, suelo | `daylength, dormancy_threshold_daylength, rainfall, soil_data, soil` | hours / hours / mm | daily | escalar + dataclass | `RUFAS\biophysical\field\field\field.py:1425-1427` | arg |
| `field.field.Field` | `field.crop.crop_management.CropManagement` | operación de cosecha, nombre y tamaño de campo, tiempo, datos de suelo | `harvest_operation, field_name, field_size, time, soil_data` | ha (field_size) | per-event | escalar + dataclass SoilData | `RUFAS\biophysical\field\field\field.py:1383-1389 y 1189-1195` | arg |
| `field.field.Field` | `field.soil.carbon_cycling.residue_partition` | lluvia tras cosecha programada | `current_conditions.rainfall` | mm | per-event | escalar | `RUFAS\biophysical\field\field\field.py:1390` | arg |
| `field.field.Field` | `field.soil.carbon_cycling.residue_partition` | lluvia tras cosecha por unidades de calor | `rainfall` | mm | per-event | escalar | `RUFAS\biophysical\field\field\field.py:1196` | arg |
| `field.field.Field` | `field.manager.FieldManager` | lista de cultivos cosechados hoy | `harvested_crops` | unidad no declarada | daily | list[HarvestedCrop] | `RUFAS\biophysical\field\field\field.py:205,210` | arg |
| `field.field.Field` | `manure (NutrientRequest)` | petición de N y P de estiércol con tipo y flag de suplemento | `NutrientRequest(nitrogen, phosphorus, manure_type, use_supplemental_manure)` | kg | per-event | dataclass NutrientRequest | `RUFAS\biophysical\field\field\field.py:1120-1125` | arg |
| `field.field.Field` | `field.manager.FieldManager` | evento de estiércol acoplado a su petición de nutrientes | `ManureEventNutrientRequest(field_name, event, manure_request)` | unidad no declarada | per-event | NamedTuple | `RUFAS\biophysical\field\field\field.py:1084-1085` | arg |
| `field.field.Field` | `field.field.manure_application.ManureApplication` | materia seca, fracción seca, P total, cobertura, profundidad y fracción superficial | `dry_matter_mass, dry_matter_fraction, total_phosphorus_mass, field_coverage, application_depth, surface_remainder_fraction` | kg / unitless / kg / unitless / mm / unitless | per-event | escalar | `RUFAS\biophysical\field\field\field.py:649-663` | arg |
| `field.field.Field` | `field.field.manure_application.ManureApplication` | fracciones de N inorgánico, amonio y N orgánico | `inorganic_nitrogen_fraction, ammonium_fraction, organic_nitrogen_fraction` | unitless | per-event | escalar | `RUFAS\biophysical\field\field\field.py:657-661` | arg |
| `field.field.Field` | `field.field.manure_application.ManureApplication` | fracción de P inorgánico extraíble en agua | `water_extractable_inorganic_phosphorus_fraction` | unitless | per-event | escalar | `RUFAS\biophysical\field\field\field.py:662` | arg |
| `field.field.manure_application.ManureApplication` | `field.soil (SoilData)` | pools de P del estiércol de máquina | `machine_manure.water_extractable_inorganic/organic_phosphorus, stable_inorganic/organic_phosphorus` | kg | per-event | escalar | `RUFAS\biophysical\field\field\manure_application.py:209-229` | estado: SoilData.machine_manure |
| `field.field.manure_application.ManureApplication` | `field.soil (LayerData)` | P lábil y P activo de purín líquido infiltrado | `add_to_labile_phosphorus, add_to_active_phosphorus` | kg | per-event | escalar | `RUFAS\biophysical\field\field\manure_application.py:243,251` | estado: SoilData.soil_layers[0] |
| `field.field.manure_application.ManureApplication` | `field.soil (SoilData)` | masa seca, factor de humedad y cobertura del pool de estiércol | `machine_manure.manure_dry_mass/.manure_moisture_factor/.manure_field_coverage` | kg / unitless / unitless | per-event | escalar | `RUFAS\biophysical\field\field\manure_application.py:267-269` | estado: SoilData.machine_manure |
| `field.field.manure_application.ManureApplication` | `field.soil (LayerData)` | nitratos añadidos por estiércol | `soil_layers[i].nitrate_content` | kg/ha (masa/field_size) | per-event | escalar | `RUFAS\biophysical\field\field\manure_application.py:368` | estado: SoilData.soil_layers[i].nitrate_content |
| `field.field.manure_application.ManureApplication` | `field.soil (LayerData)` | amonio añadido por estiércol | `soil_layers[i].ammonium_content` | kg/ha | per-event | escalar | `RUFAS\biophysical\field\field\manure_application.py:369` | estado: SoilData.soil_layers[i].ammonium_content |
| `field.field.manure_application.ManureApplication` | `field.soil (LayerData)` | N orgánico estable y fresco añadidos | `stable_organic_nitrogen_content, fresh_organic_nitrogen_content` | kg/ha | per-event | escalar | `RUFAS\biophysical\field\field\manure_application.py:370-371` | estado: SoilData.soil_layers[i] |
| `field.field.manure_application.ManureApplication` | `field.soil (LayerData)` | P y N de aplicación subsuperficial repartidos por factor de profundidad | `_apply_subsurface_manure` | kg | per-event | escalar (por capa) | `RUFAS\biophysical\field\field\manure_application.py:441-455` | estado: SoilData.soil_layers[*] |
| `field.field.Field` | `field.field.fertilizer_application.FertilizerApplication` | P, N, fracción de amonio, profundidad, fracción superficial, tamaño de campo | `phosphorus_applied, nitrogen_applied, ammonium_fraction, application_depth, surface_remainder_fraction, field_size` | kg / kg / unitless / mm / unitless / ha | per-event | escalar | `RUFAS\biophysical\field\field\field.py:323-330` | arg |
| `field.field.fertilizer_application.FertilizerApplication` | `field.soil.phosphorus_cycling.fertilizer` | P de fertilizante en superficie | `add_fertilizer_phosphorus` | kg | per-event | escalar | `RUFAS\biophysical\field\field\fertilizer_application.py:72-74` | arg |
| `field.field.fertilizer_application.FertilizerApplication` | `field.soil (LayerData)` | nitratos y amonio de fertilizante en la capa superficial | `soil_layers[0].nitrate_content, .ammonium_content` | kg/ha | per-event | escalar | `RUFAS\biophysical\field\field\fertilizer_application.py:79-80` | estado: SoilData.soil_layers[0] |
| `field.field.Field` | `field.field.tillage_application.TillageApplication` | profundidad, fracción de incorporación, fracción de mezcla, implemento | `tillage_depth, incorporation_fraction, mixing_fraction, implement` | mm / unitless / unitless | per-event | escalar + enum TillageImplement | `RUFAS\biophysical\field\field\field.py:1057-1064` | arg |
| `field.field.tillage_application.TillageApplication` | `field.soil (SoilData)` | pools de P incorporados y mezclados entre capas | `available_phosphorus_pool, recalcitrant_phosphorus_pool, grazing_manure, machine_manure` | kg | per-event | escalar | `RUFAS\biophysical\field\field\tillage_application.py:115-131` | estado: SoilData |
| `field.field.Field` | `OutputManager` | aplicación de fertilizante (masa, N, P, K, profundidad, tamaño de campo, % arcilla) | `fertilizer_application` | KILOGRAMS / MILLIMETERS / HECTARE / PERCENT | per-event | dict | `RUFAS\biophysical\field\field\field.py:520` | estado: OutputManager |
| `field.field.Field` | `OutputManager` | aplicación de estiércol (materia seca, N, P, profundidad, cobertura) | `manure_application / manure_request` | DRY_KILOGRAMS / KILOGRAMS / MILLIMETERS | per-event | dict | `RUFAS\biophysical\field\field\field.py:924` | estado: OutputManager |
| `field.field.Field` | `OutputManager` | siembra de cultivo (crop, field_size, % arcilla, año, día) | `crop_planting` | UNITLESS / HECTARE / PERCENT | per-event | dict | `RUFAS\biophysical\field\field\field.py:1321` | estado: OutputManager |
| `field.field.Field` | `field.field.Field` | reset anual de totales de suelo y campo | `do_annual_reset, perform_annual_field_reset` | unidad no declarada | annual | — | `RUFAS\biophysical\field\field\field.py:1897-1898` | estado: SoilData / FieldData |

##### 2.3.5 Soil — 42 edges

| origen | destino | variable | nombre_codigo | unidad | timestep | tipo | archivo:linea | via_estado |
|---|---|---|---|---|---|---|---|---|
| `field.soil.snow.Snow` | `field.soil (SoilData)` | contenido de agua del manto de nieve | `snow_content` | mm H2O | daily | escalar | `RUFAS\biophysical\field\soil\snow.py:183` | estado: SoilData.snow_content |
| `field.soil.snow.Snow` | `field.soil (SoilData)` | agua de fusión de nieve del día | `snow_melt_amount` | mm H2O | daily | escalar | `RUFAS\biophysical\field\soil\snow.py:199` | estado: SoilData.snow_melt_amount |
| `field.soil.snow.Snow` | `field.soil (SoilData)` | reducción del manto por fusión | `snow_content` | mm H2O | daily | escalar | `RUFAS\biophysical\field\soil\snow.py:200` | estado: SoilData.snow_content |
| `field.soil.snow.Snow` | `field.soil (SoilData)` | agua sublimada | `water_sublimated` | mm | daily | escalar | `RUFAS\biophysical\field\soil\snow.py:217` | estado: SoilData.water_sublimated |
| `field.soil.snow.Snow` | `field.soil (SoilData)` | manto de nieve tras sublimación | `snow_content` | mm H2O | daily | escalar | `RUFAS\biophysical\field\soil\snow.py:218` | estado: SoilData.snow_content |
| `field.soil (SoilData)` | `field.soil.soil_temp.SoilTemp` | contenido de nieve como aislante | `self.soil.data.snow_content` | mm | daily | escalar | `RUFAS\biophysical\field\field\field.py:1457` | arg |
| `field.soil.soil_temp.SoilTemp` | `field.soil (LayerData)` | temperatura de cada capa de suelo | `layer.temperature` | degrees C | daily | escalar (por capa) | `RUFAS\biophysical\field\soil\soil_temp.py:91` | estado: SoilData.soil_layers[i].temperature |
| `field.soil.soil_temp.SoilTemp` | `field.soil (LayerData)` | temperatura de la capa del día previo | `layer.previous_day_temperature` | degrees C | daily | escalar (por capa) | `RUFAS\biophysical\field\soil\soil_temp.py:98` | estado: SoilData.soil_layers[i].previous_day_temperature |
| `field.soil (SoilData)` | `field.field.Field` | agua de fusión de nieve sumada al agua que llega al suelo | `self.soil.data.snow_melt_amount` | mm | daily | escalar | `RUFAS\biophysical\field\field\field.py:1506` | estado: SoilData.snow_melt_amount |
| `field.soil.percolation.Percolation` | `field.soil (LayerData)` | agua percolada por capa reseteada | `percolated_water` | unidad no declarada | daily | array (vectorizado por capa) | `RUFAS\biophysical\field\soil\percolation.py:56` | estado: SoilData.soil_layers[*].percolated_water |
| `field.soil.percolation.Percolation` | `field.soil (LayerData)` | agua percolada a la zona vadosa | `vadose_zone_layer.water_content` | unidad no declarada | daily | escalar | `RUFAS\biophysical\field\soil\percolation.py:85` | estado: SoilData.vadose_zone_layer.water_content |
| `field.soil (LayerData)` | `field.soil.infiltration.Infiltration` | temperatura de la capa superficial (suelo helado) | `self.data.soil_layers[0].temperature` | degrees C | daily | escalar | `RUFAS\biophysical\field\soil\infiltration.py:88` | estado: SoilData.soil_layers[0].temperature |
| `field.soil.infiltration.Infiltration` | `field.soil (SoilData)` | escorrentía acumulada del día | `accumulated_runoff` | mm | daily | escalar | `RUFAS\biophysical\field\soil\infiltration.py:94` | estado: SoilData.accumulated_runoff |
| `field.soil.infiltration.Infiltration` | `field.soil (SoilData)` | agua infiltrada | `infiltrated_water` | mm | daily | escalar | `RUFAS\biophysical\field\soil\infiltration.py:96` | estado: SoilData.infiltrated_water |
| `field.soil.infiltration.Infiltration` | `field.soil (SoilData)` | escorrentía anual acumulada | `annual_runoff_total` | mm | daily | escalar | `RUFAS\biophysical\field\soil\infiltration.py:99` | estado: SoilData.annual_runoff_total |
| `field.soil.infiltration.Infiltration` | `field.soil.percolation.Percolation` | agua infiltrada a repartir entre capas | `self.data.infiltrated_water` | mm | daily | escalar | `RUFAS\biophysical\field\soil\percolation.py:102` | estado: SoilData.infiltrated_water |
| `field.soil.percolation.Percolation` | `field.soil (LayerData)` | contenido de agua por capa tras infiltración | `layer.water_content` | unidad no declarada | daily | escalar (por capa) | `RUFAS\biophysical\field\soil\percolation.py:106,109` | estado: SoilData.soil_layers[i].water_content |
| `field.soil.percolation.Percolation` | `field.soil (LayerData)` | sobrante percolado a zona vadosa | `vadose_zone_layer.water_content` | unidad no declarada | daily | escalar | `RUFAS\biophysical\field\soil\percolation.py:114` | estado: SoilData.vadose_zone_layer.water_content |
| `field.soil (SoilData)` | `field.soil.soil_erosion.SoilErosion` | escorrentía acumulada | `self.data.accumulated_runoff` | mm | daily | escalar | `RUFAS\biophysical\field\soil\soil_erosion.py:106` | estado: SoilData.accumulated_runoff |
| `field.soil.soil_erosion.SoilErosion` | `field.soil (SoilData)` | volumen de escorrentía superficial | `surface_runoff_volume` | mm per hectare | daily | escalar | `RUFAS\biophysical\field\soil\soil_erosion.py:106` | estado: SoilData.surface_runoff_volume |
| `field.soil.soil_erosion.SoilErosion` | `field.soil (SoilData)` | sedimento erosionado | `eroded_sediment` | metric tons | daily | escalar | `RUFAS\biophysical\field\soil\soil_erosion.py:117` | estado: SoilData.eroded_sediment |
| `field.soil.soil_erosion.SoilErosion` | `field.soil (SoilData)` | totales anuales de sedimento y escorrentía | `annual_eroded_sediment_total, annual_surface_runoff_total` | metric tons / mm per hectare | daily | escalar | `RUFAS\biophysical\field\soil\soil_erosion.py:120-121` | estado: SoilData |
| `field.soil.phosphorus_cycling.PhosphorusCycling` | `field.soil.phosphorus_cycling.manure` | lluvia, escorrentía, tamaño de campo, temperatura media | `rainfall, runoff, field_size, mean_air_temperature` | mm / mm / ha / °C | daily | escalar | `RUFAS\biophysical\field\soil\phosphorus_cycling\phosphorus_cycling.py:65` | arg |
| `field.soil.phosphorus_cycling.PhosphorusCycling` | `field.soil.phosphorus_cycling.fertilizer` | lluvia, escorrentía, tamaño de campo | `rainfall, runoff, field_size` | mm / mm / ha | daily | escalar | `RUFAS\biophysical\field\soil\phosphorus_cycling\phosphorus_cycling.py:66` | arg |
| `field.soil.phosphorus_cycling.PhosphorusCycling` | `field.soil.phosphorus_cycling.mineralization` | tamaño del campo | `field_size` | ha | daily | escalar | `RUFAS\biophysical\field\soil\phosphorus_cycling\phosphorus_cycling.py:67` | arg |
| `field.soil.phosphorus_cycling.PhosphorusCycling` | `field.soil.phosphorus_cycling.soluble_phosphorus` | escorrentía y tamaño del campo | `runoff, field_size` | mm / ha | daily | escalar | `RUFAS\biophysical\field\soil\phosphorus_cycling\phosphorus_cycling.py:68` | arg |
| `field.soil.carbon_cycling.CarbonCycling` | `field.soil.carbon_cycling.residue_partition` | lluvia del día | `rainfall` | mm | daily | escalar | `RUFAS\biophysical\field\soil\carbon_cycling\carbon_cycle.py:63` | arg |
| `field.soil.carbon_cycling.CarbonCycling` | `field.soil (LayerData)` | fracción global de carbono del suelo por capa | `layer.soil_overall_carbon_fraction` | unidad no declarada | daily | escalar (por capa) | `RUFAS\biophysical\field\soil\carbon_cycling\carbon_cycle.py:91` | estado: SoilData.soil_layers[i].soil_overall_carbon_fraction |
| `field.soil.nitrogen_cycling.NitrogenCycling` | `field.soil.nitrogen_cycling.leaching_runoff_erosion` | tamaño del campo | `field_size` | ha | daily | escalar | `RUFAS\biophysical\field\soil\nitrogen_cycling\nitrogen_cycling.py:58` | arg |
| `field.soil.nitrogen_cycling.NitrogenCycling` | `field.soil.nitrogen_cycling.nitrification_volatilization` | disparo de nitrificación/volatilización | `do_daily_nitrification_and_volatilization` | unidad no declarada | daily | — | `RUFAS\biophysical\field\soil\nitrogen_cycling\nitrogen_cycling.py:59` | estado: SoilData.soil_layers |
| `field.soil.nitrogen_cycling.NitrogenCycling` | `field.soil.nitrogen_cycling.denitrification` | tamaño del campo | `field_size` | ha | daily | escalar | `RUFAS\biophysical\field\soil\nitrogen_cycling\nitrogen_cycling.py:60` | arg |
| `field.soil.nitrogen_cycling.NitrogenCycling` | `field.soil.nitrogen_cycling.mineralization_decomp` | disparo de mineralización/descomposición | `mineralize_and_decompose_nitrogen` | unidad no declarada | daily | — | `RUFAS\biophysical\field\soil\nitrogen_cycling\nitrogen_cycling.py:61` | estado: SoilData.soil_layers |
| `field.soil.nitrogen_cycling.NitrogenCycling` | `field.soil.nitrogen_cycling.humus_mineralization` | disparo de mineralización de humus | `mineralize_organic_nitrogen` | unidad no declarada | daily | — | `RUFAS\biophysical\field\soil\nitrogen_cycling\nitrogen_cycling.py:62` | estado: SoilData.soil_layers |
| `field.soil.evaporation.Evaporation` | `field.soil (LayerData)` | agua evaporada por capa reseteada | `evaporated_water_content` | unidad no declarada | daily | array (vectorizado por capa) | `RUFAS\biophysical\field\soil\evaporation.py:48` | estado: SoilData.soil_layers[*].evaporated_water_content |
| `field.soil.evaporation.Evaporation` | `field.soil (SoilData)` | agua evaporada del perfil | `water_evaporated` | mm | daily | escalar | `RUFAS\biophysical\field\soil\evaporation.py:76` | estado: SoilData.water_evaporated |
| `field.soil.evaporation.Evaporation` | `field.soil (SoilData)` | evaporación anual acumulada | `annual_soil_evaporation_total` | mm | daily | escalar | `RUFAS\biophysical\field\soil\evaporation.py:77` | estado: SoilData.annual_soil_evaporation_total |
| `field.soil (SoilData)` | `field.field.Field` | agua sublimada descontada de la demanda | `self.soil.data.water_sublimated` | mm | daily | escalar | `RUFAS\biophysical\field\field\field.py:1566` | estado: SoilData.water_sublimated |
| `field.soil (SoilData)` | `field.field.Field` | agua evaporada descontada de la demanda | `self.soil.data.water_evaporated` | mm | daily | escalar | `RUFAS\biophysical\field\field\field.py:1571` | estado: SoilData.water_evaporated |
| `field.soil (LayerData)` | `field.crop.nitrogen_uptake.NitrogenUptake` | nitratos por capa de suelo | `layer_nutrient ("nitrate_content")` | kg/ha | daily | list[float] | `RUFAS\biophysical\field\crop\non_water_uptake.py:101` | arg (vía SoilData.get_vectorized_layer_attribute) |
| `field.soil (SoilData)` | `field.crop.nitrogen_uptake.NitrogenUptake` | factor de agua del suelo para fijación de N | `soil_data.soil_water_factor` | unidad no declarada | daily | escalar | `RUFAS\biophysical\field\crop\nitrogen_uptake.py:128` | estado: SoilData.soil_water_factor |
| `field.soil (LayerData)` | `field.crop.water_uptake.WaterUptake` | profundidades, contenido y capacidad de agua, punto de marchitez por capa | `top_depth, bottom_depth, water_content, available_water_capacity, wilting_point_content` | unidad no declarada | daily | list[float] | `RUFAS\biophysical\field\crop\water_uptake.py:81-85` | arg (vía SoilData.get_vectorized_layer_attribute) |
| `field.soil.carbon_cycling.residue_partition` | `field.soil (SoilData)` | lignina, relación lignina/N y fracción metabólica del residuo | `plant_residue_lignin_composition, plant_lignin_nitrogen_ratio, plant_residue_metabolic_fraction` | unidad no declarada | per-event | escalar | `RUFAS\biophysical\field\soil\carbon_cycling\residue_partition.py:45-55` | estado: SoilData |

##### 2.3.6 Crop — 23 edges

| origen | destino | variable | nombre_codigo | unidad | timestep | tipo | archivo:linea | via_estado |
|---|---|---|---|---|---|---|---|---|
| `field.crop.Crop` | `field.crop (CropData)` | agua retenida en el dosel | `canopy_water` | mm | daily | escalar | `RUFAS\biophysical\field\crop\crop.py:214` | estado: CropData.canopy_water |
| `field.crop.Crop` | `field.field.Field` | agua que llega al suelo tras intercepción | `precipitation_reaching_soil` | mm | daily | escalar | `RUFAS\biophysical\field\crop\crop.py:218` | arg |
| `field.crop (CropData)` | `field.field.Field` | transpiración máxima ponderada por cobertura | `crop.data.max_transpiration, crop.data.field_proportion` | mm / unitless | daily | escalar | `RUFAS\biophysical\field\field\field.py:1545-1546` | estado: CropData |
| `field.crop.Crop` | `field.crop.heat_units.HeatUnits` | temperaturas media/mín/máx del aire | `mean_air_temperature, min_air_temperature, max_air_temperature` | °C | daily | escalar | `RUFAS\biophysical\field\crop\crop.py:146-150` | arg |
| `field.crop.Crop` | `field.crop.nitrogen_uptake.NitrogenUptake` | datos de suelo | `soil_data` | unidad no declarada | daily | dataclass SoilData | `RUFAS\biophysical\field\crop\crop.py:152` | arg |
| `field.crop.nitrogen_uptake.NitrogenUptake` | `field.soil (LayerData)` | nitratos restantes tras absorción radicular | `layer_nutrient escrito con set_vectorized_layer_attribute` | kg/ha | daily | list[float] | `RUFAS\biophysical\field\crop\non_water_uptake.py:133` | estado: SoilData.soil_layers[*].nitrate_content |
| `field.crop.nitrogen_uptake.NitrogenUptake` | `field.crop (CropData)` | nitrógeno almacenado en biomasa | `crop_data.nitrogen` | kg/ha | daily | escalar | `RUFAS\biophysical\field\crop\nitrogen_uptake.py:131-135` | estado: CropData.nitrogen |
| `field.crop.Crop` | `field.crop.phosphorus_uptake.PhosphorusUptake` | datos de suelo | `soil_data` | unidad no declarada | daily | dataclass SoilData | `RUFAS\biophysical\field\crop\crop.py:153` | arg |
| `field.crop.phosphorus_uptake.PhosphorusUptake` | `field.soil (LayerData)` | fósforo lábil restante tras absorción | `layer_nutrient escrito con set_vectorized_layer_attribute` | kg/ha | daily | list[float] | `RUFAS\biophysical\field\crop\non_water_uptake.py:133 (vía phosphorus_uptake.py:71)` | estado: SoilData.soil_layers[*] |
| `field.crop.non_water_uptake.NonWaterUptake` | `field.crop (CropData)` | capas de suelo accesibles a raíces | `total_soil_layers, accessible_soil_layers, inaccessible_soil_layers` | unidad no declarada | daily | escalar | `RUFAS\biophysical\field\crop\non_water_uptake.py:292-296` | estado: CropData |
| `field.crop.Crop` | `field.crop.water_uptake.WaterUptake` | datos de suelo | `soil_data` | unidad no declarada | daily | dataclass SoilData | `RUFAS\biophysical\field\crop\crop.py:183` | arg |
| `field.crop.water_uptake.WaterUptake` | `field.soil (LayerData)` | agua restante por capa tras absorción del cultivo | `water_content` | unidad no declarada | daily | list[float] | `RUFAS\biophysical\field\crop\water_uptake.py:154` | estado: SoilData.soil_layers[*].water_content |
| `field.crop.Crop` | `field.crop (CropData)` | absorción de agua diaria y acumulada reseteadas fuera de temporada | `cumulative_evaporation, cumulative_transpiration, cumulative_potential_evapotranspiration, cumulative_water_uptake` | mm | daily | escalar | `RUFAS\biophysical\field\crop\crop.py:190-193` | estado: CropData |
| `field.crop.Crop` | `field.crop (CropData)` | profundidad radicular máxima limitada por el perfil | `data.max_root_depth` | mm | per-event (siembra) | escalar | `RUFAS\biophysical\field\crop\crop.py:375` | estado: CropData.max_root_depth |
| `field.crop.Crop` | `field.soil.carbon_cycling.residue_partition` | lluvia al entrar en dormancia (añade residuo a pools) | `rainfall` | mm | per-event | escalar | `RUFAS\biophysical\field\crop\crop.py:304` | arg |
| `field.crop.crop_management.CropManagement` | `field.soil (SoilData)` | nitrógeno del residuo de cosecha | `soil_data.crop_yield_nitrogen` | unidad no declarada | per-event | escalar | `RUFAS\biophysical\field\crop\crop_management.py:452` | estado: SoilData.crop_yield_nitrogen |
| `field.crop.crop_management.CropManagement` | `field.soil (SoilData)` | composición de lignina del residuo vegetal | `soil_data.plant_residue_lignin_composition` | unidad no declarada | per-event | escalar | `RUFAS\biophysical\field\crop\crop_management.py:453-455` | estado: SoilData.plant_residue_lignin_composition |
| `field.crop.crop_management.CropManagement` | `field.soil (LayerData)` | residuo vegetal en la capa superficial | `soil_layers[0].plant_residue` | unidad no declarada | per-event | escalar | `RUFAS\biophysical\field\crop\crop_management.py:459` | estado: SoilData.soil_layers[0].plant_residue |
| `field.crop.crop_management.CropManagement` | `field.soil (LayerData)` | nitrógeno orgánico fresco del residuo | `soil_layers[0].fresh_organic_nitrogen_content` | unidad no declarada | per-event | escalar | `RUFAS\biophysical\field\crop\crop_management.py:460` | estado: SoilData.soil_layers[0].fresh_organic_nitrogen_content |
| `field.crop.crop_management.CropManagement` | `field.soil (LayerData)` | fósforo inorgánico lábil del residuo | `soil_layers[0].labile_inorganic_phosphorus_content` | unidad no declarada | per-event | escalar | `RUFAS\biophysical\field\crop\crop_management.py:461` | estado: SoilData.soil_layers[0].labile_inorganic_phosphorus_content |
| `field.crop.crop_management.CropManagement` | `field.soil (LayerData)` | residuo y nutrientes repartidos en profundidad al matar el cultivo | `_distribute_residue_nutrients` | unidad no declarada | per-event | escalar (por capa) | `RUFAS\biophysical\field\crop\crop_management.py:466-493` | estado: SoilData.soil_layers[*] |
| `field.crop.crop_management.CropManagement` | `field (HarvestedCrop)` | cultivo cosechado con masa y calidad | `harvested_crop` | kg (dry_matter_mass), percent (resto) | per-event | dataclass HarvestedCrop | `RUFAS\biophysical\field\crop\crop_management.py:346-362` | arg |
| `field.crop.crop_management.CropManagement` | `OutputManager` | rendimiento de cosecha (dry_yield, crop, harvest_year/day, field_name, harvest_type) | `harvest_yield` | DRY_KILOGRAMS_PER_HECTARE y otros | per-event | dict | `RUFAS\biophysical\field\crop\crop_management.py:365-393` | estado: OutputManager |

##### 2.3.7 Animal — 22 edges

| origen | destino | variable | nombre_codigo | unidad | timestep | tipo | archivo:linea | via_estado |
|---|---|---|---|---|---|---|---|---|
| `animal.HerdManager` | `feed_storage.FeedManager` | alimentos que idealmente deberían comprarse | `ideal_feeds_to_purchase` | kg | daily | dataclass IdealFeeds | `RUFAS\simulation_engine.py:508-513` | arg |
| `animal.HerdManager` | `feed_storage.FeedManager` | ración solicitada tras formulación | `requested_feed` | kg | per-event (intervalo de ración) | dataclass RequestedFeed | `RUFAS\simulation_engine.py:551,558` | arg |
| `animal.HerdManager` | `feed_storage.FeedManager` | petición diaria de alimento del rebaño | `requested_feed` | kg | daily | dataclass RequestedFeed | `RUFAS\simulation_engine.py:581-586` | arg |
| `animal.Animal` | `animal.digestive_system.DigestiveSystem` | entradas digestivas (peso, nutrientes, P, leche) | `digestive_system_inputs` | unidad no declarada | daily | dataclass DigestiveSystemInputs | `RUFAS\biophysical\animal\animal.py:1627-1641` | arg |
| `animal.digestive_system.DigestiveSystem` | `animal.digestive_system.ManureExcretionCalculator` | peso vivo, P fecal y urinario, nutrientes | `body_weight, fecal_phosphorus, urine_phosphorus_required, nutrients` | unidad no declarada | daily | escalar + dataclass | `RUFAS\biophysical\animal\digestive_system\digestive_system.py:84-89 (ternera), 129-134 (novilla), 143-153 (vaca)` | arg |
| `animal.digestive_system.ManureExcretionCalculator` | `animal.digestive_system.DigestiveSystem` | excreciones de estiércol del animal | `manure_excretion (AnimalManureExcretions)` | kg (masas), g (P, K) | daily | dataclass AnimalManureExcretions | `RUFAS\biophysical\animal\digestive_system\digestive_system.py:87,110,137` | estado: DigestiveSystem.manure_excretion |
| `animal.digestive_system.DigestiveSystem` | `animal.Pen` | suma de excreciones de todos los animales del corral | `total_manure_excretion` | kg / g | daily | dataclass AnimalManureExcretions | `RUFAS\biophysical\animal\pen.py:287-290` | estado: Animal.digestive_system.manure_excretion |
| `animal.Pen` | `manure (ManureStream)` | agua del estiércol (masa menos sólidos totales) | `water` | kg | daily | escalar en ManureStream | `RUFAS\biophysical\animal\pen.py:721` | arg |
| `animal.Pen` | `manure (ManureStream)` | nitrógeno amoniacal total | `ammoniacal_nitrogen` | kg | daily | escalar en ManureStream | `RUFAS\biophysical\animal\pen.py:722` | arg |
| `animal.Pen` | `manure (ManureStream)` | nitrógeno total del estiércol | `nitrogen` | kg | daily | escalar en ManureStream | `RUFAS\biophysical\animal\pen.py:723` | arg |
| `animal.Pen` | `manure (ManureStream)` | fósforo del estiércol | `phosphorus` | kg (convertido desde g) | daily | escalar en ManureStream | `RUFAS\biophysical\animal\pen.py:724` | arg |
| `animal.Pen` | `manure (ManureStream)` | potasio del estiércol | `potassium` | kg (convertido desde g) | daily | escalar en ManureStream | `RUFAS\biophysical\animal\pen.py:725` | arg |
| `animal.Pen` | `manure (ManureStream)` | sólidos volátiles degradables y no degradables | `degradable_volatile_solids, non_degradable_volatile_solids` | kg | daily | escalar en ManureStream | `RUFAS\biophysical\animal\pen.py:727-728` | arg |
| `animal.Pen` | `manure (ManureStream)` | sólidos totales | `total_solids` | kg | daily | escalar en ManureStream | `RUFAS\biophysical\animal\pen.py:729` | arg |
| `animal.Pen` | `manure (ManureStream)` | volumen del flujo de estiércol | `volume` | m^3 | daily | escalar en ManureStream | `RUFAS\biophysical\animal\pen.py:730` | arg |
| `animal.Pen` | `manure (ManureStream)` | potencial de producción de metano | `methane_production_potential` | m^3 metano / kg sólidos volátiles | daily | escalar en ManureStream | `RUFAS\biophysical\animal\pen.py:731` | arg |
| `animal.Pen` | `manure (PenManureData)` | nº de animales, superficie de deposición, tipo de corral, masa y N de orina | `PenManureData(...)` | animals / m^2 / kg | daily | dataclass PenManureData | `RUFAS\biophysical\animal\pen.py:711-718` | arg |
| `animal.Pen` | `manure.ManureManager` | primer procesador asignado a cada flujo | `pen_manure_data.first_processor` | unidad no declarada | daily | str | `RUFAS\biophysical\animal\pen.py:654 (general), 767 (parlor)` | estado: ManureStream.pen_manure_data.first_processor |
| `animal.bedding.Bedding` | `manure (ManureStream)` | masa y volumen de cama añadidos al flujo | `total_bedding_mass, total_bedding_volume` | kg / m^3 | daily | escalar en PenManureData | `RUFAS\biophysical\animal\pen.py:874-876` | estado: ManureStream.pen_manure_data (set_bedding_mass_and_volume) |
| `animal.bedding.Bedding` | `manure (ManureStream)` | agua, P, ceniza y sólidos de la cama | `water, phosphorus, ash, total_solids, volume, bedding_non_degradable_volatile_solids` | kg / m^3 | daily | escalar en ManureStream | `RUFAS\biophysical\animal\pen.py:882-901` | arg |
| `animal.Pen` | `animal.HerdManager` | diccionario de flujos de estiércol por corral | `animal_manure_streams` | unidad no declarada | daily | dict[str, ManureStream] | `RUFAS\biophysical\animal\pen.py:659 → herd_manager.py:757` | arg |
| `animal.HerdManager` | `simulation_engine` | todos los flujos de estiércol del rebaño | `herd_manager_output / all_manure_data` | unidad no declarada | daily | dict[str, ManureStream] | `RUFAS\biophysical\animal\herd_manager.py:889 → simulation_engine.py:575` | arg |

##### 2.3.8 Manure — 16 edges

| origen | destino | variable | nombre_codigo | unidad | timestep | tipo | archivo:linea | via_estado |
|---|---|---|---|---|---|---|---|---|
| `manure.ManureManager` | `manure.storage.AnaerobicLagoon / manure.storage.SlurryStorageOutdoor` | parámetros sinusoidales de temperatura | `intercept_mean_temp, phase_shift, amplitude` | unidad no declarada | init | escalar | `RUFAS\biophysical\manure\manure_manager.py:748-750` | estado: Storage.intercept_mean_temp/.phase_shift/.amplitude |
| `manure.ManureManager` | `manure.processor.Processor (primer procesador)` | flujo de estiércol entrante | `stream` | unidad no declarada | daily | dataclass ManureStream | `RUFAS\biophysical\manure\manure_manager.py:125` | arg |
| `manure.ManureManager` | `manure.processor.Processor` | flujo procesado enrutado al destino según matriz de adyacencia | `stream / split_stream` | unidad no declarada | daily | dataclass ManureStream | `RUFAS\biophysical\manure\manure_manager.py:140,142-143` | arg |
| `manure.handler.Handler` | `manure.storage / manure.separator` | flujo de salida con agua de limpieza y N tras emisión de amoníaco | `output_stream` | kg / m^3 | daily | dataclass ManureStream | `RUFAS\biophysical\manure\handler\handler.py:187-201,204` | arg |
| `manure.handler.Handler` | `manure (ManureStream)` | borrado de los datos del corral en el flujo | `pen_manure_data=None` | unidad no declarada | daily | — | `RUFAS\biophysical\manure\handler\handler.py:199` | arg |
| `manure.separator.Separator` | `manure.storage` | fracción sólida separada | `solid_manure_stream` | kg / m^3 | daily | dataclass ManureStream | `RUFAS\biophysical\manure\separator\separator.py:168-185,232` | arg |
| `manure.separator.Separator` | `manure.storage` | fracción líquida separada | `liquid_manure_stream` | kg / m^3 | daily | dataclass ManureStream | `RUFAS\biophysical\manure\separator\separator.py:209-227,232` | arg |
| `manure.storage.Storage` | `manure.storage.Storage` | estiércol recibido acumulado en el almacén | `stored_manure += _received_manure` | kg / m^3 | daily | dataclass ManureStream | `RUFAS\biophysical\manure\storage\storage.py:206` | estado: Storage.stored_manure |
| `manure.storage.Storage` | `manure.ManureManager` | flujo vaciado que pasa al siguiente procesador | `manure_to_be_returned["manure"]` | kg / m^3 | per-event (día de vaciado) | dict[str, ManureStream] | `RUFAS\biophysical\manure\storage\storage.py:219-231` | arg |
| `manure.storage.Storage` | `manure.ManureNutrientManager` | N, P, K, masa y materia seca almacenados | `ManureNutrients(...)` | kg | daily | dataclass ManureNutrients | `RUFAS\biophysical\manure\manure_manager.py:155-164` | arg |
| `manure.ManureNutrientManager` | `manure.ManureNutrientManager` | pools de nutrientes por tipo de estiércol | `nutrients_by_manure_category` | kg | daily | dict[ManureType, ManureNutrients] | `RUFAS\biophysical\manure\manure_nutrient_manager.py:48` | estado: ManureNutrientManager.nutrients_by_manure_category |
| `manure.ManureNutrientManager` | `manure.ManureManager` | resultado de la petición (N, P, masa total, fracciones, materia seca) | `request_result` | kg / unitless | per-event | dataclass NutrientRequestResults | `RUFAS\biophysical\manure\manure_manager.py:891` | arg |
| `manure.ManureManager` | `manure.storage.Storage` | retirada proporcional de nutrientes de cada almacén | `processor.stored_manure` | kg | per-event | dataclass ManureStream | `RUFAS\biophysical\manure\manure_manager.py:951-956` | estado: Storage.stored_manure (reasignado con dataclasses.replace) |
| `manure.FieldManureSupplier` | `manure.ManureManager` | estiércol suplementario externo | `supplemental_manure` | kg | per-event | dataclass NutrientRequestResults | `RUFAS\biophysical\manure\manure_manager.py:903,907` | arg |
| `manure.ManureManager` | `simulation_engine` | resultados de la petición de estiércol | `manure_request_results` | kg | per-event | dataclass NutrientRequestResults | `RUFAS\simulation_engine.py:440,443` | arg |
| `manure (NutrientRequestResults)` | `field.field.Field` | agua del purín líquido aplicada al campo | `water_amount_in_l → water_amount_in_mm` | liters → mm | per-event | escalar | `RUFAS\biophysical\field\field\field.py:948-953` | estado: FieldData.manure_water |

##### 2.3.9 Feed storage — 3 edges

| origen | destino | variable | nombre_codigo | unidad | timestep | tipo | archivo:linea | via_estado |
|---|---|---|---|---|---|---|---|---|
| `feed_storage.FeedManager` | `feed_storage.Storage` | cultivo cosechado asignado a un silo/almacén | `harvested_crop` | unidad no declarada | daily | dataclass HarvestedCrop | `RUFAS\biophysical\feed_storage\feed_manager.py:322 → storage.py:134` | arg |
| `feed_storage.FeedManager` | `animal.HerdManager` | inventario total proyectado de alimentos | `total_projected_inventory` | kg | daily | dataclass TotalInventory | `RUFAS\simulation_engine.py:503,527-529` | arg |
| `feed_storage.FeedManager` | `animal / EEE.EmissionsEstimator` | alimento comprado realmente suministrado | `daily_feeds_fed.purchased` | kg | daily | dataclass FeedFulfillmentResults (dict[RUFAS_ID, float]) | `RUFAS\simulation_engine.py:583-591` | arg |

##### 2.3.10 EEE — 4 edges

| origen | destino | variable | nombre_codigo | unidad | timestep | tipo | archivo:linea | via_estado |
|---|---|---|---|---|---|---|---|---|
| `EEE.EnergyEstimator` | `EEE.Tractor` | tipo de operación de campo, tamaño de tractor, implemento, rendimiento | `FieldOperationEvent, tillage_implement, crop_yield` | unidad no declarada | per-event (post-simulación) | escalar + enum | `RUFAS\EEE\energy.py:150-160` | arg |
| `EEE.EnergyEstimator` | `OutputManager` | consumo de diésel y métricas asociadas | `diesel_consumption, herd_size_for_..., tillage_implement_for_...` | unidad no declarada | annual (post-simulación) | escalar | `RUFAS\EEE\energy.py:174,212-263` | estado: OutputManager |
| `EEE.EmissionsEstimator` | `OutputManager` | emisiones/recursos diarios del forraje propio suministrado | `n2o_emissions_outputs, ammonia_emissions_outputs, fertilizer_N/P/K_outputs, manure_N_outputs` | unidad no declarada | annual (post-simulación) | dict (bulk) | `RUFAS\EEE\emissions.py:901-946` | estado: OutputManager |
| `EEE.EmissionsEstimator` | `OutputManager` | emisiones de alimento comprado y cambio de uso del suelo | `purchased_feed_emissions, land_use_change_emissions` | unidad no declarada | daily | escalar | `RUFAS\EEE\emissions.py:214-215` | estado: OutputManager |

##### 2.3.11 OutputManager (read back) — 13 edges

| origen | destino | variable | nombre_codigo | unidad | timestep | tipo | archivo:linea | via_estado |
|---|---|---|---|---|---|---|---|---|
| `OutputManager` | `EEE.EnergyEstimator` | aplicaciones de fertilizante leídas de vuelta (mass, depth, field_size, clay, year, day, field_name) | `CROP_AND_SOIL_FILTERS[FERTILIZER_APPLICATION]` | unidad no declarada | per-event (post-simulación) | dict | `RUFAS\EEE\energy.py:62-74` | estado: OutputManager (filter_variables_pool, energy.py:288) |
| `OutputManager` | `EEE.EnergyEstimator` | eventos de laboreo leídos de vuelta (tillage_depth, implement, field_size, clay) | `CROP_AND_SOIL_FILTERS[TILLING]` | unidad no declarada | per-event (post-simulación) | dict | `RUFAS\EEE\energy.py:75-87` | estado: OutputManager |
| `OutputManager` | `EEE.EnergyEstimator` | aplicaciones de estiércol leídas de vuelta (dry_matter_mass, dry_matter_fraction, depth) | `CROP_AND_SOIL_FILTERS[MANURE_APPLICATION]` | unidad no declarada | per-event (post-simulación) | dict | `RUFAS\EEE\energy.py:88-101` | estado: OutputManager |
| `OutputManager` | `EEE.EnergyEstimator` | cosechas leídas de vuelta (dry_yield, crop, harvest_year/day, harvest_type) | `CROP_AND_SOIL_FILTERS[HARVEST]` | unidad no declarada | per-event (post-simulación) | dict | `RUFAS\EEE\energy.py:102-114` | estado: OutputManager |
| `OutputManager` | `EEE.EnergyEstimator` | siembras leídas de vuelta (crop, field_size, clay, year, day) | `CROP_AND_SOIL_FILTERS[PLANTING]` | unidad no declarada | per-event (post-simulación) | dict | `RUFAS\EEE\energy.py:115-118` | estado: OutputManager |
| `OutputManager` | `EEE.EmissionsEstimator` | rendimientos de cosecha para emisiones de forraje propio | `FARMGROWN..._FILTERS["harvest_yield"]` | unidad no declarada | annual (post-simulación) | dict | `RUFAS\EEE\emissions.py:13-19 (leído en emissions.py:516)` | estado: OutputManager |
| `OutputManager` | `EEE.EmissionsEstimator` | emisiones de N2O del suelo por campo | `FARMGROWN..._FILTERS["nitrous_oxide_emissions"]` | unidad no declarada | annual (post-simulación) | dict | `RUFAS\EEE\emissions.py:20-27 (leído en emissions.py:319)` | estado: OutputManager |
| `OutputManager` | `EEE.EmissionsEstimator` | emisiones de amoníaco del suelo por campo | `FARMGROWN..._FILTERS["ammonia_emissions"]` | unidad no declarada | annual (post-simulación) | dict | `RUFAS\EEE\emissions.py:28-36` | estado: OutputManager |
| `OutputManager` | `EEE.EmissionsEstimator` | N, P, K de fertilizante aplicado | `FARMGROWN..._FILTERS["fertilizer_applications"]` | unidad no declarada | annual (post-simulación) | dict | `RUFAS\EEE\emissions.py:37-43 (leído en emissions.py:368)` | estado: OutputManager |
| `OutputManager` | `EEE.EmissionsEstimator` | N de estiércol aplicado | `FARMGROWN..._FILTERS["manure_applications"]` | unidad no declarada | annual (post-simulación) | dict | `RUFAS\EEE\emissions.py:44-50` | estado: OutputManager |
| `OutputManager` | `EEE.EmissionsEstimator` | mapeo cultivo→ID de alimento (crop_received) | `FARMGROWN..._FILTERS["crop_received"]` | unidad no declarada | annual (post-simulación) | dict | `RUFAS\EEE\emissions.py:51-60 (leído en emissions.py:467)` | estado: OutputManager |
| `OutputManager` | `EEE.EmissionsEstimator` | deducciones de forraje propio suministrado a animales | `FARMGROWN..._FILTERS["farmgrown_feed_deductions"]` | unidad no declarada | annual (post-simulación) | dict | `RUFAS\EEE\emissions.py:61-67 (leído en emissions.py:436)` | estado: OutputManager |
| `OutputManager` | `EEE.EmissionsEstimator` | inventario diario de forraje propio | `FARMGROWN..._FILTERS["farmgrown_feed_inventory"]` | unidad no declarada | annual (post-simulación) | dict | `RUFAS\EEE\emissions.py:68-72 (leído en emissions.py:758)` | estado: OutputManager |

##### 2.3.12 Simulation engine — 7 edges

| origen | destino | variable | nombre_codigo | unidad | timestep | tipo | archivo:linea | via_estado |
|---|---|---|---|---|---|---|---|---|
| `simulation_engine` | `feed_storage.FeedManager` | cultivo cosechado a almacenar | `crop, simulation_day` | unidad no declarada | daily | dataclass HarvestedCrop | `RUFAS\simulation_engine.py:449` | arg |
| `simulation_engine` | `feed_storage.FeedManager` | calendario de cosechas traducido a IDs RuFaS | `next_harvest_dates_with_rufas_ids` | unidad no declarada | daily | dict[RUFAS_ID, date] | `RUFAS\simulation_engine.py:506` | arg |
| `simulation_engine` | `EEE.EmissionsEstimator` | alimento comprado del día para emisiones | `daily_purchased_feeds_fed` | kg | daily | dict[int, float] | `RUFAS\simulation_engine.py:626` | arg |
| `simulation_engine` | `manure.ManureManager` | flujos de estiércol diarios + condiciones del día | `daily_manure_data, current_day_conditions` | unidad no declarada | daily | dict[str, ManureStream] + CurrentDayConditions | `RUFAS\simulation_engine.py:611-613` | arg |
| `simulation_engine` | `manure.ManureManager` | petición de nutrientes (ruta con módulo de estiércol activo) | `manure_request` | kg | per-event | dataclass NutrientRequest | `RUFAS\simulation_engine.py:440` | arg — AMBIGÜEDAD: ver siguiente línea |
| `simulation_engine` | `manure.FieldManureSupplier` | petición de nutrientes (ruta sin módulo de estiércol) | `manure_request` | kg | per-event | dataclass NutrientRequest | `RUFAS\simulation_engine.py:442` | arg — AMBIGÜEDAD: ruta alternativa según simulate_manure |
| `simulation_engine` | `field.manager.FieldManager` | aplicaciones de estiércol por campo | `manure_applications` | unidad no declarada | daily | list[ManureEventNutrientRequestResults] | `RUFAS\simulation_engine.py:416-418` | arg |

### 2.4 Aliasing edges — receivers that mutate shared objects in place

These are data-flow edges with **no return value and no assignment at the call site**. A module
receives an object as an argument and writes into it; the change is visible to every other holder of
that object. For a figure, these are the arrows that make the field subsystem a single mutable blob
rather than a pipeline.

- `Weather.get_current_day_conditions` writes `daylength` and `annual_mean_air_temperature` directly
  into the **cached** `CurrentDayConditions`. The same instance is reused and overwritten for every
  field, so a field with a different latitude overwrites the previous field's daylength —
  `RUFAS/weather.py:177-178` (and `:219-220` in `get_conditions_series`).
- `SoilData` is shared between `Soil`, all nine soil submodules, `ManureApplication`,
  `FertilizerApplication`, `TillageApplication` and the crop submodules: `Soil.__init__` hands
  `self.data` to the nine processes (`RUFAS/biophysical/field/soil/soil.py:57-66`); `Field` hands
  `self.soil.data` to `TillageApplication` and `ManureApplication`
  (`RUFAS/biophysical/field/field/field.py:135,139`).
- `NonWaterUptake.extract_nutrient_from_soil_layers` mutates the nutrient list by slice assignment
  (`layer_nutrients[:] = ...`) at `RUFAS/biophysical/field/crop/non_water_uptake.py:517`, then writes
  it back with `set_vectorized_layer_attribute` at `:133`.
- `WaterUptake.uptake` rewrites `water_content` of every layer —
  `RUFAS/biophysical/field/crop/water_uptake.py:154`.
- `CropManagement._transfer_residue` writes fields of the `SoilData` and of `SoilData.soil_layers[0]`
  it received as an argument — `RUFAS/biophysical/field/crop/crop_management.py:452-461`.
- `Field._add_manure_water` accumulates into `FieldData.manure_water`; `Field._get_manure_water`
  zeroes it — `RUFAS/biophysical/field/field/field.py:953` and `:1656`.
- `Field._reset_crop_field_coverage_fractions` writes `crop.data.field_proportion` from outside
  `Crop` — `RUFAS/biophysical/field/field/field.py:1411`.
- `Field._plant_crop` → `crop.update_crop_max_root_depth` mutates `CropData.max_root_depth` —
  `RUFAS/biophysical/field/crop/crop.py:375`.
- `Snow.update_snow` / `Snow.sublimate` mutate `SoilData.snow_content`, `.snow_melt_amount`,
  `.water_sublimated` — `RUFAS/biophysical/field/soil/snow.py:183,199,200,217,218`.
- `SoilTemp.daily_soil_temperature_update` mutates `layer.temperature` and
  `layer.previous_day_temperature` of every `LayerData` —
  `RUFAS/biophysical/field/soil/soil_temp.py:91,98`.
- `Pen._apply_bedding` mutates the `PenManureData` of the received `ManureStream`
  (`set_bedding_mass_and_volume`) before returning a new stream —
  `RUFAS/biophysical/animal/pen.py:874-876`.
- `Pen.get_manure_streams` mutates `pen_manure_data.first_processor` on an already-created stream —
  `RUFAS/biophysical/animal/pen.py:654` and `:767`.
- `SlurryStorageOutdoor.process_manure` mutates `self._received_manure.volume` and `.water` with the
  day's precipitation before processing —
  `RUFAS/biophysical/manure/storage/slurry_storage_outdoor.py:59-60` (equivalent in `AnaerobicLagoon`
  at `anaerobic_lagoon.py:75-76`).
- `Storage.process_manure` accumulates with `+=` onto `self.stored_manure` —
  `RUFAS/biophysical/manure/storage/storage.py:206`.
- `ManureManager._remove_nutrients_from_storage` reassigns `processor.stored_manure` of every store
  (via `dataclasses.replace` — not in-place mutation, but still a write into another object's state)
  — `RUFAS/biophysical/manure/manure_manager.py:951-956`.
- `OpenLot.process_manure` reassigns `self._received_manure` with the already-processed stream —
  `RUFAS/biophysical/manure/storage/open_lot.py:73`.
- `HarvestedCrop.remove_dry_matter_mass` / `remove_feed_mass` mutate the harvested object that the
  feed module holds — `RUFAS/data_structures/crop_soil_to_feed_storage_connection.py:145,179`.

### 2.5 Edges looked for and NOT FOUND IN CODE

- **No grazing-manure animal→field edge on the daily path.**
  `ManureApplication.apply_grazing_manure` exists
  (`RUFAS/biophysical/field/field/manure_application.py:53`) but no call to it was found from the
  animal module or from `Field`. The `grazing_manure` pool is nevertheless read by
  `phosphorus_cycling/manure.py:56-60` and written by `TillageApplication`
  (`tillage_application.py:115-131`) — so the pool is cycled, but the edge that fills it from grazing
  animals was not located.
- `Soil.daily_soil_routine` and `Soil.daily_soil_water_routine`
  (`RUFAS/biophysical/field/soil/soil.py:68,109`) are **not invoked by `Field`**; `Field` calls the
  submodules directly (`field.py:1448-1539`). Flagged as dead path / ambiguity — see §3.4 and §9.
- `SimulationEngine.annual_mass_balance` is empty (`pass`) — `RUFAS/simulation_engine.py:663-664`.
  It transfers no value; there is no mass-balance closure edge.
- No read of `OutputManager` by any biophysical module (field, soil, crop, animal, manure). EEE is
  the only consumer that reads the pool back.

---

## 3. Orchestration

### 3.1 One daily step, FULL_FARM

Entry: `simulate()` `simulation_engine.py:282` → `_run_simulation_main_loop` `:314` →
`_annual_simulation` `:647` → day loop `:651-652` → `_execute_full_farm_daily_simulation` `:322`.

1. **`_execute_daily_field_operations`** — `simulation_engine.py:337`
   - `_generate_daily_manure_applications` `:415` → per field `field_manager.check_manure_schedules`
     `:432` (→ `field.check_manure_application_schedule` `field_manager.py:643`) →
     `manure_manager.request_nutrients` `:440` (`manure_manager.py:859`) **or**
     `FieldManureSupplier.request_nutrients` `:442` — **two routes, selected by `simulate_manure`;
     both reported, neither chosen.**
   - `field_manager.daily_update_routine` `:416` → per field (`field_manager.py:93`):
     `weather.get_current_day_conditions` `:94`, `field.manage_field` `:105`; finally
     `output_gatherer.send_daily_variables` `:109`.
2. **Inside `Field.manage_field`** (`field.py:143`): `_check_fertilizer_application_schedule` `:175`
   → `_execute_manure_application` per event `:180` → `_check_tillage_schedule` `:193` →
   `_execute_daily_processes` `:197` → `_assess_dormancy` `:201` → `_check_crop_planting_schedule`
   `:203` → `_check_crop_harvest_schedule` `:205` → `_remove_dead_crops` `:207` →
   `_reset_crop_field_coverage_fractions` `:208`.
3. **`_execute_daily_processes`** (`field.py:1432`): `soil.snow.update_snow` `:1448` →
   `soil.soil_temp.daily_soil_temperature_update` `:1451` → `_cycle_water` `:1461` → per crop
   `crop.perform_daily_crop_update` `:1464`.
4. **`_cycle_water`** (`field.py:1466`) — the real hydrological order:
   `percolate` `:1518` → `infiltrate` `:1519` → `percolate_infiltrated_water` `:1520` →
   `soil_erosion.erode` `:1522` → `phosphorus_cycling.cycle_phosphorus` `:1528` →
   `carbon_cycling.cycle_carbon` `:1534` → `nitrogen_cycling.cycle_nitrogen` `:1539` → per crop
   `set_maximum_transpiration` `:1544` → `snow.sublimate` `:1565` → `evaporation.evaporate` `:1570`
   → per crop `cycle_water_for_crop` `:1576`.
   - **P**: `manure.daily_manure_update` → `fertilizer.do_fertilizer_phosphorus_operations` →
     `mineralization.mineralize_phosphorus` → `soluble_phosphorus.daily_update_routine`
     (`phosphorus_cycling.py:65-68`).
   - **C**: `decomposition.decompose` → `residue_partition.partition_residue` →
     `pool_gas_partition.partition_pool_gas` → `_soil_carbon_aggregation` (`carbon_cycle.py:61-64`).
   - **N**: `leach_runoff_and_erode_nitrogen` → `do_daily_nitrification_and_volatilization` →
     `denitrify` → `mineralize_and_decompose_nitrogen` → `mineralize_organic_nitrogen`
     (`nitrogen_cycling.py:58-62`).
5. `_receive_daily_harvested_crops` `:339` → `feed_manager.receive_crop` `:449` (`feed_manager.py:302`).
6. `_build_harvest_schedule` `:340` → `field_manager.get_next_harvest_dates` `:482`.
7. **`_execute_feed_planning`** `:342`: `get_total_projected_inventory` `:503`,
   `_update_all_max_daily_feeds` `:511` → `herd_manager.update_all_max_daily_feeds` `:527`
   (`herd_manager.py:1660`), `manage_planning_cycle_purchases` `:513`, reports `:514-515`,
   conditional `process_degradations` `:519` (`feed_manager.py:336`).
8. **`_execute_ration_planning`** `:344`: if due (`:538`) → `_formulate_ration` `:540` →
   `herd_manager.formulate_rations` `:551` (`herd_manager.py:1718`),
   `feed_manager.manage_ration_interval_purchases` `:558`; then
   `update_herd_305_day_milk_yields` `:541`.
9. **`_execute_daily_animal_operations`** `:346`: `herd_manager.execute_daily_routines` `:575`
   (`herd_manager.py:807`) → `_reset_daily_statistics` `:847` → `_process_daily_herd_updates` `:850`
   (`:678`; 9 groups `:681-692`, `_perform_daily_routines_for_animals` `:701` / def `:583` →
   `Animal.daily_routines` `animal.py:1871`: nutrients `:1896`, digestive `:1898`, milk `:1900`,
   growth `:1902`, reproduction `:1904`, life stage `:1906`) → `_update_sold_animal_statistics`
   `:857` → `_apply_daily_herd_structure_updates` `:864` → `record_pen_history` `:873` →
   `_collect_manure_outputs_by_pen` `:874` (`:747`) → `update_herd_statistics` `:880` →
   `_report_daily_routine_outputs` `:883`. Then `collect_daily_feed_request` `:581` and
   `feed_manager.manage_daily_feed_request` `:583`.
10. **`_execute_daily_manure_operations`** `:348` → `manure_manager.run_daily_update` `:611`
    (`manure_manager.py:91`): dispatch to each stream's first processor `:111-125`, then topological
    order `:127-143` (`process_manure` `:129`, `receive_manure` / `split_stream` `:140-143`),
    `reset_nutrient_pools` `:145`, `_build_nutrient_pools` `:146`.
11. `_report_daily_records` `:350`: `calculate_purchased_feed_emissions` `:626`, `time.record_time()`
    `:627`, `weather.record_weather` `:628`.
12. `_advance_time` `:352` → `time.advance()` `rufas_time.py:30`.

**Year end:** `_run_post_annual_routines` `:637` → `annual_mass_balance` `:644` (**empty body**,
`:663-664`) and `annual_reset` `:645` → `field_manager.annual_update_routine` `:661`.

### 3.2 Repeated and nested calls

- **Per field**: `field_manager.py:93` and `simulation_engine.py:431`.
- **Per crop**: `field.py:1463`, `:1543`, `:1575` — three passes per day.
- **Per soil layer**: 18 `for layer in ...soil_layers` loops, e.g. `carbon_cycle.py:77`,
  `decomposition.py:46`, `pool_gas_partition.py:128`, `residue_partition.py:118,183`,
  `evaporation.py:49`, `denitrification.py:57`, `humus_mineralization.py:48`,
  `leaching_runoff_erosion.py:175`, `nitrification_volatilization.py:51`,
  `phosphorus_mineralization.py:52`, `soil_temp.py:86`.
- **Two manure pools per day**: `machine_manure` and `grazing_manure`
  (`phosphorus_cycling/manure.py:56-60`).
- **Per pen / per processor**: `manure_manager.py:111` and `:127`. **Per animal group**:
  `herd_manager.py:694`.
- **`_formulate_ration` can run twice in the same day**: `simulation_engine.py:540` and again `:596`
  if feed is insufficient.

### 3.3 Iteration to convergence

No *numerical convergence* loop is declared anywhere. What exists is **retry until feasible**:

- `pen.py:1083` `while True` — ration reformulation with retries (`_attempt_formulation` `:1085`,
  exit `:1109`).
- `pen.py:1353` `while ration_sufficient_for_milk_production` — reduces milk production until the
  ration is adequate or `MINIMUM_AVG_PEN_MILK` is reached (`:1358`).
- `herd_manager.py:985` and `:1028` — herd-size adjustment.
- `manure_manager.py:393` `while heap` — Kahn topological sort, not convergence.

### 3.4 Ambiguity: two orderings exist for the soil routine

`Soil.daily_soil_routine` (`soil.py:68`) and `Soil.daily_soil_water_routine` (`soil.py:109`) define a
**different order** from the one that actually runs — evaporation before erosion, and P→N→C at
`soil.py:156-160`, versus erosion before evaporation and P→C→N at `field.py:1522-1539`.

Neither `Soil` method has any caller outside `soil.py` and the test suite (grep over the whole repo).
The effective production order is `field.py:1518-1576`. **Both paths are reported; neither is
chosen.** This matters beyond bookkeeping: it is the site of Bug 1 (§10.1).

### 3.5 Parallelism

**None found.** A grep for `thread|multiprocessing|asyncio|concurrent.futures|ThreadPool|Pool(` over
`RUFAS/` returns only false positives ("nutrient pool", "variables_pool") and one comment at
`graph_generator.py:146` ("This class is not multi-thread safe!!!"). Execution is entirely
sequential.

### 3.6 Persistent vs recomputed state

**Persistent across days** (mutated in place, never reinitialised daily):

- `SoilData` (`soil_data.py:13`): profile contents and `soil_layers`; `initial_water_content`,
  `initial_nitrates_total` (`:428-429`); annual accumulators `annual_soil_evaporation_total`,
  `annual_runoff_total`, `annual_eroded_sediment_total`, `annual_surface_runoff_total`,
  `annual_runoff_*_phosphorus`, `annual_runoff_nitrates_total`, `annual_eroded_*_nitrogen_total`
  (`:433-454`).
- `LayerData` (`layer_data.py:10`): C pools (`active/slow/passive_carbon_amount`, used at
  `carbon_cycle.py:80-95`), N and P pools (`add_to_labile_phosphorus` `:614`,
  `add_to_active_phosphorus` `:631`), `plant_residue` (`field.py:1558`); annual
  `annual_carbon_CO2_lost`, `annual_decomposition_carbon_CO2_lost`,
  `annual_nitrous_oxide_emissions_total`, `annual_volatilized_ammonium_total` (`:1019-1023`).
- `ManurePool` (`manure_pool.py:47-59`): `manure_dry_mass`, `manure_applied_mass`,
  `manure_field_coverage`, `manure_moisture_factor`, stable/extractable P pools, and annual
  `annual_runoff_manure_*_phosphorus`, `annual_decomposed_manure`.
- `CropData` (`crop_data.py:43`): `accumulated_heat_units` (`:283`), `cumulative_evaporation` `:313`,
  `cumulative_transpiration` `:314`, `cumulative_potential_evapotranspiration` `:315`,
  `cumulative_water_uptake` `:323`.
- `FieldData`: `annual_irrigation_water_use_total` (`field_data.py:146`).
- `Storage.stored_manure` (`manure/storage/storage.py:84`, accumulates `:206`, empties per schedule
  `:209-231`).
- `Animal.days_born` (`animal.py:1889`), `days_in_pregnancy` (`:1914`); `HerdManager` lists
  (`calves`, `heiferIs…`, `cows`, `herd_manager.py:682-691`).
- Engine cursors: `next_max_daily_feed_recalculation` (`simulation_engine.py:238`),
  `next_degradations_processing` (`:240`), `next_ration_reformulation` (`:246`).

**Reset every day:**

- `ManurePool.runoff_reset()` for both pools (`phosphorus_cycling/manure.py:56-57`; def
  `manure_pool.py:208`).
- `ManureNutrientManager.reset_nutrient_pools()` + `_build_nutrient_pools()`
  (`manure_manager.py:145-146`; def `manure_nutrient_manager.py:22`).
- `Processor._received_manure` emptied after being added (`storage.py:207`).
- `HerdManager._reset_daily_statistics()` and
  `herd_reproduction_statistics = HerdReproductionStatistics()` (`herd_manager.py:847-848`).
- `Field._reset_crop_field_coverage_fractions()` (`field.py:208` / def `:1401`);
  `field_data.max_evapotranspiration` reassigned (`field.py:1514`).
- `CurrentDayConditions` rebuilt per field per day (`field_manager.py:94`) — but see the aliasing
  caveat in §2.4.

**Annual reset:** `SimulationEngine.annual_reset` `:656` → `FieldManager.annual_update_routine`
`:113` → `Field.perform_annual_reset` `:1894` → `SoilData.do_annual_reset` `:426` (→
`LayerData.do_annual_reset` `:1015` per layer, `soil_data.py:457-458`) and
`FieldData.perform_annual_field_reset` `:144`.

**Gap:** no annual reset is invoked for the **animal, manure or feed-storage** modules —
`simulation_engine.py:656-661` covers fields only. Reported as found, not diagnosed.

---
## 4. Contracts and interfaces

### 4.1 Entry-point signatures (verbatim)

| Module | Signature | `file:line` |
|---|---|---|
| Soil (non-water) | `daily_soil_routine(self, solar_radiation: float, avg_temp: float, min_temp: float, max_temp: float, plant_cover: float, snow_cover: float, avg_annual_air_temp: float) -> None` | `soil/soil.py:68` |
| Soil (water) | `daily_soil_water_routine(self, rainfall, weighting_coefficient, potential_evapotranspiration, has_seasonal_high_water_table, maximum_soil_evaporation, avg_air_temp, residue, minimum_cover_management_factor, field_size) -> None` | `soil/soil.py:109` |
| Crop | `perform_daily_crop_update(self, current_conditions: CurrentDayConditions, field_data: FieldData, soil_data: SoilData, time: RufasTime) -> None` | `field/crop/crop.py:127` |
| Field (daily internal) | `_execute_daily_processes(self, current_conditions: CurrentDayConditions, time: RufasTime) -> None` | `field/field/field.py:1432` |
| FieldManager | `daily_update_routine(self, weather: Weather, time: RufasTime, manure_applications: list[ManureEventNutrientRequestResults]) -> list[HarvestedCrop]` | `field/manager/field_manager.py:65` |
| FieldManager (annual) | `annual_update_routine(self) -> None` | `field/manager/field_manager.py:113` |
| ManureManager | `run_daily_update(self, manure_streams: dict[str, ManureStream], time: RufasTime, current_day_conditions: CurrentDayConditions) -> None` | `manure/manure_manager.py:91` |
| ManureManager | `request_nutrients(self, request: NutrientRequest, time: RufasTime) -> NutrientRequestResults` | `manure/manure_manager.py:859` |
| Processor (abstract) | `receive_manure(self, manure: ManureStream) -> None` | `manure/processor.py:54` |
| Processor (abstract) | `process_manure(self, conditions: CurrentDayConditions, time: RufasTime) -> dict[str, ManureStream]` | `manure/processor.py:72` |
| Storage (manure) | `receive_manure(...)` / `process_manure(self, _: CurrentDayConditions, time: RufasTime) -> dict[str, ManureStream]` | `manure/storage/storage.py:179` / `:202` |
| HerdManager | `execute_daily_routines(self, available_feeds: list[Feed], time: RufasTime, weather: Weather) -> dict[str, ManureStream]` | `animal/herd_manager.py:807` |
| FeedManager | `manage_daily_feed_request(self, requested_feed: RequestedFeed, time: RufasTime) -> tuple[bool, FeedFulfillmentResults]` | `feed_storage/feed_manager.py:436` |
| EEE | `EEEManager.estimate_all() -> None` (static) | `EEE/EEE_manager.py:11` |
| EEE | `EmissionsEstimator.estimate_farmgrown_feed_emissions(self) -> None` | `EEE/emissions.py:261` |
| EEE | `EmissionsEstimator.calculate_purchased_feed_emissions(self, purchased_feeds: dict[int, float]) -> None` | `EEE/emissions.py:178` |
| EEE | `EnergyEstimator.estimate_all() -> None` (static) | `EEE/energy.py:132` |

Orchestration call sites: `simulation_engine.py:413` `_execute_daily_field_operations`, `:563`
`_execute_daily_animal_operations`, `:600` `_execute_daily_manure_operations`, `:637`
`_run_post_annual_routines`.

### 4.2 Contract dataclasses — and which ones consumers mutate

The `Mutated by consumers?` column is the one that matters for a figure: a `frozen=True` contract is
a real interface; a mutable one is a shared blackboard.

| Class | `file:line` | Purpose | Mutated by consumers? |
|---|---|---|---|
| `StreamType` (Enum) | `animal_to_manure_connection.py:9` | Manure stream category | n/a |
| `PenManureData` | `animal_to_manure_connection.py:26` | Pen context for a stream (`num_animals`, deposition area m², urine mass/N kg, `first_processor`). Unit map at `:64` | Mutable dataclass; combine logic `:114-118`. Whether manure processors mutate it: **NOT FOUND IN CODE** (not exhaustively traced) |
| `ManureStream` | `animal_to_manure_connection.py:135` | Animal→Manure and processor→processor payload (water, N, NH4-N, P, K, ash, VS, TS in kg; volume m³). Unit map `:189` | **Yes** — e.g. `self._received_manure.water += …` at `manure/storage/anaerobic_lagoon.py:76` and `slurry_storage_outdoor.py:60` |
| `NutrientRequest` | `manure_to_crop_soil_connection.py:42` | Crop/Soil→Manure ask (N kg, P kg, `ManureType`, supplemental flag) | **No** — `frozen=True` |
| `NutrientRequestResults` | `manure_to_crop_soil_connection.py:86` | Manure→Crop/Soil answer (N, P, total mass, dry matter kg + organic/inorganic/ammonium fractions) | **No** — `frozen=True`; combined via `__add__` `:159` |
| `ManureEventNutrientRequest` / `…Results` | `:247` / `:255` | NamedTuple pairing (field_name, event, request/results) | No (NamedTuple) |
| `FieldManureSupplier` | `:263` | Fallback supplier when the manure module is off (`simulation_engine.py:440`) | n/a |
| `ManureNutrients` | `manure_nutrients.py:11` | Accumulated nutrients with an explicit per-field `*_unit: MeasurementUnits` | **No** — `frozen=True` |
| `BaseFieldManagementEvent` | `events.py:10` | (year, day) scheduling base | Mutable plain class |
| `PlantingEvent` / `HarvestEvent` / `TillageEvent` / `ManureEvent` / `FertilizerEvent` | `events.py:74 / 120 / 170 / 237 / 334` | Scheduled field operations | Mutable plain classes |
| `HarvestedCrop` | `crop_soil_to_feed_storage_connection.py:12` | Field→FeedStorage payload (dry_matter_mass kg, DM %, digestibility, CP %) | **Yes** — `last_time_degraded` is explicitly re-set over time (`:26-28`) |
| `Feed` / `NASEMFeed` / `NRCFeed` / `RequestedFeed` / `FeedFulfillmentResults` | `feed_storage_to_animal_connection.py:59 / 179 / 365 / 501 / 538` | FeedStorage↔Animal contracts | Mutable dataclasses |
| `SoilData` | `soil/soil_data.py:13` | Whole-profile state incl. `soil_layers: list[LayerData]`; `field_size` is an `InitVar` (`:168`) | **Yes, heavily** — handed to `Crop.perform_daily_crop_update` and mutated by `NitrogenUptake.uptake(soil_data)` (`crop/nitrogen_uptake.py:106`) |
| `LayerData` | `soil/layer_data.py:10` | One soil layer; `field_size`, `residue` are `InitVar` | **Yes** — `add_to_labile_phosphorus` `:614`, `add_to_active_phosphorus` `:631` |
| `CropData` | `crop/crop_data.py:43` | SWAT-derived crop parameters + live state | **Yes** (mutable `kw_only` dataclass) |
| `FieldData` | `field/field_data.py:9` | Field state: latitude, `field_size` (ha, `:81`), residue, transpiration, ET | **Yes** — e.g. `self.field_data.max_evapotranspiration = …` at `field/field.py:1512` |
| `CurrentDayConditions` | `current_day_conditions.py:10` | Per-day weather bundle handed to Field/Crop/Soil/Manure | **Yes** — `Weather.get_current_day_conditions` writes `daylength` and `annual_mean_air_temperature` onto the *stored* object (`weather.py:177-178`, `:219-220`). The same instance is reused per date, so the mutation leaks across callers |

### 4.3 Where inputs are validated

| Site | `file:line` | Checks |
|---|---|---|
| `PenManureData.__post_init__` | `animal_to_manure_connection.py:78-80` | PARLOR stream must come from a LAC_COW pen → `ValueError` |
| `PenManureData` combine | `:114`, `:116`, `:118` | no general stream type; same animal combination; same `first_processor` |
| `ManureStream` split | `:349` | split ratio strictly in (0, 1) |
| `NutrientRequest.__post_init__` | `manure_to_crop_soil_connection.py:57-82` | all numeric fields ≥ 0; `manure_type` is a `ManureType`; at least one nutrient > 0 |
| `NutrientRequestResults.__post_init__` | `:120-157` | fractions in [0, 1]; non-fractions ≥ 0; organic + inorganic N fractions == 1 (`isclose`, abs_tol 1e-6); same for P |
| `ManureNutrients.__post_init__` | `manure_nutrients.py:44-64`; operators `:165, :205, :208, :244, :258` | type is `ManureType`, values non-negative; type guards on `__add__`/`__mul__`/`__sub__`; no negative scalar or result |
| `HarvestedCrop.__post_init__` | `crop_soil_to_feed_storage_connection.py:94`, raise `:174` | field consistency |
| `RequestedFeed.__mul__` | `feed_storage_to_animal_connection.py:528` | scalar must be int/float |
| `SoilData.__post_init__` | `soil_data.py:271`, errors `:295-308` | `field_size` not None (`TypeError`), `field_size > 0` (`ValueError`); both also logged via `OutputManager().add_error` |
| `Weather.check_adequate_weather_data` | `weather.py:309`, `add_error` `:342`, `raise` `:347` | every simulated date exists in the weather file |
| `Weather.__init__` duplicate check | `weather.py:87` | duplicate date → `add_warning` |
| `ManureManager.run_daily_update` | `manure_manager.py:117-124` | unknown `first_processor` → `add_error` + `KeyError` |
| `InputManager._validate_data` | `input_manager.py:1562` → `DataValidator.validate_data_by_type` (`data_validator.py:803`) | per-property type/range validation against the metadata schema |
| `InputManager` metadata validation | `input_manager.py:214, 236, 408, 1328, 1850` | required file blobs, runtime metadata, property existence, primitive types |
| `InputManager._cross_validate_data` | `input_manager.py:165` | runs the declarative cross-validation JSONs |
| `DataValidator` domain checks | `data_validator.py:1801`, `:1813` | beef breeding-season start day; beef weaning weight |
| Field application depth | `field/field/field.py:684` `_validate_application_depth_and_fraction` | depth / surface-remainder fraction sanity |

Note: `data_validator.py` contains **zero** literal `add_error(` calls (`grep -c` = 0); errors surface
elsewhere (`output_manager.py:637`).

### 4.4 Is there a central configuration schema?

**Yes — in three layers.**

1. **Property schema (the real schema)**: `input/metadata/properties/default.json` (203,962 bytes) —
   per-blob property definitions with `description`, `type`, `minimum`/`maximum`, `default`. Example:
   `weather_properties` at `input/metadata/properties/default.json:5978`.
2. **Manifest metadata**: e.g. `input/metadata/example_field_only_metadata.json:1` — maps logical
   names → `path`, `type` (json/csv), `properties` (which schema blob validates it).
3. **Cross-validation rules**: `input/metadata/cross_validation/*.json`, e.g.
   `weather_cross_validation.json:1` (high/low/avg arrays must be equal length).

Loader: `RUFAS/input_manager.py:60` `InputManager` (singleton `__new__` `:67`),
`start_data_processing` `:106`, `_load_properties` `:639`, `_load_cross_validation` `:575`,
`_load_data_from_json` `:691`, `_load_data_from_csv` `:735`.

Read example: `nutrient_standard = NutrientStandard(self.im.get_data("config.nutrient_standard"))` —
`simulation_engine.py:218`; `get_data` at `input_manager.py:1021` (dotted address into the validated
pool). Also `county_code = self.im.get_data("config.FIPS_county_code")` — `EEE/emissions.py:105`.

Code-level constants, **not** user config: `general_constants.py:4`, `user_constants.py:5`, units enum
`units.py:6`.

---

## 5. Boundary transformations

### 5.1 Unit conversions with factor and constant name

| Conversion | Factor | Constant | Declared | Used at |
|---|---|---|---|---|
| mm → m | 0.001 | `MM_TO_M` | `general_constants.py:98` | `manure/storage/anaerobic_lagoon.py:74`, `slurry_storage_outdoor.py:58` (precip mm → m × area m² → m³) |
| g → kg | 0.001 | `GRAMS_TO_KG` | `:105` | `animal/digestive_system/manure_excretion_calculator.py:143, 264, 272, 487, 489, 670, 678` |
| kg → g | 1000 | `KG_TO_GRAMS` | `:106` | same file `:261, 269, 276, 484, 511, 667, 682`; `animal_module_reporter.py:249` |
| kg → mg | 1e6 | `KG_TO_MILLIGRAMS` | `:107` | `soil/layer_data.py:751` |
| mg → kg | 1e-6 | `MILLIGRAMS_TO_KG` | `:108` | `soil/layer_data.py:786` |
| Mg → kg | 1000 | `MEGAGRAMS_TO_KILOGRAMS` | `:109` | `soil/layer_data.py:597, 749, 785` (bulk density Mg/m³ → kg) |
| % → fraction | 0.01 | `PERCENTAGE_TO_FRACTION` | `:138` | `digestive_system/enteric_methane_calculator.py:152`; `manure_excretion_calculator.py:142, 263, 284, 645, 677` |
| L → m³ | 0.001 | `LITERS_TO_CUBIC_METERS` | `:113` | `manure/handler/handler.py:318` |
| L → mm³ | 1e6 | `LITERS_TO_CUBIC_MILLIMETERS` | `:116` | `field/field_data.py:165`; inverse at `soil/phosphorus_cycling/fertilizer.py:224, 238` |
| ha → mm² | 1e10 | `HECTARES_TO_SQUARE_MILLIMETERS` | `:144` | `field_data.py:166`; `layer_data.py:595, 747, 783`; `manure_pool.py:589, 766`; `carbon_cycle.py:141`; `soluble_phosphorus.py:137, 256`; `fertilizer.py:223, 237` |
| cm² → ha | 1e-8 | `SQUARE_CENTIMETERS_TO_HECTARES` | `:143` | `field/manure_application.py:489` (grazing patch → ha) |
| mm³ → m³ | 1e-9 | `CUBIC_MILLIMETERS_TO_CUBIC_METERS` | `:119` | `layer_data.py:598, 748, 784` |
| kcal → MJ | 4.184 | `KCAL_TO_MJ` | `:128` | call sites not enumerated |
| °C → K | 273.15 | `CELSIUS_TO_KELVIN` | `:135` | — |
| Manure DM→wet, N→DM, P→DM | 21.739 / 20.909 / 51.111 (liquid); 2.469 / 67.516 / 135.033 (solid) | `LIQUID_MANURE_DRY_MASS_TO_WET_MASS` etc. | `manure_to_crop_soil_connection.py:8-24`, mapped `:27` | manure request sizing |

**Two dimensional oddities, reported without resolving:**

1. `UserConstants.WATER_DENSITY_KG_PER_M3 = WATER_DENSITY_KG_PER_LITER * GeneralConstants.LITERS_TO_CUBIC_METERS`
   → `0.997 × 0.001 = 0.000997` (`user_constants.py:37`), while its declared unit is
   `KILOGRAMS_PER_CUBIC_METER` (`:55`) and water density is 997 kg/m³.
   **Reading A:** a dimensional bug (should be `× CUBIC_METERS_TO_LITERS = 1000`), which would make
   `anaerobic_lagoon.py:76`, `slurry_storage_outdoor.py:60` and `handler.py:337` under-add water by
   1e6. **Reading B:** downstream code compensates elsewhere. Not traced far enough to choose —
   verify at `manure/storage/anaerobic_lagoon.py:74-76`.
2. `KCAL_TO_MJ = 4.184` (`general_constants.py:128`) is labelled `MCAL_PER_MJ` in `CONSTANTS_TO_UNITS`
   (`:181`) — name/unit mismatch; direction unverified.

### 5.2 Temporal aggregation / disaggregation

- Daily loop → annual block: `simulation_engine.py:647` (`_annual_simulation` iterates
  `year_start_day..year_end_day`), then `_run_post_annual_routines` `:637` → `annual_reset()` `:656`.
- Annual accumulator reset: `SoilData.do_annual_reset` `soil/soil_data.py:426-451` — zeroes
  `annual_soil_evaporation_total`, `annual_runoff_total`, `annual_eroded_sediment_total`,
  `annual_surface_runoff_total`, `annual_runoff_fertilizer_phosphorus`,
  `annual_runoff_nitrates_total`, `annual_runoff_ammonium_total`, manure-pool annual
  runoff/decomposition; re-seeds `initial_water_content` / `initial_nitrates_total` from current
  profile totals.
- Field annual reset chain: `field/field/field.py:1894` → `soil.data.do_annual_reset()` `:1897` and
  `field_data.perform_annual_field_reset()` `:1898`; driven by `field_manager.annual_update_routine`
  `:113-120`.
- **Annual-mean temperature is computed once over the whole simulation, not per year**:
  `Weather._calculate_average_annual_temperature` `weather.py:277-306` (docstring `:294-303` explains
  the deliberate change from per-year averaging). This is a temporal-aggregation choice with
  downstream effect on soil temperature damping and manure storage temperature.
- Interval-based, not daily: ration reformulation `simulation_engine.py:534`, feed degradations
  `:531`, feed-planning recalculation `:483`.
- EEE turns a config date range into a day list: `EEE/emissions.py:263-266`.

### 5.3 Spatial aggregation / disaggregation

- **Whole-field kg → kg/ha** at the Manure/Fertilizer → Soil boundary, by dividing by `field_size`
  (ha): `field/manure_application.py:359, 360, 363, 366` (nitrate, ammonium, organic N per ha);
  `field/fertilizer_application.py:76, 77, 87`; `layer_data.py:600`.
- **kg ↔ mg/kg soil ↔ kg/ha** inside `LayerData`: mass→concentration `layer_data.py:745-752`;
  concentration→area density `determine_soil_nutrient_area_density` `:754-787` (returns kg/ha).
- **Per-soil-layer distribution**: `ManureApplication._apply_subsurface_nutrients` loops
  `depth_factors` from `FertilizerApplication.generate_depth_factors(application_depth, bottom_depths)`
  and splits P and dry matter per layer — `field/manure_application.py:429-454`.
- **Grazing manure coverage**: patch area cm² → ha → field fraction, clipped at 1.0 —
  `manure_application.py:489-490`.
- **Litres → mm depth over the field**: `FieldData.convert_liters_to_millimeters`
  `field_data.py:149-167` (L → mm³ ÷ (ha → mm²)).
- **Per-pen → herd**: `HerdManager.execute_daily_routines` returns `dict[str, ManureStream]` keyed by
  pen (`herd_manager.py:807-812`); `ManureManager.run_daily_update` routes each pen stream to its
  `first_processor` (`manure_manager.py:111-124`), then combines via `ManureStream.__add__`
  (`animal_to_manure_connection.py:208`).
- **Per-field latitude → per-field daylength**: `field_manager.py:95-96`.

### 5.4 Resampling, interpolation, imputation

- **Least-squares seasonal temperature fit** `T(d) = A·cos + B·sin + C` over the simulation window's
  daily means: `Weather.set_linest_temperature_factors` `weather.py:107-145`; components `:70-72`;
  `np.linalg.lstsq` `:132`; yields `intercept_mean_temp`, `amplitude`, `phase_shift` (`:136-145`).
- **Manure temperature from that fit** (damped + lagged sinusoid): `manure/storage/storage.py:151-155`
  — `intercept_mean_temp + amplitude × MANURE_DAMPING_FACTOR × cos(2π/365 × (day − phase_shift − MANURE_TEMPERATURE_LAG))`.
  Constants `MANURE_DAMPING_FACTOR = 0.65` (`manure/manure_constants.py:210`) and
  `MANURE_TEMPERATURE_LAG = 30` days (`:214`). Wired Weather → ManureManager at
  `simulation_engine.py:258` and `manure_manager.py:65, 748-750`.
- **Soil temperature fitting**: `soil/soil_temp.py` `daily_soil_temperature_update` (called
  `field.py:1450`).
- **Daylength is computed, not read**: `CurrentDayConditions.determine_daylength`
  `current_day_conditions.py:65-105` (SWAT 1:1.1.6), with a polar-day/polar-night branch `:91-103`.
- **Precipitation → rain/snow split** (a derivation, not an input):
  `CurrentDayConditions.__post_init__` `current_day_conditions.py:56-62` — if
  `mean_air_temperature < 0.0` the whole `precipitation` becomes `snowfall`, else `rainfall`.
- **Weather gap filling: NOT FOUND IN CODE.** Missing weather is a hard failure
  (`weather.py:342-347`), not imputed. Per-variable defaults exist only in the schema
  (`input/metadata/properties/default.json:5998-6045`, e.g. `precip` default 0, `high` default 21).
- Emissions interpolation helpers live outside the package:
  `helpful_scripts/emissions_interpolation/`, feeding
  `input/data/EEE/full_feeds_emissions_July2024_interpolated*.csv`.

### 5.5 Variables that change name across a boundary

| Quantity | Name on side A | `file:line` | Name on side B | `file:line` |
|---|---|---|---|---|
| Solar radiation | CSV `Hday` (MJ m⁻²) | `input/data/weather/example_arid_weather.csv:1`; schema `default.json:6029` | `CurrentDayConditions.incoming_light` | `current_day_conditions.py:45` |
| Solar radiation | `incoming_light` | `current_day_conditions.py:45` | `solar_radiation` param | `soil/soil.py:70` |
| Mean air temp | CSV `avg` | `default.json:6021` | `mean_air_temperature` → `avg_temp` | `current_day_conditions.py:47` → `soil/soil.py:71` |
| Max air temp | CSV `high` | `default.json:6006` | `max_air_temperature` → `max_temp` | `current_day_conditions.py:48` → `soil/soil.py:73` |
| Min air temp | CSV `low` | `default.json:6014` | `min_air_temperature` → `min_temp` | `current_day_conditions.py:46` → `soil/soil.py:72` |
| Precipitation | CSV `precip` | `default.json:5998` | `precipitation` → `rainfall`/`snowfall` | `current_day_conditions.py:54` → `:51-53`, split `:56-62`; consumed as `rainfall` `soil/soil.py:111` |
| Snow water content | `SoilData.snow_content` | passed at `field/field.py:1456` | `snow_cover` param | `soil/soil.py:75` |
| Annual mean air temp | `Weather.mean_annual_temperature` | `weather.py:92` | `CurrentDayConditions.annual_mean_air_temperature` → `avg_annual_air_temp` | `weather.py:178` / `current_day_conditions.py:50` → `soil/soil.py:76` |
| Plant cover | `field_data.current_residue` + above-ground biomass | `field/field.py:1449` | `plant_cover` param | `soil/soil.py:74` |
| Manure dry matter | `NutrientRequestResults.dry_matter` (kg) | `manure_to_crop_soil_connection.py:114` | `dry_matter_mass` kwarg | `field/field.py:649` |
| **Manure N** | `NutrientRequestResults.nitrogen` (**kg**) | `manure_to_crop_soil_connection.py:89` | re-based as `inorganic_nitrogen_fraction = (supplied_nitrogen / dry_matter) × inorganic_nitrogen_fraction` — **kg → unitless fraction, same identifier name on both sides** | `field/field.py:656-661` |
| Manure P | `NutrientRequestResults.phosphorus` | `:92` | `total_phosphorus_mass` kwarg | `field/field.py:651` |
| Field size | `FieldData.field_size` (ha) | `field_data.py:81` | `field_size` InitVar in `SoilData`/`LayerData` | `soil_data.py:168`, `layer_data.py:16` |
| Temperature fit params | `Weather.intercept_mean_temp / phase_shift / amplitude` | `weather.py:59-61` | same names on `ManureManager.__init__` and each `Storage` | `manure_manager.py:65`, `storage/storage.py:92-94` |

The manure-N row is the one to watch on a figure: the **name stays the same while the unit changes
from kg to a dimensionless fraction**.

---

## 6. External boundaries

### 6.1 What enters

| Source | Format | Provides | Reader `file:line` |
|---|---|---|---|
| `input/data/weather/*.csv` (`example_arid_weather.csv`, `example_arid_weather_w_irrigation.csv`, `example_temperate_weather.csv`) | CSV | `year, jday, precip, high, low, avg, Hday, irrigation` | `input_manager.py:735`; consumed `simulation_engine.py:207` |
| `input/data/config/*.json` | JSON | `start_date`, `end_date` (`%Y:%j`), `nutrient_standard`, `FIPS_county_code` | `simulation_engine.py:218`; `EEE/emissions.py:263-265`, `:105` |
| `input/data/animal/*`, `input/data/animal_genetics/*.csv` | JSON/CSV | herd, ration, population, mean phenotype, semen listings | manifest `input/metadata/example_field_only_metadata.json:12-36` |
| `input/data/EEE/` (`default_costs.csv`, `default_emissions.csv`, `full_feeds_emissions_*.csv`, `full_feeds_land_use_change_emissions_*.csv`, `tractor_dataset.csv`, `constants.json`) | CSV/JSON | energy prices, emission factors, purchased-feed and LUC emissions, tractor specs | `EEE/emissions.py:107, 112`; `EEE/energy.py:145` |
| `input/data/{soil, crop, crop_configurations, field, feed, feed_management, manure, manure_schedule, fertilizer_schedule, tillage_schedule, tasks}` | JSON/CSV | module configurations and schedules | `input_manager.py:790` `_populate_pool` |
| `input/metadata/**` | JSON | schema, manifests, cross-validation | `input_manager.py:540, 575, 639` |
| **Open-Meteo HTTP API** | JSON over HTTPS | **prototype only** — see §6.3 | `prototype_msf/fetch_openmeteo.py:17`; `prototype_msf/realtime_recommendation.py:57`; `prototype_msf/spatializer_workspace/weather_client/client.py:118` |

**Databases: NOT FOUND IN CODE.** RUFAS reads no database of any kind.

### 6.2 What leaves

| Artifact | Writer `file:line` | Content |
|---|---|---|
| `output/CSVs/*_saved_variables_<filter>_*.csv` | `output_manager.py:1806`, `:1861-1863` | every `add_variable` record selected by an output filter |
| `output/output_filters/csv_all_variables.txt` | (input to the writer above) | which variables to emit |
| `output/logs/*_logs_*.json` | `output_manager.dump_logs` `:1942` | info records |
| `output/logs/*_warnings_*.json` | `dump_warnings` `:1954` | warnings |
| `output/logs/*_errors_*.json` | `dump_errors` `:1966` | errors |
| `output/logs/*_variable_names_*.txt` | `dump_variable_names_and_contexts` `:1995` | variable name/context inventory |
| `output/logs/*_InputManager_get_data_log_*.json` | `input_manager.dump_get_data_logs` `:1714` | every `get_data` address requested |
| `output/logs/*_InputManager_delete_data_log_*.json` | `input_manager.dump_delete_data_logs` `:1729` | deleted inputs |
| `output/logs/*_InputManager_metadata_properties_*.csv` | `input_manager.save_metadata_properties` `:1744` | flattened schema snapshot |
| Aggregated reports | `report_generator.generate_report` `:48` (aggregation `:296`, unit combination `:546`) | user-defined aggregated tables |
| Graphs | `graph_generator.py` | plots from report data |
| Bulk non-data pools | `output_manager.dump_all_nondata_pools` `:2130`; flush `:2202` | everything non-variable |
| Filename convention | `output_manager.generate_file_name` `:1284` | `<prefix>_y<year>_d<day>_<base>_<DD-Mon-YYYY_Day_HH-MM-SS>.<ext>` |

Weather is echoed back to output: `Weather.record_weather` `weather.py:225-274` writes
`precipitation`, `rainfall`, `snowfall` (mm), `maximum/minimum/average_temperature` (°C), `radiation`
(MJ/m²), `irrigation` (mm); plus `average_annual_temperature` (°C) at `:101-105`.

### 6.3 The Open-Meteo bridge — where it actually is

This needs three separate statements, because the bridge referred to as "PR #111" is **not in this
repository**.

**(a) In the RUFAS repo, Open-Meteo appears only under `prototype_msf/`, never under `RUFAS/`.**
Three call sites:

1. `prototype_msf/fetch_openmeteo.py:17-24` — `https://api.open-meteo.com/v1/forecast`, **daily**
   params `temperature_2m_max, temperature_2m_min, temperature_2m_mean, precipitation_sum,
   shortwave_radiation_sum` + `latitude, longitude, start_date, end_date,
   timezone=America/Toronto`.
2. `prototype_msf/realtime_recommendation.py:57-63` — identical daily variable list.
3. `prototype_msf/spatializer_workspace/weather_client/` — `BASE_URL` `config.py:20`; **hourly**
   defaults `temperature_2m, wind_speed_10m, precipitation, precipitation_probability,
   relative_humidity_2m` (`config.py:46-52`); **current** defaults `temperature_2m, wind_speed_10m,
   precipitation, relative_humidity_2m` (`config.py:56-61`); `wind_speed_unit=ms` (`config.py:71`),
   `timezone=auto` (`config.py:86`). Request assembly `client.py:290`, `:358`.

**(b) PR #111 is in `supabase-connector`, and the bridge it added has been deleted.** Verified in
`C:\Proyectos\supabase-connector`:

| Event | Commit | Date | Files |
|---|---|---|---|
| Added | `5e657e3`, merged `42ea2f5` *"feat(rufas): OpenMeteo → RUFAS CurrentDayConditions bridge (weather adapter) (#111)"* | 2026-07-20 | `src/features/rufas/weather/openMeteoToRufas.ts` (+62), `src/features/pricing/weather/openMeteo.ts` (+17/−2) |
| Removed | `62feb32`, merged `0493081` *"chore: remove dead openMeteoToRufas bridge (#115)"* | 2026-07-24 | `src/features/rufas/weather/openMeteoToRufas.ts` (−62) |

`git log --all --grep="111"` inside the **RUFAS** repo returns nothing — correct, the PR was never
there. The OpenSpec change `openspec/changes/integrate-slope-aspect-api/proposal.md:109` and
`specs/topographic-input-service/spec.md:122` refer to "the existing Open-Meteo bridge", meaning the
`prototype_msf` client in (a), not the deleted TypeScript file.

The deleted bridge mapped exactly four required fields plus two optional ones
(`openMeteoToRufas.ts` as of `5e657e3`): `shortwave_radiation_sum` → `incoming_light` (MJ/m²),
`temperature_2m_min/mean/max` → `min/mean/max_air_temperature` (°C), `precipitation_sum` →
`precipitation` (mm), and a hard-coded `QUEBEC_ANNUAL_MEAN_TEMP_C = 4.0` →
`annual_mean_air_temperature`.

**(c) Snow variables: NOT requested, anywhere.** A grep for
`snowfall|snow_depth|snow_water|snow` over `prototype_msf/**` returns only prose in
`prototype_msf/slope_aspect_api.md:103-104, 130` and
`spatializer_workspace/spatializer_v2/evaluators/agronomic_match_design.md:48` — no snow parameter in
any URL or variable tuple. `config.py:42-44` documents that `soil_moisture_0_to_1cm` was removed;
snow was never requested. The deleted `openMeteoToRufas.ts` likewise requested no snow variable,
and its own comment states why: *"RUFAS auto-splits rain/snow based on mean_temp < 0°C"* — which
matches `current_day_conditions.py:56-62`.

### 6.4 Weather variables RUFAS itself consumes

CSV header (`input/data/weather/example_arid_weather.csv:1`):
`year,jday,precip,high,low,avg,Hday,irrigation`.

| Column | Declared description / unit | Schema `file:line` | Parsed at |
|---|---|---|---|
| `year` | Year; min 1900 | `default.json:5980-5987` | `weather.py:64` |
| `jday` | Julian day of year; 1–366 | `:5988-5997` | `weather.py:65` |
| `precip` | Amount of precipitation (mm H₂O); min 0, default 0 | `:5998-6005` | `weather.py:78` |
| `high` | Maximum air temperature of the day (°C); default 21 | `:6006-6013` | `weather.py:77` |
| `low` | Minimum air temperature of the day (°C); default 0 | `:6014-6020` | `weather.py:75` |
| `avg` | Average air temperature of the day (°C); default 0 | `:6021-6028` | `weather.py:76`, `:72`, `:92` |
| `Hday` | Solar radiation of the day (MJ m⁻²); min 0, default 0 | `:6029-6037` | `weather.py:74` |
| `irrigation` | Irrigation (mm H₂O); min 0, default 0 | `:6038-6045` | `weather.py:79` |

**RUFAS reads no snow column.** Snowfall is *derived* from `precip` when mean temp < 0
(`current_day_conditions.py:56-62`) and consumed by `Snow.update_snow(current_day_conditions, day)`
(`soil/snow.py:141`, called from `field.py:1447`). Wind speed, relative humidity, snow depth and snow
water equivalent are **NOT FOUND IN CODE** as RUFAS weather inputs — which is the constraint any new
external weather source has to respect.

### 6.5 `spatializer_v2` is outside RUFAS

For the figure: `spatializer_v2` must not be drawn as a RUFAS module. It lives in
`C:\Proyectos\terranimo-test\` with a working copy at
`prototype_msf/spatializer_workspace/spatializer_v2/`. It does not import RUFAS. Its only connection
is an adapter that reads a RUFAS state object and returns evaluator inputs —
`spatializer_v2/adapters/rufas_to_runoff.py`, which reads
`field.soil.data.soil_layers[0].water_filled_pore_space` and raises `IncompleteRufasStateError` when
the state is not populated. Nothing in `RUFAS/` imports `spatializer_v2`.

---
## 7. Extension points — what a subsurface-drainage module would have to touch

### 7.1 There is exactly one plugin-style registry in RUFAS, and it is manure-only

- **ABC**: `manure/processor.py:14` `class Processor(ABC)` with `@abstractmethod receive_manure`
  (`:53-54`) and `@abstractmethod process_manure(conditions, time) -> dict[str, ManureStream]`
  (`:71-72`). The reporting prefix is auto-derived from the base class name (`:50-51`).
- **Subclass chain**: `manure/storage/storage.py:32` `class Storage(Processor)` →
  `anaerobic_lagoon.py:14`, `composting.py:53`, `open_lot.py:15`.
- **Registry**: `manure/processor_enum.py:19` `class ProcessorType(Enum)` maps config strings to
  classes (`:25-46`), resolved by `get_processor_class` (`:49`, lookup `:69`).
- **Instantiation**: `manure/manure_manager.py:743`
  `processor_initializer = ProcessorType.get_processor_class(processor_type)` → `:746`
  `processor = processor_initializer(**processor_config)`.
- **Schema mirrors the same strings**: `input/metadata/properties/default.json:5559`
  `"pattern": "^(SlurryStorageOutdoor|SlurryStorageUnderfloor|AnaerobicLagoon|Composting|OpenLot|BeddedPack|DailySpread)$"`
  (plus `processor_type` blocks at `:5420, :5456, :5491, :5556`).

### 7.2 Soil/crop has no such abstraction

`soil/soil.py:16` `class Soil` hard-codes its nine components in `__init__` (`:57-66`), and the daily
loop hard-codes every call. Adding a `TileDrainage` submodule is therefore **not** a registration —
it is an edit in nine places:

| Touch point | `file:line` |
|---|---|
| New component attribute + docstring | `soil/soil.py:57-66` (and the Attributes block `:29-50`) |
| Daily call in the **real** loop | `field/field/field.py:1518-1540` (`percolate` → `infiltrate` → `percolate_infiltrated_water` → `erode` → cycles) |
| Daily call in the **unused** Soil routine | `soil/soil.py:153-160` (see §3.4 and Bug 1) |
| State fields | `soil/soil_data.py` (dataclass defaults ~`:197-255`) and/or `soil/layer_data.py:253-283` |
| Config→dataclass wiring **whitelist** | `field/manager/field_manager.py:543-556` (`expected_values`, `_setup_soil`) and `:602-624` (`_setup_soil_layer`) |
| Input schema | `input/metadata/properties/default.json` → `soil_profile_properties` block |
| Validation/defaults engine | `data_validator.py:1411-1455` |
| Output reporting | `field/manager/field_data_reporter.py:29-41` (`send_daily_variables`), plus a `send_*` method like `:1429` `send_soil_daily_variables` |
| Engine hookup | `simulation_engine.py:214`, `:416` `field_manager.daily_update_routine(...)`, `:661` annual |

The **whitelist** at `field_manager.py:543-556` / `:602-619` is the trap: a key present in the JSON
schema but absent from those lists is silently never read (this is exactly what happens to three
existing keys — see §9).

### 7.3 Existing drainage code: none

`grep -niE "drainage|tile_drain|\bdrain(s|ed|ing)?\b"` over `RUFAS/` and `tests/` returns **zero
hits**. Three things look related and are not:

- `field/field_data.py:80` `seasonal_high_water_table: bool = False` — a boolean consumed by
  `soil/percolation.py:32` `percolate(has_seasonal_high_water_table)`. It **gates percolation out of
  the profile**; it does not model drainage.
- `vadose_zone_layer` — a single `LayerData` below the profile (`soil/soil_data.py` ~`:336-337`, per
  `docs/rufas_field_representation.md:148`); used by `crop_management.py:500`,
  `tillage_application.py:111`, `field_data_reporter.py:1251`. A deep sink, not a drain.
- `subsurface_*` in `fertilizer_application.py:86-134`, `manure_application.py:298-447`,
  `crop_management.py:486-505` — **subsurface nutrient placement**, not water drainage.

**Implication for MSF:** a drainage module cannot be plugged in. It has to be inserted into the
hard-coded water sequence in `field.py:_cycle_water`, and its state has to be added to `SoilData` or
`LayerData` *and* to both whitelists.

---

## 8. Scientific provenance

Citations below are **as written in the code**. Where a module names no model, the row says so rather
than attributing one.

### 8.1 Per module

| Module | Model named in code | `file:line` |
|---|---|---|
| infiltration | SWAT 2:1.1, eqn 2:1.1.4 | `soil/infiltration.py:9`, `:119` |
| percolation | SWAT 2:3.2, eqn 2:3.2.4 | `soil/percolation.py:10`, `:147` |
| evaporation | SWAT 2:2.3.3.2, eqn 2:2.3.16 | `soil/evaporation.py:10`, `:98` |
| snow | SWAT 2009, eqn 1:2.5.1 | `soil/snow.py:13`, `:68` |
| soil_temp | SWAT 1:1.3.3 | `soil/soil_temp.py:8-9`, `:65` |
| soil_erosion | **MUSLE** / SWAT 4:1.1 | `soil/soil_erosion.py:8`, `:148` |
| N: denitrification | SWAT 3:1.4 **+ Parton et al.** ("Generalized model for N₂ and N₂O production from nitrification and…") | `nitrogen_cycling/denitrification.py:10`, `:158`, `:163` |
| N: humus_mineralization | SWAT 3:1.2.1 | `nitrogen_cycling/humus_mineralization.py:7-8` |
| N: mineralization_decomp | SWAT 3:1.2.2, eqn 3:1.2.9 | `nitrogen_cycling/mineralization_decomp.py:35` |
| N: nitrification_volatilization | SWAT 3:1.3 | `nitrogen_cycling/nitrification_volatilization.py:8-9` |
| N: leaching_runoff_erosion | SWAT 4:2.1, 4:2.2 **+ Vadas & Powell (2019)** | `nitrogen_cycling/leaching_runoff_erosion.py:16-17`, `:35` |
| P: fertilizer | **SurPhos** ("pseudocode_soil S.5.C.I.1, SurPhos [14]") | `phosphorus_cycling/fertilizer.py:9`, `:295` |
| P: manure | **SurPhos** | `phosphorus_cycling/manure.py:6`, `:108` |
| P: phosphorus_mineralization | **SurPhos** (`pminrl.f` lines 69, 70) + **Vadas, Krogstad & Sharpley (2006)** | `phosphorus_mineralization.py:9`, `:219-220` |
| P: soluble_phosphorus | **APLE** (Agricultural Phosphorus Loss Estimator), eqn [15] | `phosphorus_cycling/soluble_phosphorus.py:10`, `:173` |
| C: decomposition | **DAYCENT** — as a Basecamp folder path, not a citation | `carbon_cycling/decomposition.py:24-27` |
| C: carbon_cycle | **no model named** — internal pseudocode only (`pseudocode_soil S.6.D.1–S.6.D.7`) | `carbon_cycling/carbon_cycle.py:30-32` |
| C: pool_gas_partition | **no model named** — pseudocode only | `carbon_cycling/pool_gas_partition.py:24-26` |
| C: residue_partition | pseudocode + **Parton et al. 1987** for three rate constants only | `carbon_cycling/residue_partition.py:26`, `:363`, `:392`, `:757` |
| crop heat_units | SWAT 5:3.1 | `crop/heat_units.py:46`, `:94` |
| crop nitrogen_uptake | SWAT 5:2.3.1 | `crop/nitrogen_uptake.py:70`, `:215` |
| crop phosphorus_uptake | SWAT 5:2.3.2 | `crop/phosphorus_uptake.py:6`, `:41` |
| crop water_uptake | SWAT 5:2.2.1 | `crop/water_uptake.py:51`, `:445` |
| crop biomass_allocation | SWAT 5:2.1.1 + 5:2.4 | `crop/biomass_allocation.py:8-9` |
| crop leaf_area_index | SWAT 5:2.1.2 | `crop/leaf_area_index.py:9` |
| crop dormancy | SWAT 5:1.2; Appendix A.1.12 | `crop/dormancy.py:62`, `:28` |
| crop non_water_uptake | SWAT 5:2.3.5, 5:2.3.23 | `crop/non_water_uptake.py:210` |
| crop harvest_operations | **NOT FOUND IN CODE** (pure Enum) | `crop/harvest_operations.py:1-16` |
| crop.py (composite) | **NOT FOUND IN CODE** | `crop/crop.py:25-60` |
| tillage_application | SWAT 6:1.6 + SurPhos `plow.f` | `field/tillage_application.py:12`, `:101`, `:274` |
| manure_application | **SurPhos**, theoretical doc p.7 | `field/manure_application.py:16`, `:86` |
| fertilizer_application | **SurPhos** ("originates with Pete Vadas' SurPhos model") | `field/fertilizer_application.py:160`, `:69` |
| manure_pool | **SurPhos** [11]; pseudocode_soil S.5.D.I.3, II.1 | `soil/manure_pool.py:502`, `:722` |
| manure — bedded_pack | IPCC 2019 | `manure/storage/bedded_pack.py:357` |
| manure — solids_storage_calculator | IPCC (2006) | `manure/storage/solids_storage_calculator.py:198` |
| manure — continuous_mix (digester) | IPCC Tier II, via April Leytem (USDA) | `manure/digester/continuous_mix.py:323` |
| manure — storage.py, anaerobic_lagoon, composting, open_lot, slurry_*, separator, handler | **NOT FOUND IN CODE** (only "Arrhenius" as a method name, `storage.py:311`) | — |
| animal — enteric_methane_calculator | IPCC Tier 2 2006; Niu et al. 2018; Mills et al. 2003 | `animal/digestive_system/enteric_methane_calculator.py:204`, `:65` |
| animal — manure_excretion_calculator | ASABE 2005; Nennich 2005; Reed 2015; Johnson 2016; NASEM 2021; NRC 2001; Vadas 2007 | `manure_excretion_calculator.py:223`, `:767` |
| EEE (energy/tractor/tractor_implement) | internal "EEE Functions file" only (Helper Functions 412, 419, 420, 421) | `EEE/energy.py:436`, `tractor.py:123`, `tractor_implement.py:110` |

### 8.2 Resolving the SurPhos-vs-APLE and DayCent-vs-CENTURY contradiction

Repo-wide greps for SurPhos / APLE / DayCent / CENTURY / Vadas / Parton / Neitsch / SWAT give the
following **facts**:

- **`CENTURY` appears nowhere in `RUFAS/` source.** The only hits in the repo are
  `prototype_msf/README.md:115` ("Parton et al. (1987). CENTURY model. *Soil Sci. Soc. Am. J.*
  51:1173-1179") and `RUFAS/util.py:1077`, an unrelated date-format string
  (`"year_without_century"`).
- **`DAYCENT` appears once in source**: `carbon_cycling/decomposition.py:27`, as a Basecamp *folder
  path*, not a citation. Also `docs/scientific/crop_and_soil.tex:3252`: "…are based on the DAYCENT
  model."
- **"Vadas 2008" and "Vadas & Powell 2013" are not in the code.** `prototype_msf/README.md:113` and
  `openspec/changes/integrate-slope-aspect-api/proposal.md:197` say "Vadas & Powell (2013). SurPhos
  model", but the only Vadas bib entry is `docs/scientific/resources/crop_and_soil.bib:542` =
  **vadas2007**, *"A model for phosphorus transformation and runoff loss for surface-applied
  manures"*, J. Environ. Qual. 36(1):324-332.
- **`neitsch2011swat`** (`crop_and_soil.bib:66-71`) exists — Neitsch, Arnold, Kiniry & Williams, SWAT
  Theoretical Documentation Version 2009, TWRI TR-406, 2011 — but **no `.py` file cites "Neitsch" by
  name**; all 200+ SWAT hits are bare "SWAT `<section>`".
- **`parton1987analysis`** (`crop_and_soil.bib:11-19`) is the CENTURY paper, but the string "CENTURY"
  is never used in code.
- `crop_and_soil.tex:22`: "…drawn from existing models of soil and plant biogeochemistry including
  the SWAT model, Daycent, and SurPhos."

**Per-file verdict:**

| File | What the code itself names | Claim A (SurPhos / DayCent) | Claim B (APLE / CENTURY) |
|---|---|---|---|
| `phosphorus_cycling/soluble_phosphorus.py:10,131,173,195,223,227` | **APLE only** — eqns [9], [14], [15], [16], "page 8 of the APLE" | **contradicted for this file** | **supported for this file** |
| `phosphorus_cycling/manure.py:6,97,108,112` | **SurPhos only** | supported | not addressed (no APLE mention) |
| `phosphorus_cycling/fertilizer.py:9,268,295,325,358` | **SurPhos only** | supported | not addressed |
| `phosphorus_cycling/phosphorus_mineralization.py:9,139,219` | SurPhos + Vadas/Krogstad/Sharpley 2006 | supported | not addressed |
| `carbon_cycling/decomposition.py:24-27` | **DAYCENT** | supported | **contradicted** — "CENTURY" absent |
| `carbon_cycling/residue_partition.py:363,392,757` | **"Parton et al. 1987"** for three rate constants; module ref is pseudocode S.6.B | partially — Parton 1987 *is* the CENTURY paper, but the code names neither model | not addressed |
| `carbon_cycling/carbon_cycle.py:30`, `pool_gas_partition.py:24` | **no model named** | not addressed | not addressed |
| Neitsch 2011 | in `.bib`/`.tex` only, never in `.py` | — | — |

**Remaining ambiguity, not resolved:** `docs/scientific/crop_and_soil.tex:2404` says the soluble-P
equations are "based on equations from the APLE **and SurPhos** models `\parencite{vadas2007}`" — it
attaches APLE prose to the *vadas2007* key, which is the **SurPhos** paper. So the `.py` file says
APLE, the `.tex` says both and cites SurPhos. **Both readings are reported; neither is chosen.**

**Bottom line from the code alone:** SurPhos → manure / fertilizer / mineralization P +
manure_application + tillage. APLE → soluble_phosphorus (plus one bound in `layer_data.py:704-709`
that cites **both** SurPhos eqn [18] and APLE eqn [11]). DAYCENT → `decomposition.py` only. CENTURY →
absent. "Vadas 2008" → absent.

---

## 9. Code that is not connected

- **`AnimalHealth` is an orphan.** `animal/animal_health/animal_health.py:7` `class AnimalHealth` is
  never imported or instantiated anywhere in `RUFAS/` or `tests/` (only self-imports `:1-3`). Its
  siblings `disease.py`, `outcomes.py`, `animal_health_status.py` are imported only by it. An entire
  health subsystem exists and never runs.
- **`Soil.daily_soil_routine` and `Soil.daily_soil_water_routine` are dead in production.**
  `soil/soil.py:68` and `:109` are called **only** from
  `tests/test_biophysical/test_crop_soil_field/soil_tests/test_soil.py:24` and `:75`. Production uses
  `field.py:1518-1540`. See §3.4 and Bug 1.
- **Referenced in at most one file**: `AminoAcidComposition` (`animal/ration/amino_acid.py`),
  `Mixing` (manure).
- **Unused parameters**: `ContinuousMix.process_manure(self, conditions, time)` never uses
  `conditions` (`manure/digester/continuous_mix.py:67`), which is required by the ABC signature
  (`processor.py:72`). `NutrientUptake.uptake(self, soil_data)` (`crop/nutrient_uptake.py:22`) is a
  `pass` stub.
- **Unwired schema keys — declared, validated, and then read by nobody**:
  `support_practice_factor`, `soil_evaporation_compensation_coefficient`,
  `initial_fresh_organic_phosphorus_concentration`. All three are present in `default.json`
  `soil_profile_properties` but absent from **both** `expected_values` whitelists
  (`field_manager.py:543-556` and `:602-619`); grepping for them in `field/manager/` and
  `input_manager.py` returns nothing. A user can set them and nothing happens.
- **`SimulationEngine.annual_mass_balance` is `pass`** (`simulation_engine.py:663-664`) — no mass
  balance is computed.
- **No annual reset for animal, manure or feed storage** — `simulation_engine.py:656-661` resets
  fields only (§3.6).

---

## 10. Two bugs, verified

Both were re-checked directly against the source for this document, not taken on report.

### 10.1 Bug 1 — `infiltrate` arity: **real, and masked by a test mock**

```
RUFAS/biophysical/field/soil/infiltration.py:29
    def infiltrate(self, rainfall: float) -> None:          # ONE parameter

RUFAS/biophysical/field/field/field.py:1519
    self.soil.infiltration.infiltrate(water_reaching_soil)  # 1 arg — consistent

RUFAS/biophysical/field/soil/soil.py:154
    self.infiltration.infiltrate(rainfall, weighting_coefficient, potential_evapotranspiration)
                                                            # 3 args — TypeError if executed
```

`weighting_coefficient` and `potential_evapotranspiration` are declared parameters of
`daily_soil_water_routine` (`soil.py:111-113`) and appear **nowhere** in the body of `infiltrate`
(`infiltration.py:50-99`).

**Why it is never caught:** the only caller of `daily_soil_water_routine` is
`tests/test_biophysical/test_crop_soil_field/soil_tests/test_soil.py:75`, which replaces
`soil.infiltration.infiltrate` with a `MagicMock()` at `test_soil.py:67` and then asserts the
three-argument call at `test_soil.py:87`:

```
test_soil.py:67   soil.infiltration.infiltrate = MagicMock()
test_soil.py:87   soil.infiltration.infiltrate.assert_called_once_with(
                      rainfall, weighting_coefficient, potential_evapotranspiration)
```

The test **encodes the wrong arity**, so it passes and would keep passing if the signature were
fixed in only one place.

**Status: inconsistent, but currently unreachable in production**, because `daily_soil_water_routine`
is dead code (§9). It becomes a live `TypeError` the moment anyone wires that routine up — which is
precisely what §7.2 says a drainage module would touch.

### 10.2 Bug 2 — schema defaults: **real, two distinct defects**

**Mechanism.** `DataValidator._fix_data` overwrites a user value that violates the schema with
`variable_properties["default"]` (`data_validator.py:1444` list branch, `:1447` dict branch), logging
only a **warning** (`:1441`, `:1454`). Where no `default` key exists it errors instead (`:1411-1428`).

**Defect (a) — value drift between the two default sources.** `input/metadata/properties/default.json`
(`soil_profile_properties`) and the dataclass defaults disagree for eight variables. Whichever path
initialises the object wins:

| Key | Schema default | Dataclass default | `file:line` |
|---|---|---|---|
| `humus_mineralization_rate_factor` | `0.003` (`default.json:5728`) | `0.0003` — **10×** | `soil/soil_data.py:252` |
| `slope_length` | `50` | `3` | `soil/soil_data.py:226` |
| `denitrification_threshold_water_content` | `1.0` | `1.10` | `soil/soil_data.py:254` |
| `clay_fraction` | `0.225` | `0.187` | `soil/layer_data.py:280` |
| `silt_fraction` | `0.625` | `0.645` | `soil/layer_data.py:282` |
| `sand_fraction` | `0.125` | `0.145` | `soil/layer_data.py:281` |
| `rock_fraction` | `0.013` | `0.01` | `soil/layer_data.py:283` |
| `ammonium_volatilization_cation_exchange_factor` | `0.45` | `0.15` — **3×** | `soil/layer_data.py:396` |

The texture triplet matters for MSF: schema says 22.5 / 62.5 / 12.5 % clay/silt/sand, the dataclass
says 18.7 / 64.5 / 14.5 %. Those are **different texture classes**.

Keys where the two sources **agree** (checked, no drift): `second_moisture_condition_parameter` 85,
`average_subbasin_slope` 0.05, `albedo` 0.16, `denitrification_rate_coefficient` 1.4,
`residue_fresh_organic_mineralization_rate` 0.05, `pH` 7.0, `initial_temperature`/`temperature`
15.05, `bulk_density` 1.4, `organic_carbon_fraction` 0.012, water concentrations 0.25/0.2/0.3/0.5,
`saturated_hydraulic_conductivity` 9.5.

**Defect (b) — silent override and silent discard.** An out-of-range user value is replaced by the
schema default at `data_validator.py:1444/1447` with a warning only, and the simulation continues.
Worse, for three keys the user value is **never read at all** because they are missing from the
whitelists (§9):

- `support_practice_factor` — schema default `0.08`, but
  `soil_erosion.py:339-355` `_determine_support_practice_factor()` takes **no arguments** and ends in
  `return 1`. Verified verbatim. The SWAT 4:1.1.3 support-practice factor is hard-coded to 1,
  i.e. "no contour tillage, no stripcropping, no terracing", regardless of configuration.
- `soil_evaporation_compensation_coefficient` — schema declares it at *profile* level with default
  `0.95`; the attribute actually lives on **`LayerData`** with default `1` (`layer_data.py:266`) and
  is consumed at `evaporation.py:54`.
- `initial_fresh_organic_phosphorus_concentration` — declared, never read.

**No comment or document in the repo acknowledges either defect** — searched; **NOT FOUND IN CODE**.

---
## 11. Section 2 repeated as a flat list

The same 219 edges as §2, one per line, pipe-separated, no markdown — ready to paste into a graph
tool or a spreadsheet. Column order:

```
origen|destino|variable|nombre_codigo|unidad|timestep|tipo|archivo:linea|via_estado
```

Paths are relative to `C:\Proyectos\RuFaS-MyForageSystem\`. `unidad no declarada` means the code
declares no unit — not that the quantity is dimensionless.

```
origen|destino|variable|nombre_codigo|unidad|timestep|tipo|archivo:linea|via_estado
input_manager|weather|datos meteorológicos crudos|weather_data|unidad no declarada|init|dict|RUFAS\simulation_engine.py:207|arg
weather|weather|condiciones diarias indexadas por fecha|weather_data[date_key]|unidad no declarada|init|dict[date, CurrentDayConditions]|RUFAS\weather.py:90|estado: Weather.weather_data
weather|weather|precipitación repartida a lluvia o nieve|snowfall / rainfall|mm|init (post_init del dataclass)|escalar|RUFAS\current_day_conditions.py:60-62|estado: CurrentDayConditions.snowfall/.rainfall
weather|weather|duración del día para la latitud del campo|daylength|hours|daily|escalar|RUFAS\weather.py:177|estado: Weather.weather_data[date].daylength
weather|weather|temperatura media anual del aire|annual_mean_air_temperature|degrees C|daily|escalar|RUFAS\weather.py:178|estado: Weather.weather_data[date].annual_mean_air_temperature
weather|weather|temperatura media anual de toda la simulación|mean_annual_temperature|degrees C|init|escalar|RUFAS\weather.py:92|estado: Weather.mean_annual_temperature
weather|manure.ManureManager|intercepto/desfase/amplitud de la curva sinusoidal de temperatura|intercept_mean_temp, phase_shift, amplitude|degrees C (intercept, amplitude) / days (phase_shift) - unidad no declarada en código|init|escalar|RUFAS\simulation_engine.py:258|arg
manure.ManureManager|manure.storage.AnaerobicLagoon / manure.storage.SlurryStorageOutdoor|parámetros sinusoidales de temperatura|intercept_mean_temp, phase_shift, amplitude|unidad no declarada|init|escalar|RUFAS\biophysical\manure\manure_manager.py:748-750|estado: Storage.intercept_mean_temp/.phase_shift/.amplitude
weather|field.manager.FieldManager|condiciones del día para la latitud del campo|current_conditions|unidad no declarada|daily|dataclass CurrentDayConditions|RUFAS\biophysical\field\manager\field_manager.py:94|arg
field.manager.FieldManager|OutputManager|duración del día|daylength|HOURS|daily|escalar|RUFAS\biophysical\field\manager\field_manager.py:101|estado: OutputManager
field.manager.FieldManager|field.field.Field|condiciones del día|current_conditions|unidad no declarada|daily|dataclass CurrentDayConditions|RUFAS\biophysical\field\manager\field_manager.py:105-106|arg
field.field.Field|field.soil.snow.Snow|condiciones del día (nevada, temp. media)|current_day_conditions|mm / degrees C|daily|dataclass CurrentDayConditions|RUFAS\biophysical\field\field\field.py:1448|arg
field.soil.snow.Snow|field.soil (SoilData)|contenido de agua del manto de nieve|snow_content|mm H2O|daily|escalar|RUFAS\biophysical\field\soil\snow.py:183|estado: SoilData.snow_content
field.soil.snow.Snow|field.soil (SoilData)|agua de fusión de nieve del día|snow_melt_amount|mm H2O|daily|escalar|RUFAS\biophysical\field\soil\snow.py:199|estado: SoilData.snow_melt_amount
field.soil.snow.Snow|field.soil (SoilData)|reducción del manto por fusión|snow_content|mm H2O|daily|escalar|RUFAS\biophysical\field\soil\snow.py:200|estado: SoilData.snow_content
field.field.Field|field.soil.snow.Snow|demanda máxima de sublimación|maximum_sublimation|mm|daily|escalar|RUFAS\biophysical\field\field\field.py:1565|arg
field.soil.snow.Snow|field.soil (SoilData)|agua sublimada|water_sublimated|mm|daily|escalar|RUFAS\biophysical\field\soil\snow.py:217|estado: SoilData.water_sublimated
field.soil.snow.Snow|field.soil (SoilData)|manto de nieve tras sublimación|snow_content|mm H2O|daily|escalar|RUFAS\biophysical\field\soil\snow.py:218|estado: SoilData.snow_content
field.field.Field|field.soil.soil_temp.SoilTemp|radiación solar incidente|current_conditions.incoming_light|MJ/m^2|daily|escalar|RUFAS\biophysical\field\field\field.py:1452|arg
field.field.Field|field.soil.soil_temp.SoilTemp|temperatura media/mínima/máxima del aire|mean_air_temperature, min_air_temperature, max_air_temperature|degrees C|daily|escalar|RUFAS\biophysical\field\field\field.py:1453-1455|arg
field.field.Field|field.soil.soil_temp.SoilTemp|cobertura total de planta más residuo|total_plant_cover|kg per hectare|daily|escalar|RUFAS\biophysical\field\field\field.py:1450,1456|arg
field.soil (SoilData)|field.soil.soil_temp.SoilTemp|contenido de nieve como aislante|self.soil.data.snow_content|mm|daily|escalar|RUFAS\biophysical\field\field\field.py:1457|arg
field.field.Field|field.soil.soil_temp.SoilTemp|temperatura media anual del aire|annual_mean_air_temperature|degrees C|daily|escalar|RUFAS\biophysical\field\field\field.py:1458|arg
field.soil.soil_temp.SoilTemp|field.soil (LayerData)|temperatura de cada capa de suelo|layer.temperature|degrees C|daily|escalar (por capa)|RUFAS\biophysical\field\soil\soil_temp.py:91|estado: SoilData.soil_layers[i].temperature
field.soil.soil_temp.SoilTemp|field.soil (LayerData)|temperatura de la capa del día previo|layer.previous_day_temperature|degrees C|daily|escalar (por capa)|RUFAS\biophysical\field\soil\soil_temp.py:98|estado: SoilData.soil_layers[i].previous_day_temperature
field.field.Field|field.field.Field|agua de aplicación de purín acumulada|field_data.manure_water|mm|per-event|escalar|RUFAS\biophysical\field\field\field.py:953|estado: FieldData.manure_water
field.field.Field|field.field.Field|agua de purín consumida y reseteada|field_data.manure_water|mm|daily|escalar|RUFAS\biophysical\field\field\field.py:1646,1656|estado: FieldData.manure_water
field.field.Field|OutputManager|agua aportada por purín|manure_water|MILLIMETERS|daily|escalar|RUFAS\biophysical\field\field\field.py:1654|estado: OutputManager
weather|field.field.Field|lluvia del día para el riego|current_conditions.rainfall|mm|daily|escalar|RUFAS\biophysical\field\field\field.py:1498|arg
weather|field.field.Field|riego prefijado en el archivo meteorológico|current_conditions.irrigation|mm|daily|escalar|RUFAS\biophysical\field\field\field.py:1502|arg
field.field.Field|field.field.Field|déficit hídrico del intervalo de riego|field_data.current_water_deficit|mm|daily|escalar|RUFAS\biophysical\field\field\field.py:1616-1623|estado: FieldData.current_water_deficit
field.field.Field|field.field.Field|riego anual acumulado|field_data.annual_irrigation_water_use_total|mm|daily|escalar|RUFAS\biophysical\field\field\field.py:1624,1630|estado: FieldData.annual_irrigation_water_use_total
field.field.Field|OutputManager|riego aplicado|field_watering|MILLIMETERS|per-event|escalar|RUFAS\biophysical\field\field\field.py:1926|estado: OutputManager
field.field.Field|field.crop.Crop|precipitación disponible para el dosel|precipitation_reaching_soil|mm|daily|escalar|RUFAS\biophysical\field\field\field.py:1683|arg
field.crop.Crop|field.crop (CropData)|agua retenida en el dosel|canopy_water|mm|daily|escalar|RUFAS\biophysical\field\crop\crop.py:214|estado: CropData.canopy_water
field.crop.Crop|field.field.Field|agua que llega al suelo tras intercepción|precipitation_reaching_soil|mm|daily|escalar|RUFAS\biophysical\field\crop\crop.py:218|arg
field.soil (SoilData)|field.field.Field|agua de fusión de nieve sumada al agua que llega al suelo|self.soil.data.snow_melt_amount|mm|daily|escalar|RUFAS\biophysical\field\field\field.py:1506|estado: SoilData.snow_melt_amount
field.field.Field|field.field.Field|evapotranspiración potencial del día|field_data.max_evapotranspiration|mm|daily|escalar|RUFAS\biophysical\field\field\field.py:1514|estado: FieldData.max_evapotranspiration
field.field.Field|field.crop.WaterDynamics|demanda evapotranspirativa restante para el dosel|evapotranspirative_demand|mm|daily|escalar|RUFAS\biophysical\field\field\field.py:1704|arg
field.field.Field|field.soil.percolation.Percolation|presencia de nivel freático estacional alto|field_data.seasonal_high_water_table|unidad no declarada (bool)|daily|escalar|RUFAS\biophysical\field\field\field.py:1518|arg
field.soil.percolation.Percolation|field.soil (LayerData)|agua percolada por capa reseteada|percolated_water|unidad no declarada|daily|array (vectorizado por capa)|RUFAS\biophysical\field\soil\percolation.py:56|estado: SoilData.soil_layers[*].percolated_water
field.soil.percolation.Percolation|field.soil (LayerData)|agua percolada a la zona vadosa|vadose_zone_layer.water_content|unidad no declarada|daily|escalar|RUFAS\biophysical\field\soil\percolation.py:85|estado: SoilData.vadose_zone_layer.water_content
field.field.Field|field.soil.infiltration.Infiltration|agua que alcanza la superficie del suelo|water_reaching_soil|mm|daily|escalar|RUFAS\biophysical\field\field\field.py:1519|arg
field.soil (LayerData)|field.soil.infiltration.Infiltration|temperatura de la capa superficial (suelo helado)|self.data.soil_layers[0].temperature|degrees C|daily|escalar|RUFAS\biophysical\field\soil\infiltration.py:88|estado: SoilData.soil_layers[0].temperature
field.soil.infiltration.Infiltration|field.soil (SoilData)|escorrentía acumulada del día|accumulated_runoff|mm|daily|escalar|RUFAS\biophysical\field\soil\infiltration.py:94|estado: SoilData.accumulated_runoff
field.soil.infiltration.Infiltration|field.soil (SoilData)|agua infiltrada|infiltrated_water|mm|daily|escalar|RUFAS\biophysical\field\soil\infiltration.py:96|estado: SoilData.infiltrated_water
field.soil.infiltration.Infiltration|field.soil (SoilData)|escorrentía anual acumulada|annual_runoff_total|mm|daily|escalar|RUFAS\biophysical\field\soil\infiltration.py:99|estado: SoilData.annual_runoff_total
field.soil.infiltration.Infiltration|field.soil.percolation.Percolation|agua infiltrada a repartir entre capas|self.data.infiltrated_water|mm|daily|escalar|RUFAS\biophysical\field\soil\percolation.py:102|estado: SoilData.infiltrated_water
field.soil.percolation.Percolation|field.soil (LayerData)|contenido de agua por capa tras infiltración|layer.water_content|unidad no declarada|daily|escalar (por capa)|RUFAS\biophysical\field\soil\percolation.py:106,109|estado: SoilData.soil_layers[i].water_content
field.soil.percolation.Percolation|field.soil (LayerData)|sobrante percolado a zona vadosa|vadose_zone_layer.water_content|unidad no declarada|daily|escalar|RUFAS\biophysical\field\soil\percolation.py:114|estado: SoilData.vadose_zone_layer.water_content
field.field.Field|field.soil.soil_erosion.SoilErosion|tamaño del campo, factor C mínimo, residuo y agua total|field_size, 0.02, current_residue, total_water|ha / unitless / kg per hectare / mm|daily|escalar|RUFAS\biophysical\field\field\field.py:1522-1527|arg
field.soil (SoilData)|field.soil.soil_erosion.SoilErosion|escorrentía acumulada|self.data.accumulated_runoff|mm|daily|escalar|RUFAS\biophysical\field\soil\soil_erosion.py:106|estado: SoilData.accumulated_runoff
field.soil.soil_erosion.SoilErosion|field.soil (SoilData)|volumen de escorrentía superficial|surface_runoff_volume|mm per hectare|daily|escalar|RUFAS\biophysical\field\soil\soil_erosion.py:106|estado: SoilData.surface_runoff_volume
field.soil.soil_erosion.SoilErosion|field.soil (SoilData)|sedimento erosionado|eroded_sediment|metric tons|daily|escalar|RUFAS\biophysical\field\soil\soil_erosion.py:117|estado: SoilData.eroded_sediment
field.soil.soil_erosion.SoilErosion|field.soil (SoilData)|totales anuales de sedimento y escorrentía|annual_eroded_sediment_total, annual_surface_runoff_total|metric tons / mm per hectare|daily|escalar|RUFAS\biophysical\field\soil\soil_erosion.py:120-121|estado: SoilData
field.field.Field|field.soil.phosphorus_cycling.PhosphorusCycling|agua que llega al suelo, escorrentía, tamaño de campo, temperatura media|water_reaching_soil, accumulated_runoff, field_size, mean_air_temperature|mm / mm / ha / °C|daily|escalar|RUFAS\biophysical\field\field\field.py:1528-1533|arg
field.soil.phosphorus_cycling.PhosphorusCycling|field.soil.phosphorus_cycling.manure|lluvia, escorrentía, tamaño de campo, temperatura media|rainfall, runoff, field_size, mean_air_temperature|mm / mm / ha / °C|daily|escalar|RUFAS\biophysical\field\soil\phosphorus_cycling\phosphorus_cycling.py:65|arg
field.soil.phosphorus_cycling.PhosphorusCycling|field.soil.phosphorus_cycling.fertilizer|lluvia, escorrentía, tamaño de campo|rainfall, runoff, field_size|mm / mm / ha|daily|escalar|RUFAS\biophysical\field\soil\phosphorus_cycling\phosphorus_cycling.py:66|arg
field.soil.phosphorus_cycling.PhosphorusCycling|field.soil.phosphorus_cycling.mineralization|tamaño del campo|field_size|ha|daily|escalar|RUFAS\biophysical\field\soil\phosphorus_cycling\phosphorus_cycling.py:67|arg
field.soil.phosphorus_cycling.PhosphorusCycling|field.soil.phosphorus_cycling.soluble_phosphorus|escorrentía y tamaño del campo|runoff, field_size|mm / ha|daily|escalar|RUFAS\biophysical\field\soil\phosphorus_cycling\phosphorus_cycling.py:68|arg
field.field.Field|field.soil.carbon_cycling.CarbonCycling|agua que llega al suelo, temperatura media, tamaño de campo|water_reaching_soil, mean_air_temperature, field_size|mm / °C / ha|daily|escalar|RUFAS\biophysical\field\field\field.py:1534-1538|arg
field.soil.carbon_cycling.CarbonCycling|field.soil.carbon_cycling.residue_partition|lluvia del día|rainfall|mm|daily|escalar|RUFAS\biophysical\field\soil\carbon_cycling\carbon_cycle.py:63|arg
field.soil.carbon_cycling.CarbonCycling|field.soil (LayerData)|fracción global de carbono del suelo por capa|layer.soil_overall_carbon_fraction|unidad no declarada|daily|escalar (por capa)|RUFAS\biophysical\field\soil\carbon_cycling\carbon_cycle.py:91|estado: SoilData.soil_layers[i].soil_overall_carbon_fraction
field.field.Field|field.soil.nitrogen_cycling.NitrogenCycling|tamaño del campo|field_size|ha|daily|escalar|RUFAS\biophysical\field\field\field.py:1539|arg
field.soil.nitrogen_cycling.NitrogenCycling|field.soil.nitrogen_cycling.leaching_runoff_erosion|tamaño del campo|field_size|ha|daily|escalar|RUFAS\biophysical\field\soil\nitrogen_cycling\nitrogen_cycling.py:58|arg
field.soil.nitrogen_cycling.NitrogenCycling|field.soil.nitrogen_cycling.nitrification_volatilization|disparo de nitrificación/volatilización|do_daily_nitrification_and_volatilization|unidad no declarada|daily|—|RUFAS\biophysical\field\soil\nitrogen_cycling\nitrogen_cycling.py:59|estado: SoilData.soil_layers
field.soil.nitrogen_cycling.NitrogenCycling|field.soil.nitrogen_cycling.denitrification|tamaño del campo|field_size|ha|daily|escalar|RUFAS\biophysical\field\soil\nitrogen_cycling\nitrogen_cycling.py:60|arg
field.soil.nitrogen_cycling.NitrogenCycling|field.soil.nitrogen_cycling.mineralization_decomp|disparo de mineralización/descomposición|mineralize_and_decompose_nitrogen|unidad no declarada|daily|—|RUFAS\biophysical\field\soil\nitrogen_cycling\nitrogen_cycling.py:61|estado: SoilData.soil_layers
field.soil.nitrogen_cycling.NitrogenCycling|field.soil.nitrogen_cycling.humus_mineralization|disparo de mineralización de humus|mineralize_organic_nitrogen|unidad no declarada|daily|—|RUFAS\biophysical\field\soil\nitrogen_cycling\nitrogen_cycling.py:62|estado: SoilData.soil_layers
field.field.Field|field.soil.evaporation.Evaporation|evaporación máxima del suelo|max_soil_evaporation|mm|daily|escalar|RUFAS\biophysical\field\field\field.py:1570|arg
field.soil.evaporation.Evaporation|field.soil (LayerData)|agua evaporada por capa reseteada|evaporated_water_content|unidad no declarada|daily|array (vectorizado por capa)|RUFAS\biophysical\field\soil\evaporation.py:48|estado: SoilData.soil_layers[*].evaporated_water_content
field.soil.evaporation.Evaporation|field.soil (SoilData)|agua evaporada del perfil|water_evaporated|mm|daily|escalar|RUFAS\biophysical\field\soil\evaporation.py:76|estado: SoilData.water_evaporated
field.soil.evaporation.Evaporation|field.soil (SoilData)|evaporación anual acumulada|annual_soil_evaporation_total|mm|daily|escalar|RUFAS\biophysical\field\soil\evaporation.py:77|estado: SoilData.annual_soil_evaporation_total
field.soil (SoilData)|field.field.Field|agua sublimada descontada de la demanda|self.soil.data.water_sublimated|mm|daily|escalar|RUFAS\biophysical\field\field\field.py:1566|estado: SoilData.water_sublimated
field.soil (SoilData)|field.field.Field|agua evaporada descontada de la demanda|self.soil.data.water_evaporated|mm|daily|escalar|RUFAS\biophysical\field\field\field.py:1571|estado: SoilData.water_evaporated
field.field.Field|field.crop.WaterDynamics|transpiración máxima del cultivo|max_transpiration|mm|daily|escalar|RUFAS\biophysical\field\field\field.py:1544 → crop.py:262|estado: CropData.max_transpiration
field.crop (CropData)|field.field.Field|transpiración máxima ponderada por cobertura|crop.data.max_transpiration, crop.data.field_proportion|mm / unitless|daily|escalar|RUFAS\biophysical\field\field\field.py:1545-1546|estado: CropData
field.field.Field|field.crop.Crop|evaporación real y demanda evapotranspirativa total|actual_evaporation, full_evapotranspirative_demand|mm|daily|escalar|RUFAS\biophysical\field\field\field.py:1576|arg
field.field.Field|field.crop.Crop|condiciones del día, datos de campo y datos de suelo|current_conditions, field_data, soil_data|unidad no declarada|daily|dataclass CurrentDayConditions / FieldData / SoilData|RUFAS\biophysical\field\field\field.py:1464|arg
field.crop.Crop|field.crop.heat_units.HeatUnits|temperaturas media/mín/máx del aire|mean_air_temperature, min_air_temperature, max_air_temperature|°C|daily|escalar|RUFAS\biophysical\field\crop\crop.py:146-150|arg
field.crop.Crop|field.crop.nitrogen_uptake.NitrogenUptake|datos de suelo|soil_data|unidad no declarada|daily|dataclass SoilData|RUFAS\biophysical\field\crop\crop.py:152|arg
field.soil (LayerData)|field.crop.nitrogen_uptake.NitrogenUptake|nitratos por capa de suelo|layer_nutrient ("nitrate_content")|kg/ha|daily|list[float]|RUFAS\biophysical\field\crop\non_water_uptake.py:101|arg (vía SoilData.get_vectorized_layer_attribute)
field.crop.nitrogen_uptake.NitrogenUptake|field.soil (LayerData)|nitratos restantes tras absorción radicular|layer_nutrient escrito con set_vectorized_layer_attribute|kg/ha|daily|list[float]|RUFAS\biophysical\field\crop\non_water_uptake.py:133|estado: SoilData.soil_layers[*].nitrate_content
field.crop.nitrogen_uptake.NitrogenUptake|field.crop (CropData)|nitrógeno almacenado en biomasa|crop_data.nitrogen|kg/ha|daily|escalar|RUFAS\biophysical\field\crop\nitrogen_uptake.py:131-135|estado: CropData.nitrogen
field.soil (SoilData)|field.crop.nitrogen_uptake.NitrogenUptake|factor de agua del suelo para fijación de N|soil_data.soil_water_factor|unidad no declarada|daily|escalar|RUFAS\biophysical\field\crop\nitrogen_uptake.py:128|estado: SoilData.soil_water_factor
field.crop.Crop|field.crop.phosphorus_uptake.PhosphorusUptake|datos de suelo|soil_data|unidad no declarada|daily|dataclass SoilData|RUFAS\biophysical\field\crop\crop.py:153|arg
field.crop.phosphorus_uptake.PhosphorusUptake|field.soil (LayerData)|fósforo lábil restante tras absorción|layer_nutrient escrito con set_vectorized_layer_attribute|kg/ha|daily|list[float]|RUFAS\biophysical\field\crop\non_water_uptake.py:133 (vía phosphorus_uptake.py:71)|estado: SoilData.soil_layers[*]
field.crop.non_water_uptake.NonWaterUptake|field.crop (CropData)|capas de suelo accesibles a raíces|total_soil_layers, accessible_soil_layers, inaccessible_soil_layers|unidad no declarada|daily|escalar|RUFAS\biophysical\field\crop\non_water_uptake.py:292-296|estado: CropData
field.crop.Crop|field.crop.water_uptake.WaterUptake|datos de suelo|soil_data|unidad no declarada|daily|dataclass SoilData|RUFAS\biophysical\field\crop\crop.py:183|arg
field.soil (LayerData)|field.crop.water_uptake.WaterUptake|profundidades, contenido y capacidad de agua, punto de marchitez por capa|top_depth, bottom_depth, water_content, available_water_capacity, wilting_point_content|unidad no declarada|daily|list[float]|RUFAS\biophysical\field\crop\water_uptake.py:81-85|arg (vía SoilData.get_vectorized_layer_attribute)
field.crop.water_uptake.WaterUptake|field.soil (LayerData)|agua restante por capa tras absorción del cultivo|water_content|unidad no declarada|daily|list[float]|RUFAS\biophysical\field\crop\water_uptake.py:154|estado: SoilData.soil_layers[*].water_content
field.crop.Crop|field.crop (CropData)|absorción de agua diaria y acumulada reseteadas fuera de temporada|cumulative_evaporation, cumulative_transpiration, cumulative_potential_evapotranspiration, cumulative_water_uptake|mm|daily|escalar|RUFAS\biophysical\field\crop\crop.py:190-193|estado: CropData
field.field.Field|field.crop.Crop|profundidad del fondo del perfil de suelo|bottom_layer_depth|mm|per-event (siembra)|escalar|RUFAS\biophysical\field\field\field.py:1264-1265|arg
field.crop.Crop|field.crop (CropData)|profundidad radicular máxima limitada por el perfil|data.max_root_depth|mm|per-event (siembra)|escalar|RUFAS\biophysical\field\crop\crop.py:375|estado: CropData.max_root_depth
field.field.Field|field.crop.Crop|proporción de campo por cultivo|crop.data.field_proportion|unidad no declarada|daily|escalar|RUFAS\biophysical\field\field\field.py:1411|estado: CropData.field_proportion
field.field.Field|field.crop.Crop|duración del día, umbral de dormancia, lluvia, suelo|daylength, dormancy_threshold_daylength, rainfall, soil_data, soil|hours / hours / mm|daily|escalar + dataclass|RUFAS\biophysical\field\field\field.py:1425-1427|arg
field.crop.Crop|field.soil.carbon_cycling.residue_partition|lluvia al entrar en dormancia (añade residuo a pools)|rainfall|mm|per-event|escalar|RUFAS\biophysical\field\crop\crop.py:304|arg
field.field.Field|field.crop.crop_management.CropManagement|operación de cosecha, nombre y tamaño de campo, tiempo, datos de suelo|harvest_operation, field_name, field_size, time, soil_data|ha (field_size)|per-event|escalar + dataclass SoilData|RUFAS\biophysical\field\field\field.py:1383-1389 y 1189-1195|arg
field.crop.crop_management.CropManagement|field.soil (SoilData)|nitrógeno del residuo de cosecha|soil_data.crop_yield_nitrogen|unidad no declarada|per-event|escalar|RUFAS\biophysical\field\crop\crop_management.py:452|estado: SoilData.crop_yield_nitrogen
field.crop.crop_management.CropManagement|field.soil (SoilData)|composición de lignina del residuo vegetal|soil_data.plant_residue_lignin_composition|unidad no declarada|per-event|escalar|RUFAS\biophysical\field\crop\crop_management.py:453-455|estado: SoilData.plant_residue_lignin_composition
field.crop.crop_management.CropManagement|field.soil (LayerData)|residuo vegetal en la capa superficial|soil_layers[0].plant_residue|unidad no declarada|per-event|escalar|RUFAS\biophysical\field\crop\crop_management.py:459|estado: SoilData.soil_layers[0].plant_residue
field.crop.crop_management.CropManagement|field.soil (LayerData)|nitrógeno orgánico fresco del residuo|soil_layers[0].fresh_organic_nitrogen_content|unidad no declarada|per-event|escalar|RUFAS\biophysical\field\crop\crop_management.py:460|estado: SoilData.soil_layers[0].fresh_organic_nitrogen_content
field.crop.crop_management.CropManagement|field.soil (LayerData)|fósforo inorgánico lábil del residuo|soil_layers[0].labile_inorganic_phosphorus_content|unidad no declarada|per-event|escalar|RUFAS\biophysical\field\crop\crop_management.py:461|estado: SoilData.soil_layers[0].labile_inorganic_phosphorus_content
field.crop.crop_management.CropManagement|field.soil (LayerData)|residuo y nutrientes repartidos en profundidad al matar el cultivo|_distribute_residue_nutrients|unidad no declarada|per-event|escalar (por capa)|RUFAS\biophysical\field\crop\crop_management.py:466-493|estado: SoilData.soil_layers[*]
field.field.Field|field.soil.carbon_cycling.residue_partition|lluvia tras cosecha programada|current_conditions.rainfall|mm|per-event|escalar|RUFAS\biophysical\field\field\field.py:1390|arg
field.field.Field|field.soil.carbon_cycling.residue_partition|lluvia tras cosecha por unidades de calor|rainfall|mm|per-event|escalar|RUFAS\biophysical\field\field\field.py:1196|arg
field.soil.carbon_cycling.residue_partition|field.soil (SoilData)|lignina, relación lignina/N y fracción metabólica del residuo|plant_residue_lignin_composition, plant_lignin_nitrogen_ratio, plant_residue_metabolic_fraction|unidad no declarada|per-event|escalar|RUFAS\biophysical\field\soil\carbon_cycling\residue_partition.py:45-55|estado: SoilData
field.crop.crop_management.CropManagement|field (HarvestedCrop)|cultivo cosechado con masa y calidad|harvested_crop|kg (dry_matter_mass), percent (resto)|per-event|dataclass HarvestedCrop|RUFAS\biophysical\field\crop\crop_management.py:346-362|arg
field.crop.crop_management.CropManagement|OutputManager|rendimiento de cosecha (dry_yield, crop, harvest_year/day, field_name, harvest_type)|harvest_yield|DRY_KILOGRAMS_PER_HECTARE y otros|per-event|dict|RUFAS\biophysical\field\crop\crop_management.py:365-393|estado: OutputManager
field.field.Field|field.manager.FieldManager|lista de cultivos cosechados hoy|harvested_crops|unidad no declarada|daily|list[HarvestedCrop]|RUFAS\biophysical\field\field\field.py:205,210|arg
field.manager.FieldManager|simulation_engine|cultivos cosechados de todos los campos|harvested_crops|unidad no declarada|daily|list[HarvestedCrop]|RUFAS\biophysical\field\manager\field_manager.py:108,111|arg
simulation_engine|feed_storage.FeedManager|cultivo cosechado a almacenar|crop, simulation_day|unidad no declarada|daily|dataclass HarvestedCrop|RUFAS\simulation_engine.py:449|arg
feed_storage.FeedManager|feed_storage.Storage|cultivo cosechado asignado a un silo/almacén|harvested_crop|unidad no declarada|daily|dataclass HarvestedCrop|RUFAS\biophysical\feed_storage\feed_manager.py:322 → storage.py:134|arg
field.manager.FieldManager|simulation_engine|próximas fechas de cosecha por cultivo|next_harvest_dates|unidad no declarada (date)|daily|dict[str, date]|RUFAS\biophysical\field\manager\field_manager.py:147|arg
simulation_engine|feed_storage.FeedManager|calendario de cosechas traducido a IDs RuFaS|next_harvest_dates_with_rufas_ids|unidad no declarada|daily|dict[RUFAS_ID, date]|RUFAS\simulation_engine.py:506|arg
weather|feed_storage.FeedManager|condiciones meteorológicas para degradación de forrajes|weather|unidad no declarada|per-event (intervalo de 30 días)|objeto Weather|RUFAS\simulation_engine.py:519 → feed_manager.py:349|arg
weather|feed_storage.FeedManager|meteorología para proyectar inventario|weather|unidad no declarada|daily|objeto Weather|RUFAS\simulation_engine.py:504 → feed_manager.py:532|arg
feed_storage.FeedManager|animal.HerdManager|inventario total proyectado de alimentos|total_projected_inventory|kg|daily|dataclass TotalInventory|RUFAS\simulation_engine.py:503,527-529|arg
animal.HerdManager|feed_storage.FeedManager|alimentos que idealmente deberían comprarse|ideal_feeds_to_purchase|kg|daily|dataclass IdealFeeds|RUFAS\simulation_engine.py:508-513|arg
weather|animal.HerdManager|temperatura media del aire para formular raciones|current_temperature|degrees C|per-event (intervalo de ración)|escalar|RUFAS\simulation_engine.py:550-556|arg
animal.HerdManager|feed_storage.FeedManager|ración solicitada tras formulación|requested_feed|kg|per-event (intervalo de ración)|dataclass RequestedFeed|RUFAS\simulation_engine.py:551,558|arg
weather|animal.HerdManager|temperatura media para requisitos nutricionales de los corrales|weather.get_current_day_conditions(time).mean_air_temperature|degrees C|daily|escalar|RUFAS\biophysical\animal\herd_manager.py:1657-1659|arg
weather|animal.HerdManager|condiciones del día para reestructurar el rebaño|current_day_conditions|unidad no declarada|daily|dataclass CurrentDayConditions|RUFAS\biophysical\animal\herd_manager.py:743|arg
weather|animal.Pen|temperatura media para requisitos nutricionales al insertar animal|current_day_conditions.mean_air_temperature|degrees C|per-event|escalar|RUFAS\biophysical\animal\herd_manager.py:1219|arg
weather|animal.HerdManager|temperatura media para reformular la ración de un corral|current_temperature|degrees C|per-event|escalar|RUFAS\biophysical\animal\herd_manager.py:1232|arg
animal.HerdManager|feed_storage.FeedManager|petición diaria de alimento del rebaño|requested_feed|kg|daily|dataclass RequestedFeed|RUFAS\simulation_engine.py:581-586|arg
feed_storage.FeedManager|animal / EEE.EmissionsEstimator|alimento comprado realmente suministrado|daily_feeds_fed.purchased|kg|daily|dataclass FeedFulfillmentResults (dict[RUFAS_ID, float])|RUFAS\simulation_engine.py:583-591|arg
simulation_engine|EEE.EmissionsEstimator|alimento comprado del día para emisiones|daily_purchased_feeds_fed|kg|daily|dict[int, float]|RUFAS\simulation_engine.py:626|arg
animal.Animal|animal.digestive_system.DigestiveSystem|entradas digestivas (peso, nutrientes, P, leche)|digestive_system_inputs|unidad no declarada|daily|dataclass DigestiveSystemInputs|RUFAS\biophysical\animal\animal.py:1627-1641|arg
animal.digestive_system.DigestiveSystem|animal.digestive_system.ManureExcretionCalculator|peso vivo, P fecal y urinario, nutrientes|body_weight, fecal_phosphorus, urine_phosphorus_required, nutrients|unidad no declarada|daily|escalar + dataclass|RUFAS\biophysical\animal\digestive_system\digestive_system.py:84-89 (ternera), 129-134 (novilla), 143-153 (vaca)|arg
animal.digestive_system.ManureExcretionCalculator|animal.digestive_system.DigestiveSystem|excreciones de estiércol del animal|manure_excretion (AnimalManureExcretions)|kg (masas), g (P, K)|daily|dataclass AnimalManureExcretions|RUFAS\biophysical\animal\digestive_system\digestive_system.py:87,110,137|estado: DigestiveSystem.manure_excretion
animal.digestive_system.DigestiveSystem|animal.Pen|suma de excreciones de todos los animales del corral|total_manure_excretion|kg / g|daily|dataclass AnimalManureExcretions|RUFAS\biophysical\animal\pen.py:287-290|estado: Animal.digestive_system.manure_excretion
animal.Pen|manure (ManureStream)|agua del estiércol (masa menos sólidos totales)|water|kg|daily|escalar en ManureStream|RUFAS\biophysical\animal\pen.py:721|arg
animal.Pen|manure (ManureStream)|nitrógeno amoniacal total|ammoniacal_nitrogen|kg|daily|escalar en ManureStream|RUFAS\biophysical\animal\pen.py:722|arg
animal.Pen|manure (ManureStream)|nitrógeno total del estiércol|nitrogen|kg|daily|escalar en ManureStream|RUFAS\biophysical\animal\pen.py:723|arg
animal.Pen|manure (ManureStream)|fósforo del estiércol|phosphorus|kg (convertido desde g)|daily|escalar en ManureStream|RUFAS\biophysical\animal\pen.py:724|arg
animal.Pen|manure (ManureStream)|potasio del estiércol|potassium|kg (convertido desde g)|daily|escalar en ManureStream|RUFAS\biophysical\animal\pen.py:725|arg
animal.Pen|manure (ManureStream)|sólidos volátiles degradables y no degradables|degradable_volatile_solids, non_degradable_volatile_solids|kg|daily|escalar en ManureStream|RUFAS\biophysical\animal\pen.py:727-728|arg
animal.Pen|manure (ManureStream)|sólidos totales|total_solids|kg|daily|escalar en ManureStream|RUFAS\biophysical\animal\pen.py:729|arg
animal.Pen|manure (ManureStream)|volumen del flujo de estiércol|volume|m^3|daily|escalar en ManureStream|RUFAS\biophysical\animal\pen.py:730|arg
animal.Pen|manure (ManureStream)|potencial de producción de metano|methane_production_potential|m^3 metano / kg sólidos volátiles|daily|escalar en ManureStream|RUFAS\biophysical\animal\pen.py:731|arg
animal.Pen|manure (PenManureData)|nº de animales, superficie de deposición, tipo de corral, masa y N de orina|PenManureData(...)|animals / m^2 / kg|daily|dataclass PenManureData|RUFAS\biophysical\animal\pen.py:711-718|arg
animal.Pen|manure.ManureManager|primer procesador asignado a cada flujo|pen_manure_data.first_processor|unidad no declarada|daily|str|RUFAS\biophysical\animal\pen.py:654 (general), 767 (parlor)|estado: ManureStream.pen_manure_data.first_processor
animal.bedding.Bedding|manure (ManureStream)|masa y volumen de cama añadidos al flujo|total_bedding_mass, total_bedding_volume|kg / m^3|daily|escalar en PenManureData|RUFAS\biophysical\animal\pen.py:874-876|estado: ManureStream.pen_manure_data (set_bedding_mass_and_volume)
animal.bedding.Bedding|manure (ManureStream)|agua, P, ceniza y sólidos de la cama|water, phosphorus, ash, total_solids, volume, bedding_non_degradable_volatile_solids|kg / m^3|daily|escalar en ManureStream|RUFAS\biophysical\animal\pen.py:882-901|arg
animal.Pen|animal.HerdManager|diccionario de flujos de estiércol por corral|animal_manure_streams|unidad no declarada|daily|dict[str, ManureStream]|RUFAS\biophysical\animal\pen.py:659 → herd_manager.py:757|arg
animal.HerdManager|simulation_engine|todos los flujos de estiércol del rebaño|herd_manager_output / all_manure_data|unidad no declarada|daily|dict[str, ManureStream]|RUFAS\biophysical\animal\herd_manager.py:889 → simulation_engine.py:575|arg
simulation_engine|manure.ManureManager|flujos de estiércol diarios + condiciones del día|daily_manure_data, current_day_conditions|unidad no declarada|daily|dict[str, ManureStream] + CurrentDayConditions|RUFAS\simulation_engine.py:611-613|arg
manure.ManureManager|manure.processor.Processor (primer procesador)|flujo de estiércol entrante|stream|unidad no declarada|daily|dataclass ManureStream|RUFAS\biophysical\manure\manure_manager.py:125|arg
manure.ManureManager|manure.processor.Processor|flujo procesado enrutado al destino según matriz de adyacencia|stream / split_stream|unidad no declarada|daily|dataclass ManureStream|RUFAS\biophysical\manure\manure_manager.py:140,142-143|arg
weather|manure.handler.Handler|temperatura media del aire → temperatura del establo|conditions.mean_air_temperature|degrees C|daily|escalar|RUFAS\biophysical\manure\handler\handler.py:125|arg
manure.handler.Handler|manure.storage / manure.separator|flujo de salida con agua de limpieza y N tras emisión de amoníaco|output_stream|kg / m^3|daily|dataclass ManureStream|RUFAS\biophysical\manure\handler\handler.py:187-201,204|arg
manure.handler.Handler|manure (ManureStream)|borrado de los datos del corral en el flujo|pen_manure_data=None|unidad no declarada|daily|—|RUFAS\biophysical\manure\handler\handler.py:199|arg
manure.separator.Separator|manure.storage|fracción sólida separada|solid_manure_stream|kg / m^3|daily|dataclass ManureStream|RUFAS\biophysical\manure\separator\separator.py:168-185,232|arg
manure.separator.Separator|manure.storage|fracción líquida separada|liquid_manure_stream|kg / m^3|daily|dataclass ManureStream|RUFAS\biophysical\manure\separator\separator.py:209-227,232|arg
weather|manure.storage.SlurryStorageOutdoor|precipitación añadida al volumen y agua del depósito|current_day_conditions.precipitation|mm (convertido a m)|daily|escalar|RUFAS\biophysical\manure\storage\slurry_storage_outdoor.py:58-60|estado: Storage._received_manure.volume/.water
weather|manure.storage.AnaerobicLagoon|precipitación añadida al volumen del lagunaje|current_day_conditions.precipitation|mm (convertido a m)|daily|escalar|RUFAS\biophysical\manure\storage\anaerobic_lagoon.py:74|estado: Storage._received_manure
weather|manure.storage.Composting|temperatura media anual del aire|current_day_conditions.annual_mean_air_temperature|degrees C|daily|escalar|RUFAS\biophysical\manure\storage\composting.py:107|arg
weather|manure.storage.Composting|temperatura media del aire del día|current_day_conditions.mean_air_temperature|degrees C|daily|escalar|RUFAS\biophysical\manure\storage\composting.py:108|arg
weather|manure.storage.OpenLot|temperatura media del aire para emisión de metano|current_day_conditions.mean_air_temperature|degrees C|daily|escalar|RUFAS\biophysical\manure\storage\open_lot.py:52|arg
weather|manure.storage.BeddedPack|temperatura media anual del aire|current_day_conditions.annual_mean_air_temperature|degrees C|daily|escalar|RUFAS\biophysical\manure\storage\bedded_pack.py:80|arg
manure.storage.Storage|manure.storage.Storage|estiércol recibido acumulado en el almacén|stored_manure += _received_manure|kg / m^3|daily|dataclass ManureStream|RUFAS\biophysical\manure\storage\storage.py:206|estado: Storage.stored_manure
manure.storage.Storage|manure.ManureManager|flujo vaciado que pasa al siguiente procesador|manure_to_be_returned["manure"]|kg / m^3|per-event (día de vaciado)|dict[str, ManureStream]|RUFAS\biophysical\manure\storage\storage.py:219-231|arg
manure.storage.Storage|manure.ManureNutrientManager|N, P, K, masa y materia seca almacenados|ManureNutrients(...)|kg|daily|dataclass ManureNutrients|RUFAS\biophysical\manure\manure_manager.py:155-164|arg
manure.ManureNutrientManager|manure.ManureNutrientManager|pools de nutrientes por tipo de estiércol|nutrients_by_manure_category|kg|daily|dict[ManureType, ManureNutrients]|RUFAS\biophysical\manure\manure_nutrient_manager.py:48|estado: ManureNutrientManager.nutrients_by_manure_category
field.field.Field|manure (NutrientRequest)|petición de N y P de estiércol con tipo y flag de suplemento|NutrientRequest(nitrogen, phosphorus, manure_type, use_supplemental_manure)|kg|per-event|dataclass NutrientRequest|RUFAS\biophysical\field\field\field.py:1120-1125|arg
field.field.Field|field.manager.FieldManager|evento de estiércol acoplado a su petición de nutrientes|ManureEventNutrientRequest(field_name, event, manure_request)|unidad no declarada|per-event|NamedTuple|RUFAS\biophysical\field\field\field.py:1084-1085|arg
field.manager.FieldManager|simulation_engine|peticiones de estiércol del campo|manure_requests|unidad no declarada|daily|list[ManureEventNutrientRequest]|RUFAS\biophysical\field\manager\field_manager.py:643-644|arg
simulation_engine|manure.ManureManager|petición de nutrientes (ruta con módulo de estiércol activo)|manure_request|kg|per-event|dataclass NutrientRequest|RUFAS\simulation_engine.py:440|arg — AMBIGÜEDAD: ver siguiente línea
simulation_engine|manure.FieldManureSupplier|petición de nutrientes (ruta sin módulo de estiércol)|manure_request|kg|per-event|dataclass NutrientRequest|RUFAS\simulation_engine.py:442|arg — AMBIGÜEDAD: ruta alternativa según simulate_manure
manure.ManureNutrientManager|manure.ManureManager|resultado de la petición (N, P, masa total, fracciones, materia seca)|request_result|kg / unitless|per-event|dataclass NutrientRequestResults|RUFAS\biophysical\manure\manure_manager.py:891|arg
manure.ManureManager|manure.storage.Storage|retirada proporcional de nutrientes de cada almacén|processor.stored_manure|kg|per-event|dataclass ManureStream|RUFAS\biophysical\manure\manure_manager.py:951-956|estado: Storage.stored_manure (reasignado con dataclasses.replace)
manure.FieldManureSupplier|manure.ManureManager|estiércol suplementario externo|supplemental_manure|kg|per-event|dataclass NutrientRequestResults|RUFAS\biophysical\manure\manure_manager.py:903,907|arg
manure.ManureManager|simulation_engine|resultados de la petición de estiércol|manure_request_results|kg|per-event|dataclass NutrientRequestResults|RUFAS\simulation_engine.py:440,443|arg
simulation_engine|field.manager.FieldManager|aplicaciones de estiércol por campo|manure_applications|unidad no declarada|daily|list[ManureEventNutrientRequestResults]|RUFAS\simulation_engine.py:416-418|arg
field.manager.FieldManager|field.field.Field|aplicaciones de estiércol filtradas para ese campo|manure_applications_for_field|unidad no declarada|daily|list[ManureEventNutrientRequestResults]|RUFAS\biophysical\field\manager\field_manager.py:102-106|arg
field.field.Field|field.field.manure_application.ManureApplication|materia seca, fracción seca, P total, cobertura, profundidad y fracción superficial|dry_matter_mass, dry_matter_fraction, total_phosphorus_mass, field_coverage, application_depth, surface_remainder_fraction|kg / unitless / kg / unitless / mm / unitless|per-event|escalar|RUFAS\biophysical\field\field\field.py:649-663|arg
field.field.Field|field.field.manure_application.ManureApplication|fracciones de N inorgánico, amonio y N orgánico|inorganic_nitrogen_fraction, ammonium_fraction, organic_nitrogen_fraction|unitless|per-event|escalar|RUFAS\biophysical\field\field\field.py:657-661|arg
field.field.Field|field.field.manure_application.ManureApplication|fracción de P inorgánico extraíble en agua|water_extractable_inorganic_phosphorus_fraction|unitless|per-event|escalar|RUFAS\biophysical\field\field\field.py:662|arg
field.field.manure_application.ManureApplication|field.soil (SoilData)|pools de P del estiércol de máquina|machine_manure.water_extractable_inorganic/organic_phosphorus, stable_inorganic/organic_phosphorus|kg|per-event|escalar|RUFAS\biophysical\field\field\manure_application.py:209-229|estado: SoilData.machine_manure
field.field.manure_application.ManureApplication|field.soil (LayerData)|P lábil y P activo de purín líquido infiltrado|add_to_labile_phosphorus, add_to_active_phosphorus|kg|per-event|escalar|RUFAS\biophysical\field\field\manure_application.py:243,251|estado: SoilData.soil_layers[0]
field.field.manure_application.ManureApplication|field.soil (SoilData)|masa seca, factor de humedad y cobertura del pool de estiércol|machine_manure.manure_dry_mass/.manure_moisture_factor/.manure_field_coverage|kg / unitless / unitless|per-event|escalar|RUFAS\biophysical\field\field\manure_application.py:267-269|estado: SoilData.machine_manure
field.field.manure_application.ManureApplication|field.soil (LayerData)|nitratos añadidos por estiércol|soil_layers[i].nitrate_content|kg/ha (masa/field_size)|per-event|escalar|RUFAS\biophysical\field\field\manure_application.py:368|estado: SoilData.soil_layers[i].nitrate_content
field.field.manure_application.ManureApplication|field.soil (LayerData)|amonio añadido por estiércol|soil_layers[i].ammonium_content|kg/ha|per-event|escalar|RUFAS\biophysical\field\field\manure_application.py:369|estado: SoilData.soil_layers[i].ammonium_content
field.field.manure_application.ManureApplication|field.soil (LayerData)|N orgánico estable y fresco añadidos|stable_organic_nitrogen_content, fresh_organic_nitrogen_content|kg/ha|per-event|escalar|RUFAS\biophysical\field\field\manure_application.py:370-371|estado: SoilData.soil_layers[i]
field.field.manure_application.ManureApplication|field.soil (LayerData)|P y N de aplicación subsuperficial repartidos por factor de profundidad|_apply_subsurface_manure|kg|per-event|escalar (por capa)|RUFAS\biophysical\field\field\manure_application.py:441-455|estado: SoilData.soil_layers[*]
manure (NutrientRequestResults)|field.field.Field|agua del purín líquido aplicada al campo|water_amount_in_l → water_amount_in_mm|liters → mm|per-event|escalar|RUFAS\biophysical\field\field\field.py:948-953|estado: FieldData.manure_water
field.field.Field|field.field.fertilizer_application.FertilizerApplication|P, N, fracción de amonio, profundidad, fracción superficial, tamaño de campo|phosphorus_applied, nitrogen_applied, ammonium_fraction, application_depth, surface_remainder_fraction, field_size|kg / kg / unitless / mm / unitless / ha|per-event|escalar|RUFAS\biophysical\field\field\field.py:323-330|arg
field.field.fertilizer_application.FertilizerApplication|field.soil.phosphorus_cycling.fertilizer|P de fertilizante en superficie|add_fertilizer_phosphorus|kg|per-event|escalar|RUFAS\biophysical\field\field\fertilizer_application.py:72-74|arg
field.field.fertilizer_application.FertilizerApplication|field.soil (LayerData)|nitratos y amonio de fertilizante en la capa superficial|soil_layers[0].nitrate_content, .ammonium_content|kg/ha|per-event|escalar|RUFAS\biophysical\field\field\fertilizer_application.py:79-80|estado: SoilData.soil_layers[0]
field.field.Field|field.field.tillage_application.TillageApplication|profundidad, fracción de incorporación, fracción de mezcla, implemento|tillage_depth, incorporation_fraction, mixing_fraction, implement|mm / unitless / unitless|per-event|escalar + enum TillageImplement|RUFAS\biophysical\field\field\field.py:1057-1064|arg
field.field.tillage_application.TillageApplication|field.soil (SoilData)|pools de P incorporados y mezclados entre capas|available_phosphorus_pool, recalcitrant_phosphorus_pool, grazing_manure, machine_manure|kg|per-event|escalar|RUFAS\biophysical\field\field\tillage_application.py:115-131|estado: SoilData
field.manager.FieldDataReporter|OutputManager|emisiones de óxido nitroso por capa|nitrous_oxide_emissions|KILOGRAMS_PER_HECTARE|daily|escalar (por capa)|RUFAS\biophysical\field\manager\field_data_reporter.py:1184-1192|estado: OutputManager
field.manager.FieldDataReporter|OutputManager|emisiones de amoníaco por capa|ammonia_emissions|KILOGRAMS_PER_HECTARE|daily|escalar (por capa)|RUFAS\biophysical\field\manager\field_data_reporter.py:1206-1214|estado: OutputManager
field.field.Field|OutputManager|aplicación de fertilizante (masa, N, P, K, profundidad, tamaño de campo, % arcilla)|fertilizer_application|KILOGRAMS / MILLIMETERS / HECTARE / PERCENT|per-event|dict|RUFAS\biophysical\field\field\field.py:520|estado: OutputManager
field.field.Field|OutputManager|aplicación de estiércol (materia seca, N, P, profundidad, cobertura)|manure_application / manure_request|DRY_KILOGRAMS / KILOGRAMS / MILLIMETERS|per-event|dict|RUFAS\biophysical\field\field\field.py:924|estado: OutputManager
field.field.Field|OutputManager|siembra de cultivo (crop, field_size, % arcilla, año, día)|crop_planting|UNITLESS / HECTARE / PERCENT|per-event|dict|RUFAS\biophysical\field\field\field.py:1321|estado: OutputManager
weather|OutputManager|precipitación, lluvia, nieve, temperaturas, radiación, riego|precipitation, rainfall, snowfall, maximum/minimum/average_temperature, radiation, irrigation|MILLIMETERS / DEGREES_CELSIUS / MEGAJOULES_PER_SQUARE_METER|daily|escalar|RUFAS\weather.py:241-274|estado: OutputManager
OutputManager|EEE.EnergyEstimator|aplicaciones de fertilizante leídas de vuelta (mass, depth, field_size, clay, year, day, field_name)|CROP_AND_SOIL_FILTERS[FERTILIZER_APPLICATION]|unidad no declarada|per-event (post-simulación)|dict|RUFAS\EEE\energy.py:62-74|estado: OutputManager (filter_variables_pool, energy.py:288)
OutputManager|EEE.EnergyEstimator|eventos de laboreo leídos de vuelta (tillage_depth, implement, field_size, clay)|CROP_AND_SOIL_FILTERS[TILLING]|unidad no declarada|per-event (post-simulación)|dict|RUFAS\EEE\energy.py:75-87|estado: OutputManager
OutputManager|EEE.EnergyEstimator|aplicaciones de estiércol leídas de vuelta (dry_matter_mass, dry_matter_fraction, depth)|CROP_AND_SOIL_FILTERS[MANURE_APPLICATION]|unidad no declarada|per-event (post-simulación)|dict|RUFAS\EEE\energy.py:88-101|estado: OutputManager
OutputManager|EEE.EnergyEstimator|cosechas leídas de vuelta (dry_yield, crop, harvest_year/day, harvest_type)|CROP_AND_SOIL_FILTERS[HARVEST]|unidad no declarada|per-event (post-simulación)|dict|RUFAS\EEE\energy.py:102-114|estado: OutputManager
OutputManager|EEE.EnergyEstimator|siembras leídas de vuelta (crop, field_size, clay, year, day)|CROP_AND_SOIL_FILTERS[PLANTING]|unidad no declarada|per-event (post-simulación)|dict|RUFAS\EEE\energy.py:115-118|estado: OutputManager
EEE.EnergyEstimator|EEE.Tractor|tipo de operación de campo, tamaño de tractor, implemento, rendimiento|FieldOperationEvent, tillage_implement, crop_yield|unidad no declarada|per-event (post-simulación)|escalar + enum|RUFAS\EEE\energy.py:150-160|arg
EEE.EnergyEstimator|OutputManager|consumo de diésel y métricas asociadas|diesel_consumption, herd_size_for_..., tillage_implement_for_...|unidad no declarada|annual (post-simulación)|escalar|RUFAS\EEE\energy.py:174,212-263|estado: OutputManager
OutputManager|EEE.EmissionsEstimator|rendimientos de cosecha para emisiones de forraje propio|FARMGROWN..._FILTERS["harvest_yield"]|unidad no declarada|annual (post-simulación)|dict|RUFAS\EEE\emissions.py:13-19 (leído en emissions.py:516)|estado: OutputManager
OutputManager|EEE.EmissionsEstimator|emisiones de N2O del suelo por campo|FARMGROWN..._FILTERS["nitrous_oxide_emissions"]|unidad no declarada|annual (post-simulación)|dict|RUFAS\EEE\emissions.py:20-27 (leído en emissions.py:319)|estado: OutputManager
OutputManager|EEE.EmissionsEstimator|emisiones de amoníaco del suelo por campo|FARMGROWN..._FILTERS["ammonia_emissions"]|unidad no declarada|annual (post-simulación)|dict|RUFAS\EEE\emissions.py:28-36|estado: OutputManager
OutputManager|EEE.EmissionsEstimator|N, P, K de fertilizante aplicado|FARMGROWN..._FILTERS["fertilizer_applications"]|unidad no declarada|annual (post-simulación)|dict|RUFAS\EEE\emissions.py:37-43 (leído en emissions.py:368)|estado: OutputManager
OutputManager|EEE.EmissionsEstimator|N de estiércol aplicado|FARMGROWN..._FILTERS["manure_applications"]|unidad no declarada|annual (post-simulación)|dict|RUFAS\EEE\emissions.py:44-50|estado: OutputManager
OutputManager|EEE.EmissionsEstimator|mapeo cultivo→ID de alimento (crop_received)|FARMGROWN..._FILTERS["crop_received"]|unidad no declarada|annual (post-simulación)|dict|RUFAS\EEE\emissions.py:51-60 (leído en emissions.py:467)|estado: OutputManager
OutputManager|EEE.EmissionsEstimator|deducciones de forraje propio suministrado a animales|FARMGROWN..._FILTERS["farmgrown_feed_deductions"]|unidad no declarada|annual (post-simulación)|dict|RUFAS\EEE\emissions.py:61-67 (leído en emissions.py:436)|estado: OutputManager
OutputManager|EEE.EmissionsEstimator|inventario diario de forraje propio|FARMGROWN..._FILTERS["farmgrown_feed_inventory"]|unidad no declarada|annual (post-simulación)|dict|RUFAS\EEE\emissions.py:68-72 (leído en emissions.py:758)|estado: OutputManager
EEE.EmissionsEstimator|OutputManager|emisiones/recursos diarios del forraje propio suministrado|n2o_emissions_outputs, ammonia_emissions_outputs, fertilizer_N/P/K_outputs, manure_N_outputs|unidad no declarada|annual (post-simulación)|dict (bulk)|RUFAS\EEE\emissions.py:901-946|estado: OutputManager
EEE.EmissionsEstimator|OutputManager|emisiones de alimento comprado y cambio de uso del suelo|purchased_feed_emissions, land_use_change_emissions|unidad no declarada|daily|escalar|RUFAS\EEE\emissions.py:214-215|estado: OutputManager
field.manager.FieldManager|field.soil (SoilData/LayerData)|configuración inicial del perfil de suelo (capas, pH, densidad, C org., N inicial…)|LayerData(**config_dictionary), SoilData(field_size, **config_dictionary)|mm (bottom_depth), ha (field_size); resto unidad no declarada|init|dataclass LayerData / SoilData|RUFAS\biophysical\field\manager\field_manager.py:558,630|arg
field.manager.FieldManager|field.field.Field|datos del campo, suelo y calendarios de eventos|FieldData, Soil, PlantingEvent, HarvestEvent, TillageEvent, FertilizerEvent, ManureEvent|ha (field_size), degrees (latitude)|init|dataclass + list|RUFAS\biophysical\field\manager\field_manager.py:190-199|arg
field.manager.FieldManager|field.field.Field|residuo inicial del suelo|initial_residue|kg / ha|init|escalar|RUFAS\biophysical\field\manager\field_manager.py:523,628|arg
field.field.Field|field.field.Field|reset anual de totales de suelo y campo|do_annual_reset, perform_annual_field_reset|unidad no declarada|annual|—|RUFAS\biophysical\field\field\field.py:1897-1898|estado: SoilData / FieldData
```

---

## Lagunas

What was asked for and does not exist in the code, plus what this document does **not** establish.

### A. Asked for, absent from the code

| # | Requested | Status |
|---|---|---|
| 1 | Declared units on every edge | **73 of 219 edges (33 %) have no declared unit.** Left as `unidad no declarada`; no unit inferred from a name. The soil water cascade is the worst area: `percolation.py:56, 85, 106, 109, 114` and `evaporation.py:48` move water with no unit stated anywhere in signature or docstring |
| 2 | The Open-Meteo bridge / PR #111 in RUFAS | **Not in this repo.** PR #111 is in `supabase-connector` (`42ea2f5`, 2026-07-20) and its file was deleted in PR #115 (`0493081`, 2026-07-24). What exists in the RUFAS fork is a different, unrelated prototype client under `prototype_msf/` (§6.3) |
| 3 | Snow variables from the external weather source | **None requested, anywhere.** Not in `prototype_msf/`, not in the deleted bridge. RUFAS reads no snow column either — snowfall is derived from `precip` below 0 °C (§6.4) |
| 4 | CENTURY as the carbon-model provenance | **The string "CENTURY" appears nowhere in `RUFAS/` source.** Only `decomposition.py:27` names DAYCENT, and only as a Basecamp folder path. `residue_partition.py` cites "Parton et al. 1987" for three rate constants — that *is* the CENTURY paper, but the code never names the model (§8.2) |
| 5 | "Vadas 2008" / "Vadas & Powell 2013" | **Absent from the code.** The only Vadas bib entry is `vadas2007` (`crop_and_soil.bib:542`). The 2013 attribution exists only in `prototype_msf/README.md:113` and an OpenSpec proposal |
| 6 | Subsurface / tile drainage | **Zero hits** for `drainage|tile_drain|drain` across `RUFAS/` and `tests/`. No existing code, and no extension mechanism for soil — the only plugin registry in RUFAS is manure-only (§7) |
| 7 | Animal → field grazing-manure edge | **Not found.** `ManureApplication.apply_grazing_manure` (`manure_application.py:53`) exists but has no caller from the animal module or from `Field`. The `grazing_manure` pool is read and tilled, but the edge that fills it was not located (§2.5) |
| 8 | Mass-balance closure | `SimulationEngine.annual_mass_balance` is `pass` (`simulation_engine.py:663-664`) — no such edge exists |
| 9 | Database boundaries | **None.** RUFAS reads only CSV and JSON files from `input/` |
| 10 | Weather gap filling / imputation | **None.** A missing date is a hard failure (`weather.py:342-347`) |
| 11 | Annual reset for animal / manure / feed storage | **Not found.** `simulation_engine.py:656-661` resets fields only |

### B. Ambiguities reported, deliberately not resolved

1. **Manure nutrient supplier** — `ManureManager.request_nutrients` or
   `FieldManureSupplier.request_nutrients`, chosen at runtime by `simulate_manure`
   (`simulation_engine.py:439-442`). Both edges are in the list.
2. **Two soil orderings** — `Soil.daily_soil_water_routine` (`soil.py:153-160`) versus
   `Field._cycle_water` (`field.py:1518-1576`): different sequence, different P/N/C order. The second
   is what runs; the first is what the class advertises (§3.4).
3. **`WATER_DENSITY_KG_PER_M3` = 0.000997** while its declared unit is `KILOGRAMS_PER_CUBIC_METER`
   (`user_constants.py:37`, `:55`). Reading A: dimensional bug, 1e6 under-addition of water at
   `anaerobic_lagoon.py:76`, `slurry_storage_outdoor.py:60`, `handler.py:337`. Reading B:
   compensated downstream. **Not traced far enough to choose — this one is worth closing before any
   manure-volume result is published.**
4. **`KCAL_TO_MJ = 4.184`** is labelled `MCAL_PER_MJ` in `CONSTANTS_TO_UNITS`
   (`general_constants.py:128`, `:181`) — name/unit mismatch, direction unverified.
5. **`soluble_phosphorus.py` provenance** — the `.py` says APLE only; `crop_and_soil.tex:2404` says
   "APLE and SurPhos" while citing the SurPhos paper (`vadas2007`). Both readings stated (§8.2).

### C. Limits of this document — what was *not* verified

- **The 219 edges come from a single systematic code walk.** For this document I independently
  re-opened and confirmed a sample: `weather.py:177-178`, `infiltration.py:94-99`, `pen.py:720-732`,
  `storage.py:206`, `simulation_engine.py:437-445`, plus every line cited in both bug sections
  (`infiltration.py:29`, `field.py:1519`, `soil.py:154`, `test_soil.py:65-90`, `soil_data.py:252`,
  `default.json:5724-5728`, `soil_erosion.py:339-355`). **The remaining rows were not re-verified
  one by one.** Treat the flat list as high-confidence but not line-audited in full.
- **Modules inventoried by class name only, never opened**: `data_validator.py` internals,
  `graph_generator.py`, `report_generator.py`, `task_manager.py`, `data_collection_app_updater.py`,
  `e2e_test_results_handler.py`, and the internal behaviour of most of `animal/`, `EEE/` and
  `feed_storage/`. Their edges are therefore under-represented in §2 — the animal subsystem in
  particular (22 edges) is certainly sparser in this graph than in reality.
- **Not exhaustively traced**: whether manure processors mutate `PenManureData`; the exact predicate
  of `HarvestedCrop.__post_init__` (`crop_soil_to_feed_storage_connection.py:94-174`); the call sites
  of `KCAL_TO_MJ`.
- **Units in `Field._cycle_water`**: intermediates `total_water`, `water_reaching_soil`,
  `remaining_evapotranspirative_demand` (`field.py:1504-1571`) carry **no declared unit** in the
  body. `Soil.daily_soil_water_routine` *does* declare units in its docstring (`soil.py:126-146`) —
  but that is the dead path, so the declaration documents code that never runs.
- **One reported oddity passed through without judgement**: `storage.py:223` returns
  `{"manure": replace(self.stored_manure)}` **after** `self.stored_manure = retained_stream` at
  `:222`, so it propagates the *retained* stream rather than `emitted_stream` built at `:219`.
  Reported as found; whether it is intentional was not determined.

### D. Scope boundary restated

`spatializer_v2` is **not** a RUFAS module and must not appear inside the RUFAS boundary on the
figure. It lives in `C:\Proyectos\terranimo-test\`, does not import RUFAS, and touches it only
through `adapters/rufas_to_runoff.py`, which reads a RUFAS state object from outside. Nothing under
`RUFAS/` imports it.
