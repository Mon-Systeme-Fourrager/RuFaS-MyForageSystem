# Tasks — BeefGEM Management Enhancement Layer

## Phase A — Finishing System Flag

- [x] A-1-1: Add `FinishingSystem(Enum)` to `animal_enums.py`
      (plain Enum, not str,Enum)
- [x] A-1-2: Add `finishing_system: FinishingSystem` ClassVar to
      `AnimalConfig` with default `FinishingSystem.GRAIN_FED`
- [x] A-1-3: Parse `finishing_system` from feedlot config using
      walrus operator pattern in `_initialize_feedlot_finishing_system()`
- [x] A-1-4: Add `finishing_system` validation to
      `DataValidator.validate_feedlot_config()`
- [x] A-1-5: Add `calculate_enteric_ch4_grass_fed()` to
      `BeefNRCRequirementsCalculator` (linear grass-fed model)
- [x] A-1-6: Add `calculate_enteric_ch4_grain_fed()` to
      `BeefNRCRequirementsCalculator` (IPCC Tier 2, Ym = 3.0%;
      NRC 2016 Table 16-2). Eq. 16-9 deferred — needs ration composition
      at the call site.
- [x] A-1-7: Route CH4 equation in
      `AnimalModuleReporter.report_feedlot_performance()`
      based on `finishing_system` flag, emitting
      `feedlot_mean_daily_enteric_ch4_g_d` [OutputChange]
- [x] A-1-8: Add BEEF_CH4_GRASS_FED_INTERCEPT, BEEF_CH4_GRASS_FED_SLOPE,
      BEEF_CH4_YM_FRACTION, BEEF_GROSS_ENERGY_MJ_PER_KG_DM and
      BEEF_CH4_ENERGY_MJ_PER_G to `animal_module_constants.py`
- [x] A-1-9: Write `test_finishing_system.py` — Phase A checkpoint
      (regression guard + CH4 routing tests)

## Phase B — Stocker Enhancements

- [x] B-1-1: Add `LIMIT_FEED` to `StockerDietSystem` enum
- [x] B-1-2: Add `stocker_limit_feed_pct: float = 85.0` to
      `AnimalConfig` with math.isfinite validation
- [x] B-1-3: Add `beef_stocker_limit_feed_ration` ClassVar to
      `RationManager`
- [x] B-1-4: Update `get_beef_stocker_ration()` to handle LIMIT_FEED
- [x] B-1-5: Verify handle_failed_constraints still delegates to
      _select_constraints rather than maintaining a parallel list, and
      assert the delegation with a spy. Limit-feeding does not change
      a stocker pen's AnimalCombination, so no new constraint branch
      is needed — the intake reduction is already carried in the DMI
      requirement by the time the optimiser runs.
- [x] B-1-6: Apply DMI cap in
      `BeefStockerRequirementsCalculator` when LIMIT_FEED active
- [x] B-1-7: Add `days_on_restricted_intake` and
      `is_on_restricted_intake` to Animal stocker instance attrs
- [x] B-1-8: Write `test_limit_feeding.py` — Phase B-1 checkpoint
- [x] B-2-1: Add BEEF_CH4_STOCKER_FORAGE_INTERCEPT and
      BEEF_CH4_STOCKER_FORAGE_SLOPE to `animal_module_constants.py`.
      Named `BEEF_CH4_*` not `NASEM_*` — the coefficients have no identified
      NRC 2016 equation number; see the plan's provenance note.
- [x] B-2-2: Add `calculate_enteric_ch4_stocker()` to
      `BeefStockerRequirementsCalculator`, linear in DMI
- [x] B-2-3: Add `stocker_mean_daily_enteric_ch4_g_d` output variable to
      `AnimalModuleReporter.report_stocker_performance()`, matching the
      feedlot naming. The equation has a non-zero intercept, so the
      reporter short-circuits on days_in_stocker > 0 rather than
      evaluating at zero intake. [OutputChange]
- [x] B-2-4: Write `test_enteric_ch4.py` — Phase B-2 checkpoint

## Phase C — Herd Population Dynamics

- [x] C-0-1: Add `COW_CALF_STOCKER_FEEDLOT` to `animal_grouping_scenarios.py`
      reusing the six existing `AnimalCombination` members. No new
      combination member required.
- [x] C-0-2: Write `test_grouping_scenario.py` — Phase C-0 checkpoint
      (distinct lists, no shared types, BEEF_STOCKER_ONLY regression guard)

- [x] C-1-1: Add the eight named scenario constants to
      `animal_module_constants.py`. The two conception constants are
      multipliers (1.15 / 0.625) derived from the calibration, not rates.
      Docstrings state these are named-scenario defaults, not measured
      values. 0.855 is NOT a conception rate — it is
      BEEF_CALF_CROP_WEANED_RATE, downstream of conception.
