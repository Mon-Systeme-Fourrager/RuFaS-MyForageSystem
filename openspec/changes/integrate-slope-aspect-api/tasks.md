# Tasks — Slope/Aspect API Integration

## Pre-implementation validation

- [ ] Run the SLOPE_FACTOR_FOR_LAND experiment (proposal Q3):
  - [ ] Prepare two Zone CSVs identical except for `angle_of_slope`
        (0.05 vs 0.30)
  - [ ] Run RUFAS with each CSV, same field otherwise
  - [ ] Compare outputs and record result in this file
- [ ] Email Kevin Panke-Buisse (USDA) about SLOPE_FACTOR_FOR_LAND
      design intent (Q2)
- [ ] Review with Bilal — pipeline reuse patterns (Q6)
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
- [ ] Create `prototype_msf/field_csv_writer.py`:
  - [ ] Read RUFAS Zone CSV template
  - [ ] Populate `angle_of_slope` and `angle_of_slope_aspect` from
        `TopographicResult`
  - [ ] Convert degrees → fraction per D1
  - [ ] Write final CSV to expected path

## Simulation runners

- [ ] Modify `prototype_msf/run_prototype.py`:
  - [ ] Add `--field-geometry` CLI argument
  - [ ] Orchestrate: load geometry → call API → write CSV → run RUFAS
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
- [ ] Output CSV contains real slope value, not zero and not 0.05
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
      (especially if Q2 result requires touching RUFAS core)
