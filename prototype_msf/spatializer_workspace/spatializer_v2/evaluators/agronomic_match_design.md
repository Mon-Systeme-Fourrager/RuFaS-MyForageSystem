# Agronomic Match Evaluator — Design

Status: DRAFT (design only, no code) · Created: 2026-09-16 · Author: Andrea Carranza-Díaz

This document describes the structure of the Agronomic Match Evaluator. It
contains **no numerical values** from the CRAAQ fertilization grids; see
[§9 Anti-fabrication notes](#9-anti-fabrication-notes).

---

## 1. Overview

### 1.1 Purpose

The evaluator answers two questions for one field on one day:

1. **Should manure be applied?** Does the field still have an agronomic need
   for N, P2O5 or K2O, according to the CRAAQ reference grid for its crop and
   soil analysis?
2. **How much?** What dose per hectare (N, P2O5, K2O) does the grid recommend,
   and how should it be split over the season?

### 1.2 Position in the architecture

Agronomic Match is one of three evaluators that together make up the
**Manure Availability** factor (Factor 4) of the Spatializer:

| Evaluator | Question | Status |
|---|---|---|
| Storage Pressure | Does the farm *need* to empty manure storage? | Exploration done; blocked on real storage capacity (RUFAS default `capacity = inf`) |
| Application Window | Is applying manure *allowed / sensible* today (calendar, crop stage, soil state)? | Exploration done; regulatory dates (REA) not yet read at the source |
| **Agronomic Match** | Does the *crop need* the nutrients, and how much? | This document |

It follows the same contract as the other Spatializer evaluators
(`evaluators/base.py`): a plain-data `*Inputs` dataclass passed to
`evaluate()`, returning a `*Result` that subclasses `EvaluationResult`
(`score` in [0, 1], favourable-high; `verdict`; `context`). RUFAS state is
converted into inputs by a separate adapter (`adapters/rufas_to_agronomic_match.py`,
following `adapters/rufas_to_runoff.py`); the evaluator itself does not import
RUFAS.

### 1.3 Relationship to other evaluators

- **Independent inputs.** Agronomic Match does not consume the output of
  Storage Pressure or Application Window; the three can be developed in
  parallel.
- **Overlap to avoid.** Application Window owns calendar and soil-state
  constraints (frozen soil, snow, regulatory dates); Weather owns forecast
  conditions; Runoff owns slope/saturation risk. Agronomic Match must not
  re-penalise those factors.
- **What RUFAS does not provide.** RUFAS simulates crop physiological demand
  (`CropData.optimal_nitrogen`) and soil N/P cycling, but has **no dose
  recommendation, no annual limit per field, no PAEF / Bilan Phosphore logic,
  and no potassium model**. The recommendation logic therefore comes from the
  CRAAQ grids, not from RUFAS.

---

## 2. Scope

### 2.1 MVP (Week 1)

The MVP covers **one grid only**, to validate the pattern (inputs → sub-grid
selection → reference-table lookup → result) before replicating it to the
other three grids.

- **Coverage:** Prairies / Pâturages only (mineral soils), including sub-grid
  selection (établissement / entretien, legume fraction, prairie / pâturage).
- **Output:** recommended N, P2O5, K2O per hectare.
- **N range:** min/max from the grid, plus the point dose when the grid
  determines it (or `manual_review_needed` when it does not).
- **Dataclasses:** `AgronomicMatchInputs`, `AgronomicMatchResult`.
- **Tests:** unit tests for the Prairies grid logic.

Not in the MVP: fractionation plan and warnings (Week 3).

### 2.2 Roadmap (Weeks 2–4)

- **Week 2 — Remaining grids:** Maïs à ensilage, Maïs-grain, Blé/Orge.
- **Week 3 — Fractionation and warnings:** fractionation plan from the grid
  notes; warnings for pH outside the adequate range, ISP1 above the
  no-response class (maïs), fertility class not defined for the texture group
  (prairies), and `manual_review_needed` handling.
- **Week 4 — Manure discount:** subtract the *effective* nutrient
  contribution of manure using CRAAQ Chapitre 10 efficiency coefficients
  (RT-07 for N; Tableau 10.7 for P and K, not yet loaded), including prior
  applications tracking.
- **Later — Edge cases:** fall seeding (établissement), non-profitable
  situations in the prairies N grid (grid still recommends a minimal N
  input), fertility classes that do not exist for a texture group.

### 2.3 Out of scope

- Organic soils (separate grids in Chapitre 12).
- Other crops in Chapitre 12.
- Micronutrients (B, Mg, Zn, Mn): only surfaced as informational warnings
  when a grid note mentions them.
- Regulatory limits (REA phosphorus limits, PAEF): not in the CRAAQ grids;
  belong to a separate constraint layer.

---

## 3. Data model

The dataclasses below adapt the initial proposal after re-reading the
extracted grid structure. Changes are listed in [§3.3](#33-changes-from-the-initial-proposal).

### 3.1 `AgronomicMatchInputs`

```python
from dataclasses import dataclass, field
from typing import List, Optional

from .base import EvaluationResult


@dataclass
class AgronomicMatchInputs:
    # --- Crop ------------------------------------------------------------
    crop_type: str
    # "prairies" | "paturages" | "mais_ensilage" | "mais_grain" | "ble" | "orge"
    # ASCII identifiers; display names keep accents.

    # --- Soil analysis, Mehlich-3 (raw lab values; indices computed later) --
    p_mehlich3_kg_ha: float        # prairies, blé/orge grids (kg PM-3/ha)
    k_mehlich3_kg_ha: float        # all grids (kg KM-3/ha)
    ph_water: float                # all grids (adequate range check)

    # --- Soil analysis, optional per grid ---------------------------------
    p_mehlich3_mg_kg: Optional[float] = None    # maïs: ISP1 numerator
    al_mehlich3_mg_kg: Optional[float] = None   # maïs: ISP1 denominator;
                                                # prairies: P grid column axis

    # --- Texture ------------------------------------------------------------
    texture_group: Optional[str] = None
    # "G1" | "G2" | "G3" (CRAAQ Tableau 1.1).
    # Prairies: K grid column axis. Maïs: mentioned for N, classes undefined.

    # --- Prairies / pâturages ---------------------------------------------
    situation: Optional[str] = None             # "etablissement" | "entretien"
    legume_fraction: Optional[float] = None     # 0-1; selects sub-grid
    cuts_per_season: Optional[int] = None       # 2 | 3; N and K fractionation
    seeding_season: Optional[str] = None        # "spring" | "fall" (établissement)
    companion_crop: Optional[str] = None        # culture-abri species (établissement N)
    forage_value_per_t_dm: Optional[float] = None       # $/t DM (prairies entretien N)
    n_fertilizer_cost_per_kg: Optional[float] = None    # $/kg N (prairies entretien N)
    max_yield_potential_t_dm_ha: Optional[float] = None # prairies entretien N

    # --- Maïs ----------------------------------------------------------------
    climate_zone: Optional[str] = None
    # Grid text: "selon la zone climatique". Class definition unknown
    # (see Open question 1). NOT a UTM map-projection zone.
    manure_history: Optional[bool] = None       # starter-P economic note

    # --- Blé / orge ------------------------------------------------------------
    wheat_type: Optional[str] = None
    # "spring" | "autumn" | "forage" | "bread" | "pastry"
    lodging_risk: Optional[str] = None          # "low" | "high"; N adjustment note

    # --- Prior applications this season (ROADMAP, Week 4) ------------------
    # Must be EFFECTIVE nutrients (after Ch. 10 efficiency coefficients),
    # not raw applied masses. Unused by the MVP.
    prior_effective_n_kg_ha: float = 0.0
    prior_effective_p2o5_kg_ha: float = 0.0
    prior_effective_k2o_kg_ha: float = 0.0
```

### 3.2 `AgronomicMatchResult`

```python
@dataclass
class AgronomicMatchResult(EvaluationResult):
    # Inherits: score (0-1, favourable-high), verdict (str), context (dict).
    # All fields defaulted: EvaluationResult.context has a default, so
    # subclass fields must too (same pattern as CompactionResult/RunoffResult).

    # Grid identification
    grid_id: Optional[str] = None           # e.g. "prairies_entretien_low_legume"

    # Recommended doses (after prior-application discount, when enabled)
    recommended_n_kg_ha: Optional[float] = None
    recommended_p2o5_kg_ha: Optional[float] = None
    recommended_k2o_kg_ha: Optional[float] = None

    # N range as given by the grid
    n_range_min_kg_ha: Optional[float] = None
    n_range_max_kg_ha: Optional[float] = None

    # Fractionation plan (ordered application moments) — populated from Week 3
    fractionation_plan: List[str] = field(default_factory=list)

    # Warnings — populated from Week 3
    ph_out_of_range: bool = False
    isp1_too_high: bool = False              # maïs only
    fertility_class_undefined: bool = False  # prairies: class absent for texture group
    manual_review_needed: bool = False
    warnings: List[str] = field(default_factory=list)
```

### 3.3 Changes from the initial proposal

| Change | Reason |
|---|---|
| Required fields moved before optional ones | Python dataclasses reject non-default fields after default fields (`TypeError`) |
| Result fields given defaults | `EvaluationResult.context` has a default; same constraint |
| Added `p_mehlich3_mg_kg` | Maïs P axis is ISP1, computed from P and Al **in mg/kg**; prairies and blé/orge use P in kg/ha. Converting kg/ha ↔ mg/kg needs soil mass (depth × bulk density), so both lab values are kept rather than converted |
| Added `cuts_per_season`, `seeding_season`, `companion_crop` | Prairies grid notes: N/K split by number of cuts; fall seeding rule; établissement N depends on culture-abri species |
| Added `lodging_risk`, `manure_history` | Blé/orge N adjusted by cultivar lodging risk; maïs starter-P note refers to manure history |
| `climate_zone` comment corrected | Grid wording is "zone climatique"; the class system is not defined in the grid (Open question 1) |
| `pâturages` → `paturages` | ASCII identifiers in code |
| `prior_*` renamed `prior_effective_*` and moved to roadmap | Grids do not subtract prior inputs; subtraction requires Ch. 10 efficiency coefficients (Week 4). Raw applied kg would over-discount |
| Added `grid_id`, `fertility_class_undefined` | Traceability of which sub-grid was used; prairies grid note about non-existent fertility classes |
| `score` / `verdict` semantics | Not yet defined — Open question 9 |

---

## 4. Grid coverage

All grids: mineral soils, 2e édition actualisée. Page numbers: book page →
PDF page (PDF offset varies between +40 and +41 across the file).

### 4.1 Prairies / Pâturages

Reference: Chapitre 12, "Les spécifications concernant les grilles pour les
prairies et pâturages" and grids (PDF 484–493).

**Sub-grids (4):**

| Sub-grid | Selector |
|---|---|
| Prairies, pâturages — Établissement | `situation = etablissement` |
| Prairies, pâturages — Entretien, legumes ≥ threshold | `situation = entretien`, `legume_fraction ≥ T` |
| Pâturages — Entretien, legumes < threshold | `crop_type = paturages`, `legume_fraction < T` |
| Prairies — Entretien, legumes < threshold | `crop_type = prairies`, `legume_fraction < T` |

`T` = legume-fraction threshold stated in the grid (value to be loaded from
the reference table).

**Input axes:**

| Nutrient | Axes |
|---|---|
| N — établissement | Timing (at seeding / after first cut) → range |
| N — entretien, legumes ≥ T; pâturages entretien | Single range (broadcast) |
| N — prairies entretien, legumes < T | 2-D: forage value / fertilizer cost ratio ($/t DM per $/kg N) × maximum yield potential (t DM/ha, 3 classes) |
| P | 2-D: P Mehlich-3 (kg PM-3/ha, fertility classes) × Al Mehlich-3 (mg/kg, 3 fixing-capacity classes) |
| K | 2-D: K Mehlich-3 (kg KM-3/ha, fertility classes) × texture group (G1/G2/G3) |

**Output:** kg N/ha, kg P2O5/ha, kg K2O/ha; adequate pH range.

**Additional rules (grid notes):**

- Maximum annual N dose (agronomic/environmental cap).
- N split by cutting regime (2 or 3 cuts); fertilise right after cutting.
- K above a threshold dose should be split by cutting regime, before the
  critical fall period.
- Entretien doses are designed for a DM production range; reduce
  proportionally for lower production.
- Default maximum yield potential when history is unknown (old stand / young
  stand / high-production field).
- Établissement: choose within N range by culture-abri species and association
  composition; fall seeding → reduce and apply the following spring.
- Some fertility classes do not exist for a given texture group → review
  texture classification or soil analysis.
- Non-profitable ratio: still apply a minimal N dose to keep N-P-K balance.
- Informational: B (legumes), Mg follow-up.

### 4.2 Maïs à ensilage

Reference: Chapitre 12, specifications (PDF 462–463) and grid (PDF 466).

**Sub-grids:** none.

**Input axes:**

| Nutrient | Axes |
|---|---|
| N | Single range; choice "selon la zone climatique et les textures de sol" (classes not defined in grid); part banded at seeding |
| P | 1-D: ISP1 (%) = PM-3 (mg/kg) / AlM-3 (mg/kg) × 100, classes. **Shared with maïs-grain.** No texture groups |
| K | 1-D: K Mehlich-3 (kg KM-3/ha), classes. **Own grid** (higher K export than grain) |

**Output:** kg N/ha, kg P2O5/ha, kg K2O/ha; adequate pH range.

**Additional rules:**

- Above a given ISP1 class, no P recommended.
- Maximum safe doses at seeding: see Chapitre 9 table.
- Starter P may be uneconomic depending on manure history (Cantin, MAPAQ).
- Informational: B, Mg, Zn.

### 4.3 Maïs-grain

Reference: Chapitre 12, specifications (PDF 462–463) and grid (PDF 464).

**Sub-grids:** none.

**Input axes:**

| Nutrient | Axes |
|---|---|
| N | Single range; choice by climate zone and soil texture (classes not defined in grid); part banded at seeding |
| P | 1-D: ISP1 (%), classes (same grid as maïs à ensilage) |
| K | 1-D: K Mehlich-3 (kg KM-3/ha), classes (own grid) |

**Output:** kg N/ha, kg P2O5/ha, kg K2O/ha; adequate pH range.

**Additional rules:**

- P recommendation = mean economic dose based on yield and grain moisture.
- Above a given ISP1 class, response is null or negative → no P.
- Maximum safe doses at seeding (Chapitre 9); starter-P economics vs manure
  history.
- Informational: B, Mg, Zn.

### 4.4 Blé / Orge

Reference: Chapitre 12, grid (PDF 425).

**Sub-grids:** none (one grid, N given per species).

**Input axes:**

| Nutrient | Axes |
|---|---|
| N | Two rows: blé, orge → range each |
| P | 1-D: P Mehlich-3 (kg PM-3/ha), classes. **Not ISP1** |
| K | 1-D: K Mehlich-3 (kg KM-3/ha), classes |

**Output:** kg N/ha, kg P2O5/ha, kg K2O/ha; adequate pH range.

**Additional rules:**

- Blé recommendation applies to spring, autumn, forage and bread wheat.
- Adjust N to cultivar lodging risk; cap for pastry wheat.
- N may be split between seeding and tillering, adjusted to growing conditions.
- Maximum safe doses at seeding (Chapitre 9).
- Informational: B (ergot in barley), Mn.

### 4.5 Axis summary

| Axis | Prairies | Maïs ensilage | Maïs-grain | Blé/Orge |
|---|---|---|---|---|
| P Mehlich-3 kg/ha | ✅ | — | — | ✅ |
| ISP1 (P, Al mg/kg) | — | ✅ | ✅ | — |
| Al Mehlich-3 classes | ✅ (P column) | via ISP1 | via ISP1 | — |
| K Mehlich-3 kg/ha | ✅ | ✅ | ✅ | ✅ |
| Texture group G1–G3 | ✅ (K column) | N note only | N note only | — |
| Legume fraction | ✅ | — | — | — |
| Economic ratio + yield potential | ✅ (N) | — | — | — |
| Climate zone | — | N note | N note | — |
| pH adequate range | ✅ | ✅ | ✅ | ✅ |

---

## 5. Dependencies

### 5.1 RUFAS data (via adapter)

| Input | RUFAS source | Caveat |
|---|---|---|
| `crop_type` | `field.crops[i].data.name` | Needs a mapping table RUFAS crop name → CRAAQ grid. Whether RUFAS distinguishes maïs ensilage vs grain, or prairie vs pâturage, is **not verified** |
| `situation` (établissement/entretien) | `field.planting_events`, `CropData.planting_year` | Derivation rule TBD |
| `cuts_per_season` | `field.harvest_events` | Derivation rule TBD |
| `prior_effective_*` (roadmap) | Accumulated applications — source TBD (see warning below) | `nitrogen_mass` is kg for the whole field → divide by `field_size` (ha). RUFAS does not apply K |
| Others | TBD | — |

> ⚠️ `field.manure_events` cannot be used for prior applications (RUFAS
> removes past events daily). Alternative source needed — investigate
> OutputManager records for accumulated applications.

### 5.2 External data required (NOT in RUFAS)

- Mehlich-3 soil analysis: P (kg/ha and mg/kg), K (kg/ha), Al (mg/kg).
- pH (water).
- Texture group G1/G2/G3 (CRAAQ Tableau 1.1).
- Prairies economics: forage value ($/t DM), N fertilizer cost ($/kg N).
- Prairies maximum yield potential (t DM/ha), or the grid default by stand type.
- Legume fraction of the stand.
- Climate zone for maïs (class system TBD).
- Wheat type and cultivar lodging risk.

### 5.3 Data sources to integrate

| Source | Target | Status |
|---|---|---|
| Producer soil analysis | Input mechanism TBD with Maxime | Not started |
| CRAAQ Tableau 1.1 (G1/G2/G3) | Seed `craaq_group` in RT-08 (`ref_soil_series_quebec`), supabase-connector | Column currently NULL (removed as unsourced, 2026-07-24) |
| CRAAQ Chapitre 12 grids | New reference tables, one per grid family (supabase-connector) | Not started; pending CRAAQ authorization |
| CRAAQ Chapitre 10 | RT-06 (N contents, verified), RT-07 (N efficiency, not re-verified), Tableau 10.7 (P/K efficiency, not loaded) | Partial |
| CRAAQ Chapitre 5 | Maïs N climate-zone classes | To review |

> ⚠️ Verify whether RUFAS distinguishes crop sub-types (mais-ensilage vs
> mais-grain, prairie vs pâturage). If not, sub-type must be specified
> externally via input parameter.

---

## 6. Open questions

1. **Maïs N classes.** The grids say the N dose is chosen "selon la zone
   climatique et les textures de sol" but do not define the classes. Check
   Chapitre 5 (La gestion de l'azote).
2. **Prairies vs Pâturages.** Below the legume threshold there are two
   different N grids (economic 2-D table vs single range). MSF must decide
   which applies to each field and how that is recorded.
3. **Texture group source.** RT-08 `craaq_group` is NULL. Seed from CRAAQ
   Tableau 1.1 (book p.17), with source citation.
4. **Point dose within a range.** Several grids give an N range; choosing the
   exact dose requires information not tabulated (association, cultivar,
   zone). Decide: return the range + `manual_review_needed`, a documented
   default rule, or producer input.
5. **Manure discount.** The Chapitre 12 grids do not account for prior
   manure. The discount needs Chapitre 10 efficiency coefficients (N: RT-07;
   P/K: Tableau 10.7, not loaded) — combining both chapters.
6. **Soil-analysis units.** Labs may report P and K in kg/ha or mg/kg. Confirm
   what MSF producers' analyses provide before fixing the input contract.
7. **Licensing.** Loading grid values into software/databases requires CRAAQ
   written authorization; the MSF-level authorization is pending (§8).
8. **MVP boundary.** *Resolved 2026-09-16:* MVP reduced to the Prairies grid;
   fractionation and warnings moved to Week 3 (§2, §7).
9. **Score/verdict interpretation for EvaluationResult contract.** Three
   interpretations under consideration:
   - Binary: 1.0 if recommendation possible, 0.0 if not
   - Confidence: 0-1 based on input completeness and quality
   - Delta: 1 - |planned_dose - recommended_dose| / recommended_dose
     [preferred interpretation]

   Delta is preferred because it answers "is the producer's planned dose
   correct?" which is more actionable than "was a recommendation
   computable?". Decision pending discussion with Slava/Maxime.

---

## 7. Roadmap

| Week | Deliverables |
|---|---|
| **1** | Prairies grid (MVP) + `AgronomicMatchInputs` + `AgronomicMatchResult` + tests |
| **2** | Maïs à ensilage + Maïs-grain + Blé/Orge grids |
| **3** | Fractionation + warnings |
| **4** | Manure discount integration (Ch. 10 coefficients) |

Prerequisites outside the evaluator: CRAAQ authorization (before loading
values); Tableau 1.1 seeding; soil-analysis input mechanism.

---

## 8. References

- CRAAQ. *Guide de référence en fertilisation*, 2e édition actualisée.
  - Chapitre 12 — Les grilles de référence (grids used here).
  - Chapitre 10 — Les engrais de ferme et les matières résiduelles
    fertilisantes organiques (manure efficiency coefficients).
  - Chapitre 1, Tableau 1.1 — texture groups G1/G2/G3 (book p.17).
  - Chapitre 5 — La gestion de l'azote (maïs N zones, to review).
  - Chapitre 9 — maximum safe doses at seeding (referenced by grid notes).
- Cantin, J. (MAPAQ) — starter-P economics vs manure history, as cited in the
  maïs grid notes.
- **License:** Andrea holds personal purchase (per Andrea). MSF-level
  authorization pending verification with CRAAQ.

---

## 9. Anti-fabrication notes

- **No numerical values from the CRAAQ grids are copied into this document.**
  Thresholds are referred to symbolically (e.g. legume threshold `T`).
- Grid values will be loaded from supabase-connector reference tables
  (RT-06, RT-07 extended, RT-08, and new tables per grid family), only after
  CRAAQ authorization.
- Any placeholder in code must be marked `PLACEHOLDER` with the reason and the
  expected source (table and page), following `evaluators/runoff.py`.
- Grid structure was extracted with digits masked; axis names are reliable,
  but column assignment in 2-D tables should be confirmed visually against
  the PDF before implementation.