- [x] C-1-2: Add `get_beef_calving_month()` / `set_beef_calving_month()`
      classmethods over `beef_breeding_season_start_day` (not a property —
      AnimalConfig is never instantiated), and
      `beef_conception_rate_multiplier` with > 0 and isfinite validation,
      applied and clamped in `calculate_seasonal_conception_probability`.
- [x] C-1-3: Write `test_scenario_constants.py` — Phase C-1 checkpoint
- [x] C-2-1: Add `get_beef_herd_summary()` to `AnimalModuleReporter`
      returning dict[str, float] with 4 metrics: calf_crop_pct,
      mean_calving_interval_days, replacement_rate_pct, mean_cow_bcs.
      Four originally specified metrics are CUT, not returned as 0.0 —
      mean_stocker_adg_kg_d, mean_feedlot_adg_kg_d,
      mean_feedlot_days_on_feed and total_enteric_ch4_g_d. Nothing
      retains exit performance across a run, report_feedlot_performance
      is never called in production, and beef animals produce no daily
      methane. Do not restore them without the accumulator — see C-2-4.
- [x] C-2-2: Wire summary metrics from HerdManager live state.
      calf_crop_pct counts survivors only and is biased upward; the bias
      is documented in the docstring and pinned in a test.
- [x] C-2-3: Write `test_herd_summary_reporter.py` — Phase C-2 checkpoint
- [ ] C-2-4: DEFERRED — herd-level exit-performance accumulator.
      Requires persistent state on HerdManager written from both exit
      paths, plus wiring report_feedlot_performance into a feedlot
      daily-update path. Blocked on the feedlot wiring gap. Not part
      of this module.
- [ ] C-3-1: Create `RUFAS/biophysical/animal/beef_scenario_runner.py`
      with `BeefHerdScenario` dataclass
- [ ] C-3-2: Implement `run_scenario()` function
- [ ] C-3-3: Implement `compare_scenarios() → pd.DataFrame`
- [ ] C-3-4: Define `BEEF_SCENARIOS` dict with 8 named scenarios
- [ ] C-3-5: Write `test_scenario_runner.py` — Phase C-3 checkpoint
      (@pytest.mark.integration)

## Phase D — Environmental Stress

- [ ] D-1-0: Add `relative_humidity_pct: float | None = None` to
      `AnimalConfig` with range (0-100) and `math.isfinite` validation.
      Static configuration value, not a daily weather input.
- [ ] D-1-0b: Implement `_interpolate_heat_stress` with anchor tables
      (piecewise-linear, continuous at the THI 72 onset). Raise ValueError
      if the multiplier tuple length does not match the anchor tuple.
- [ ] D-1-0c: Port the Phase D-1 checkpoint tests from the plan into
      `tests/test_biophysical/test_animal/test_beefgem/test_heat_stress.py`
      BEFORE implementing `_interpolate_heat_stress`. The seven-row
      multiplier table and the onset continuity test are written as
      specification in the plan and must exist as failing tests first.
- [ ] D-1-1: Add heat stress constants to `animal_module_constants.py`
      (BEEF_THI_BREAKPOINTS = (72.0, 80.0, 90.0),
      BEEF_HEAT_STRESS_DMI_MULTIPLIERS = (1.00, 0.88, 0.75),
      BEEF_HEAT_STRESS_NEm_MULTIPLIERS = (1.00, 1.12, 1.20))
- [ ] D-1-2: Add `calculate_thi()` static method to both calculators
- [ ] D-1-3: Add `relative_humidity_pct: float | None = None` to
      both input dataclasses, sourced from `AnimalConfig`
- [ ] D-1-4: Apply THI modifiers in both calculators after base DMI/NEm
- [ ] D-1-5: Write `test_heat_stress.py` — Phase D-1 checkpoint
- [ ] D-2-1: Add CG constants to `animal_module_constants.py`
      (CG_RESTRICTION_THRESHOLD_DAYS, CG_MIN_INTAKE_FRACTION,
      CG_MAX_ADG_MULTIPLIER, CG_DECAY_RATE_PER_DAY)
- [ ] D-2-2: Add `enable_compensatory_gain: bool = False` to
      `AnimalConfig`
- [ ] D-2-3: Add `compensatory_gain_factor: float = 1.0` to Animal
      stocker and feedlot instance attrs
- [ ] D-2-4: Set CG factor at stocker exit based on
      `days_on_restricted_intake`
- [ ] D-2-5: Apply CG decay in `_feedlot_daily_routines()`
- [ ] D-2-6: Apply CG factor in both calculators on target_adg
- [ ] D-2-7: Write `test_compensatory_gain.py` — Phase D-2 checkpoint

## Post-implementation

- [ ] POST-1: Write `test_beefgem_integration.py`
      (@pytest.mark.integration — full scenario comparison test)
- [ ] POST-2: Create `docs/beef_module/beefgem/README.md`
      with scope boundaries (no Lesson references)
- [ ] POST-3: Update `changelog.md` with [OutputChange] entry
- [ ] POST-4: Update `CLAUDE.md` with BeefGEM reference section
- [ ] POST-5: Run full pre-review checklist before requesting review
