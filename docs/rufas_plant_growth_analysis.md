# RUFAS plant growth model — analysis, with focus on phosphorus coupling

**Repository:** `C:\Proyectos\RuFaS-MyForageSystem`
**Branch / commit:** `research/andrea-msf-prototype` @ `a8da114`
**Scope:** `RUFAS/biophysical/field/crop/` — 18 modules, 5,140 lines
**Method:** AST parsing and targeted reads. No RUFAS module imported, no RUFAS code executed.
**Companions:** `docs/rufas_architecture_map.md` §4.5, `docs/rufas_phosphorus_deep_dive.md`

**Context carried in:** the P→N coupling in `nitrogen_cycling/mineralization_decomp.py` is dead
computation (`return 1`, issue #2990), and `FieldData.simulate_phosphorus_stress` already exists.
Both are re-verified here from the crop side.

---

## 1. Where the plant growth model lives

**Package:** `RUFAS/biophysical/field/crop/` — 18 modules, 19 classes.
**Main file:** `RUFAS/biophysical/field/crop/crop.py` (375 lines).
**Main class:** `Crop`.
**Principal method:** `perform_daily_crop_update(current_conditions, field_data, soil_data, time)`.

`Crop` is an aggregator, not a calculator — the growth mathematics is distributed across sibling
modules that it owns and sequences:

| Module | LOC | Class | Role in growth |
| --- | ---: | --- | --- |
| `non_water_uptake.py` | 893 | `NonWaterUptake` | shared N/P uptake machinery — largest module in the package |
| `crop_management.py` | 683 | `CropManagement` | harvest, yield, residue return |
| `crop_data.py` | 447 | `CropData`, `PlantCategory` | all crop state |
| `water_uptake.py` | 453 | `WaterUptake` | water uptake by layer |
| `leaf_area_index.py` | 447 | `LeafAreaIndex` | canopy growth |
| `crop.py` | 375 | `Crop` | **the aggregator** |
| `nitrogen_uptake.py` | 332 | `NitrogenUptake` | N uptake |
| `growth_constraints.py` | 270 | `GrowthConstraints` | **stress → growth factor** |
| `heat_units.py` | 224 | `HeatUnits` | phenology |
| `biomass_allocation.py` | 220 | `BiomassAllocation` | **growth factor → biomass** |
| `water_dynamics.py` | 195 | `WaterDynamics` | canopy water |
| `crop_data_factory.py` | 182 | `CropDataFactory`, `CropConfiguration` | crop presets |
| `dormancy.py` | 140 | `Dormancy` | dormancy thresholds |
| `root_development.py` | 103 | `RootDevelopment` | rooting depth |
| `phosphorus_uptake.py` | 90 | `PhosphorusUptake` | **P uptake** |
| `nutrient_uptake.py` | 70 | `NutrientUptake` (ABC) | abstract base |
| `harvest_operations.py` | 16 | `HarvestOperation` (Enum) | operation labels |

Uptake class hierarchy:

```
NutrientUptake (ABC, nutrient_uptake.py:6)
├── WaterUptake            (water_uptake.py:9)
└── NonWaterUptake         (non_water_uptake.py:10)
    ├── NitrogenUptake     (nitrogen_uptake.py:7)
    └── PhosphorusUptake   (phosphorus_uptake.py:10)
```

N and P share **one** implementation (`NonWaterUptake`), parameterised by a nutrient-name string.
Water is a sibling with its own implementation.

### Daily execution order (`crop.py`, `perform_daily_crop_update`)

```
guard:  if self._data.is_mature or self._data.is_dormant: return
  1. self._heat_units.absorb_heat_units(mean, min, max air temp)
  2. self._root_development.develop_roots(time)
  3. self._nitrogen_uptake.uptake(soil_data)
  4. self._phosphorus_uptake.uptake(soil_data)      <-- P enters here
  5. self._growth_constraints.constrain_growth(...) <-- P is consumed here
  6. self._leaf_area_index.grow_canopy()
  7. self._biomass_allocation.allocate_biomass(incoming_light)
```

**Uptake runs before constraint evaluation**, so `optimal_phosphorus` and `crop_data.phosphorus`
are populated before they are read. There is no order-of-initialisation bug here.

---

## 2. How the model consumes phosphorus

### 2.1 Soil fields read

**Exactly one**, at `phosphorus_uptake.py:87`:

```python
 87        self.uptake_main_process(soil_data, "phosphorus", "labile_inorganic_phosphorus_content")
```

`labile_inorganic_phosphorus_content` is the crop model's only read of soil phosphorus state. It
touches none of the active, stable, fresh-organic, sorption, or runoff fields.

The read is also a **write**: `non_water_uptake.py` pulls the vector, depletes it, and writes it
back —

```python
101        layer_nutrient = soil_data.get_vectorized_layer_attribute(soil_layer_attr)
...
132        self.uptake_nutrient(layer_nutrient, layer_depths)
133        soil_data.set_vectorized_layer_attribute(soil_layer_attr, layer_nutrient)
```

### 2.2 The crop-side chain

```
soil labile P
  -> non_water_uptake.uptake_main_process(soil_data, "phosphorus", "labile_...")
       setattr(crop_data, "optimal_phosphorus_fraction", ...)   # non_water_uptake.py:119
       setattr(crop_data, "optimal_phosphorus",          ...)   # non_water_uptake.py:122
       depletes + writes back the layer vector                  # non_water_uptake.py:133
  -> phosphorus_uptake.uptake sets crop_data.phosphorus          # phosphorus_uptake.py:88-90
  -> growth_constraints reads crop_data.phosphorus / .optimal_phosphorus
  -> growth_factor -> biomass and leaf area
```

**`optimal_phosphorus` is assigned only through `setattr` with an f-string name.** A plain grep for
`optimal_phosphorus =` finds nothing in `RUFAS/`; the sole writer is
`non_water_uptake.py:122`. Any name-based dependency analysis of this package will miss it.

### 2.3 Where `simulate_phosphorus_stress` is evaluated

One place — `growth_constraints.py:130-134`:

```python
130        self.phosphorus_stress = (
131            0.0
132            if not simulate_phosphorus_stress
133            else self._determine_nutrient_stress(self.data.phosphorus, self.data.optimal_phosphorus)
134        )
```

Its provenance:

| Step | Location |
| --- | --- |
| declared | `field/field/field_data.py:98` — `simulate_phosphorus_stress: bool = True` |
| populated | `field/manager/field_manager.py:233` — from `field_configuration_data["simulate_phosphorus_stress"]` |
| passed | `crop.py:160` — into `constrain_growth(...)` |
| evaluated | `growth_constraints.py:132` |

It is a **per-field input-file flag**, one of four siblings (`simulate_water_stress`,
`simulate_temp_stress`, `simulate_nitrogen_stress`, `simulate_phosphorus_stress`), all defaulting
to `True`.

### 2.4 What happens to yield when `phosphorus_stress = 0`

Growth factor is a **maximum**, not a product:

```python
173        return 1.0 - max(water_stress, temperature_stress, nitrogen_stress, phosphorus_stress)
```

Consequences:

- If any other stress exceeds phosphorus stress on a given day, forcing `phosphorus_stress = 0`
  changes `growth_factor` by **exactly nothing** that day.
- Yield changes only on days when phosphorus is the **binding** constraint.
- When it is binding, the effect is direct and linear through biomass:
  `biomass_allocation.py:175` — `growth = max_growth * growth_factor`.
- Canopy responds sub-linearly: `leaf_area_index.py:151-152` uses `sqrt(growth_factor)`.
- With all four stresses at 0, `growth_factor = 1.0` — the unstressed maximum, matching
  `CropData.growth_factor` default of `1.0` (`crop_data.py:268`).

Two guards make zero-phosphorus safe rather than explosive:

- `growth_constraints.py:265-266` — `if optimal == 0: stress = 0`. No division by zero.
- `growth_constraints.py:270` — `return min(1, stress)`. Bounded above.

Note the asymmetry: water stress clamps **both** ends (`max(0.0, ...)` then `min(1.0, ...)` at
lines 200-201), while nutrient stress clamps only the top.

---

## 3. The growth-factor code, verbatim

**`RUFAS/biophysical/field/crop/growth_constraints.py:130-141`** — stress assembly:

```python
130        self.phosphorus_stress = (
131            0.0
132            if not simulate_phosphorus_stress
133            else self._determine_nutrient_stress(self.data.phosphorus, self.data.optimal_phosphorus)
134        )
135
136        self.data.growth_factor = self._determine_growth_factor(
137            self.water_stress,
138            self.temp_stress,
139            self.nitrogen_stress,
140            self.phosphorus_stress,
141        )
```

**`growth_constraints.py:143-173`** — the growth factor itself (signature + return, docstring
elided):

```python
143    @staticmethod
144    def _determine_growth_factor(
145        water_stress: float,
146        temperature_stress: float,
147        nitrogen_stress: float,
148        phosphorus_stress: float,
149    ) -> float:  # pseudocode: C.7.E.1
...
171        SWAT 5:3.2.3
172        """
173        return 1.0 - max(water_stress, temperature_stress, nitrogen_stress, phosphorus_stress)
```

**`growth_constraints.py:244-270`** — the nutrient stress function shared by N and P:

```python
244    @staticmethod
245    def _determine_nutrient_stress(stored: float, optimal: float) -> float:  # pseudocode C.7.C.2
...
263        SWAT 5:3.1.3, 5:3.1.4
264        """
265        if optimal == 0:
266            stress = 0
267        else:
268            stress_factor = 200 * (stored / optimal - 0.5)
269            stress = 1 - (stress_factor / (stress_factor + exp(3.535 - (0.02597 * stress_factor))))
270        return min(1, stress)
```

**`biomass_allocation.py:102` and `:175`** — growth factor into biomass:

```python
102        self.biomass_growth = self._determine_accumulated_biomass(self.data.growth_factor, self.data.biomass_growth_max)
...
175        growth = max_growth * growth_factor
```

**`leaf_area_index.py:151-152`** — growth factor into canopy:

```python
151            self.optimal_leaf_area_change * sqrt(self.data.growth_factor),
152            self.optimal_leaf_area_change,
```

---

## 4. Consequences

### 4.1 What breaks if phosphorus is bypassed entirely

**Nothing raises.** The failure modes are silent-but-correct, not crashes.

| Bypass method | Effect on growth | Effect on soil P | Effect on reporting |
| --- | --- | --- | --- |
| `simulate_phosphorus_stress = False` (input flag) | `phosphorus_stress = 0`; yield changes only on days P was binding | **unchanged — uptake still runs and still depletes labile P** | `phosphorus_stress` reports 0 |
| skip `PhosphorusUptake.uptake` (crop side) | `optimal_phosphorus` stays `0.0` → `_determine_nutrient_stress` returns 0 via the `optimal == 0` guard → same as above | labile P **no longer depleted** by the crop | uptake variables report 0 |
| skip `cycle_phosphorus` (soil side, `field.py:1528`) | none directly — crop still reads whatever labile P exists | P pools stop evolving; crop uptake drains them monotonically | ~40 soil P variables freeze |

**The important asymmetry:** turning off the *stress flag* does **not** stop the crop consuming
soil phosphorus. Uptake (step 4) runs before constraint evaluation (step 5) and is not gated by
`simulate_phosphorus_stress`. A "phosphorus off" configuration built only from the flag leaves the
soil P drain fully active.

Combining a soil-side bypass with continued crop uptake produces a monotonically draining labile P
pool with no replenishment — not a crash, but not a physically meaningful run either.

### 4.2 Is the model sensitive to N and water separately?

**Yes, independently and symmetrically.** Four stresses, four flags, one `max`:

| Stress | Flag | Computed by | Clamping |
| --- | --- | --- | --- |
| water | `simulate_water_stress` | `_determine_water_stress` (`:176`), SWAT 5:3.1.1 | `max(0.0, ...)` and `min(1.0, ...)` |
| temperature | `simulate_temp_stress` | `_determine_temperature_stress` (`:206`), SWAT 5:3.1.2 | none explicit; `stress = 1` fallback branch |
| nitrogen | `simulate_nitrogen_stress` | `_determine_nutrient_stress` (`:245`) | `min(1, ...)` only |
| phosphorus | `simulate_phosphorus_stress` | `_determine_nutrient_stress` (`:245`) | `min(1, ...)` only |

N and P are **the same function** with different arguments — `_determine_nutrient_stress(stored,
optimal)`. They are therefore structurally identical and independently switchable. Because the
combination is `max`, the four are *not* additive: only the single largest stress matters on any
given day, so sensitivity to any one of them is conditional on it dominating the others.

Water has an extra dependency the nutrients lack: `_determine_water_stress` guards
`max_transpiration == 0` by returning 0 (`:196-197`), so water stress is inert whenever soil
conditions permit no transpiration.

### 4.3 Dead computation similar to `mineralization_decomp`

**None in the crop package.** I ran a detector across `field/crop/` and `field/soil/` for the three
signatures of the pattern found in mineralization — a function that computes values then returns a
constant, locals assigned but never read, and asserts on computed-then-discarded values. Results
across both packages:

| Finding | Location | Verdict |
| --- | --- | --- |
| `_calculate_nutrient_cycling_residue_composition_factor()` → `1` | `soil/nitrogen_cycling/mineralization_decomp.py:150` | **the known dead computation** — computes N and P terms, asserts them non-`None`, returns `1` |
| `assert nitrogen_term is not None and phosphorus_term is not None` | `mineralization_decomp.py:184` | the only `assert` in either package — part of the same defect |
| `cover_factor()` → `0.5333 / 0.6667 / 0.8` | `soil/soil_data.py:621` | **legitimate** — branch-based lookup on `cover_type`, with `ValueError` on invalid input |
| `solubilizing_factor()` → `1 / 0.4 / 0.075` | `soil/soil_data.py:658` | **legitimate** — same step-function pattern |
| unused locals | — | **none found** in either package |

So the `return 1` defect is isolated to `mineralization_decomp.py`. The crop growth chain — uptake
→ stress → growth factor → biomass/canopy — is fully live: every computed value reaches an output.

### 4.4 Two smaller observations

- **`phosphorus_uptake.py` has no module docstring, despite appearing to.** Lines 5-7 hold a
  string literal describing SWAT section 5:2.3.2, but it sits *after* the imports (lines 1-3), so
  Python treats it as a no-op expression statement, not `__doc__`. Tooling that reads module
  docstrings will report this module as undocumented.
- **`NonWaterUptake` is 893 lines serving both N and P through string-keyed `getattr`/`setattr`.**
  Any change to the phosphorus path lands on nitrogen too unless explicitly branched, and static
  analysis cannot see the coupling.

---

## Provenance

Derived by AST parsing and targeted reads at commit `a8da114`. Every line number, signature, and
quoted expression is verbatim from source. No RUFAS module was imported and no RUFAS code was
executed. The dead-computation scan is AST-based and covers `field/crop/` and `field/soil/`; it
cannot see values discarded through dynamic dispatch or discarded after leaving a function.
