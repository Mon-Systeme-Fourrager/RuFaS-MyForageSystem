# Tasks — Slope/Aspect API Integration

## Pre-implementation validation

- [ ] Run the empirical sensitivity experiment (proposal Q2):
  - [ ] Copy `input/data/soil/example_soil.json` to two variants
        differing only in `average_subbasin_slope` (0.05 vs 0.30, m/m)
  - [ ] Wire two `prototype_root_slope*.json` chains pointing to each
        variant
  - [ ] Run `python prototype_msf/run_prototype.py` twice, moving
        `prototype_msf/output/` aside between runs
  - [ ] Compare `output/CSVs/msf_prototype_saved_variables_*.csv` on
        MUSLE sediment yield, nitrate runoff, per-layer nitrogen at
        day 30; record the sensitivity coefficient in this file
- [ ] Review with Bilal — pipeline reuse patterns (per D4 and
      Maxime's 2026-07-28 directive)
- [ ] Confirm Supabase cache table schema with Maxime (D2)
- [ ] Get written approval from Slava and Maxime on this proposal
      before opening the implementation branch

## Frontend — none

*(This change has no frontend surface.)*

## Local dev tooling

- [ ] Add environment variable `JEREMIE_API_URL` with the endpoint
      from `slope_aspect_api.md`
- [ ] Add a fixture directory `prototype_msf/tests/fixtures/` with
      the three verified JSON responses (36-1, 32-1) for offline
      testing

## Data model — Supabase

- [ ] Migration: create `topographic_cache` table (schema from
      design D2)
- [ ] Deploy migration to Supabase (following the SUPABASE_DEPLOYMENT
      procedure in supabase-connector)

## Core modules

- [ ] Create `prototype_msf/unit_conversions.py`:
  - [ ] `degrees_to_fraction(slope_deg: float) -> float`
  - [ ] `degrees_to_percent(slope_deg: float) -> float`
  - [ ] `fraction_to_percent(slope_frac: float) -> float`
  - [ ] Unit tests for each conversion
- [ ] Create `prototype_msf/geomatic_client.py`:
  - [ ] HTTP client with configurable timeout
  - [ ] Response parsing into a `TopographicResult` dataclass
  - [ ] Error handling: `APITimeoutError`, `APIGeometryError`,
        `APIResponseError`, `APICoverageError`
  - [ ] Supabase cache read before API call
  - [ ] Supabase cache write after successful API call
  - [ ] Structured logging with STAC ID, latency, cache hit/miss
- [ ] Create `prototype_msf/field_geometry_loader.py`:
  - [ ] Load GeoJSON from disk
  - [ ] Validate geometry is Polygon or MultiPolygon
  - [ ] Compute geometry hash for audit trail
- [ ] Create `prototype_msf/soil_json_writer.py`:
  - [ ] Read the RUFAS soil JSON template
        (`input/data/soil/example_soil.json` or a per-run copy)
  - [ ] Convert `TopographicResult.slope_deg` → fraction (m/m) per D1
  - [ ] Set `average_subbasin_slope` to the converted value; leave
        `slope_length` unchanged
  - [ ] Aspect is NOT written to the JSON (RUFAS has no aspect
        input); aspect stays in the Supabase cache for future specs
  - [ ] Write the modified JSON to the expected path (either
        overwriting a per-run copy or to a new file, per the
        runner's convention)

## Simulation runners

- [ ] Modify `prototype_msf/run_prototype.py`:
  - [ ] Add `--field-geometry` CLI argument
  - [ ] Orchestrate: load geometry → call API → write soil JSON → run RUFAS
  - [ ] Preserve backward compatibility (parameter is optional)
- [ ] Modify `prototype_msf/run_prototype_delayed.py` — same pattern
- [ ] Modify `prototype_msf/run_prototype_injection.py` — same pattern
- [ ] Modify `prototype_msf/run_multiyr_sweep.py`:
  - [ ] Use cache aggressively — same geometry across years hits
        cache after first call
  - [ ] Log cache hit rate

## Testing

- [ ] Unit tests for `geomatic_client.py` with mocked responses
- [ ] Regression tests using saved JSON fixtures for 36-1 and 32-1
- [ ] Integration test: end-to-end with real API call to a verified
      field
- [ ] Cache hit test: two consecutive calls produce same STAC ID,
      second call < 2 s

## Documentation

- [ ] Update `prototype_msf/README.md`:
  - [ ] New section "Running with a real field geometry"
  - [ ] Example command line for each script variant
- [ ] Update `prototype_msf/slope_aspect_api.md` if any new API
      behavior is discovered during implementation

## Verification before PR

- [ ] All unit tests pass
- [ ] All regression tests pass (verified slope values match)
- [ ] Cache hit rate ≥ 90% on multi-year sweep of same field
- [ ] `run_multiyr_sweep.py` completes without errors on
      Saint-Zotique 36-1
- [ ] Written soil JSON contains the real API-derived slope value,
      not zero and not the default 0.05
- [ ] No new mypy or Black errors introduced in `prototype_msf/`
- [ ] `openspec validate integrate-slope-aspect-api --strict` passes

## Review

- [ ] Open PR against `dev-msf` (never rebase, per Maxime 2026-07-28)
- [ ] Assign Bilal as reviewer
- [ ] Address all review comments
- [ ] Merge after approval

## Post-merge

- [ ] Archive this change: `openspec archive
      integrate-slope-aspect-api`
- [ ] Update the canonical spec in `openspec/specs/` with the deltas
- [ ] Announce completion in weekly meeting
- [ ] Note any follow-up specs discovered during implementation
      (especially if the empirical sensitivity result (Q2) suggests
      RUFAS core changes are needed to unlock more of the slope
      signal)
