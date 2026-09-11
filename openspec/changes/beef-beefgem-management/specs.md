# Specs — BeefGEM Management Enhancement Layer

## Phase A — Finishing System Flag

### A-1: FinishingSystem enum

**Given** a feedlot simulation with no finishing_system configured
**When** the simulation runs
**Then** behavior is identical to pre-BeefGEM (GRAIN_FED default,
zero delta on all outputs)

**Given** finishing_system = "grass_fed" in feedlot config
**When** enteric CH4 is reported
**Then** the Mits3 equation is used: CH4 = 8.25 + 31.2 × DMI (g/d)

**Given** an invalid finishing_system string in config
**When** AnimalConfig initializes
**Then** a ValueError is raised listing valid options before any
class state is modified

**Given** finishing_system = "grain_fed" (default)
**When** feedlot CH4 is reported
**Then** the IPCC Tier 2 equation is used (Ym = 3.0% of gross energy
intake, NRC 2016 Table 16-2)

**Given** a feedlot animal exiting with mean daily DMI of 9 kg/d
**When** feedlot CH4 is reported under the grain_fed default
**Then** `feedlot_mean_daily_enteric_ch4_g_d` is 89.51 g/d, inside the
36-145 g/d range NRC 2016 Ch.16 reports for finishing cattle

**Given** a feedlot animal with days_on_feed = 0
**When** feedlot CH4 is reported
**Then** `feedlot_mean_daily_enteric_ch4_g_d` is 0.0 and no error is raised

## Phase B — Stocker Enhancements

### B-1: Limit-feeding

**Given** stocker diet_system = "limit_feed" and limit_feed_pct = 85
**When** DMI is calculated for a stocker animal
**Then** DMI = ad_libitum_DMI × 0.85 (±0.1%)

**Given** limit-feeding is active for N days
**When** the stocker exits
**Then** days_on_restricted_intake == N

**Given** stocker diet_system = "pasture" (default)
**When** the simulation runs
**Then** DMI is unchanged from pre-BeefGEM behavior

### B-2: NASEM 2016 stocker CH4

**Given** a stocker animal on forage with DMI = 10 kg/d
**When** enteric CH4 is calculated
**Then** CH4 = 10.04 + 23.7 × 10 = 247.04 g/d (exact, Eq.6.8)

**Given** a stocker animal is reported
**When** report_stocker_performance() runs
**Then** stocker_enteric_ch4_g_d appears in the output

**Given** the Phase A feedlot CH4 routing
**When** Phase B is added
**Then** feedlot CH4 output is unchanged (regression guard)

## Phase C — Herd Population Dynamics

### C-0: COW_CALF_STOCKER_FEEDLOT grouping scenario

**Given** the COW_CALF_STOCKER_FEEDLOT grouping scenario
**When** `animals_by_type` is built for a herd containing all three segments
**Then** each of the six combinations maps to a distinct, non-shared list

**Given** a `BEEF_COW` in the `COW_CALF_STOCKER_FEEDLOT` scenario
**When** `find_animal_combination` is called
**Then** `NotImplementedError` is raised, consistent with `BEEF_COW_CALF_HERD`
— runtime reproduction-state dispatch is out of C-0 scope

**Given** any combination in `COW_CALF_STOCKER_FEEDLOT`
**When** `RationOptimizer._select_constraints` is called with it
**Then** a constraint set is returned and no `ValueError` is raised

**Given** `BEEF_STOCKER_ONLY` already exists
**When** `COW_CALF_STOCKER_FEEDLOT` is added
**Then** `BEEF_STOCKER_ONLY` behavior is unchanged (regression guard)

### C-1: BeefHerdScenario dataclass

**Given** a BeefHerdScenario with calving_month=4, weaning_age_mo=7
**When** the scenario is constructed
**Then** all fields default correctly and validate without error

**Given** calving_month = 13 (invalid)
**When** the scenario is constructed
**Then** a ValueError is raised

### C-2: Herd summary reporter

**Given** a herd with known calf and cow counts
**When** get_beef_herd_summary() is called
**Then** calf_crop_pct = calves_born / cows_exposed × 100

**Given** an empty herd
**When** get_beef_herd_summary() is called
**Then** all 8 metrics return 0.0 without raising

### C-3: Scenario runner

**Given** two BeefHerdScenario instances (spring and fall calving)
**When** compare_scenarios({"spring": s1, "fall": s2}, years=1) is called
**Then** a pd.DataFrame is returned with shape (2, 8)
**And** both scenarios produce at least one differing metric

**Given** BEEF_SCENARIOS["spring_calving_baseline"]
**When** run_scenario() completes for 1 year
**Then** calf_crop_pct is between 60 and 100

## Phase D — Environmental Stress

### D-1: Heat stress

**Given** temperature_c=30, relative_humidity_pct=80
**When** THI is calculated
**Then** THI = 82.92 (±0.01)

**Given** THI at or below 72
**When** DMI and NEm are calculated
**Then** no modification is applied (multipliers = 1.00)

**Given** the piecewise-linear heat stress interpolation
**When** the DMI and NEm multipliers are evaluated across the THI range
**Then** they take these values (±0.001):

| THI | DMI multiplier | NEm multiplier | Note |
| --- | --- | --- | --- |
| 71.9 | 1.000 | 1.000 | below onset |
| 72 | 1.000 | 1.000 | anchor, onset of stress |
| 76 | 0.940 | 1.060 | midway 72-80 |
| 80 | 0.880 | 1.120 | anchor, source moderate |
| 85 | 0.815 | 1.160 | midway 80-90 |
| 90 | 0.750 | 1.200 | anchor, source severe |
| 95 | 0.750 | 1.200 | clamped above last anchor |

**Given** THI 71.999 and THI 72.001
**When** the DMI multiplier is evaluated at each
**Then** the two agree to within 1e-4 — the response is continuous at the
onset, with no step

**Given** the anchor and multiplier tuples
**When** their lengths are compared
**Then** all three are the same length and pair one-to-one; a mismatch
raises ValueError

**Given** relative_humidity_pct = None (default)
**When** the simulation runs
**Then** no heat stress is applied and all outputs match pre-BeefGEM

**Given** relative_humidity_pct outside 0-100 or non-finite
**When** AnimalConfig initializes
**Then** a ValueError is raised

### D-2: Compensatory gain

**Given** enable_compensatory_gain = False (default)
**When** the simulation runs
**Then** compensatory_gain_factor = 1.0 always (no ADG modification)

**Given** enable_compensatory_gain = True and 30 days of restriction
**When** the stocker exits
**Then** compensatory_gain_factor > 1.0 and ≤ 1.25

**Given** restriction ends
**When** each simulation day passes
**Then** compensatory_gain_factor decays by 2% per day toward 1.0
