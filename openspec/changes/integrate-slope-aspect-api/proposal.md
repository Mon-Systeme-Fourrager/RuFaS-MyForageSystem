# Integrate Slope/Aspect API into RUFAS Simulation Pipeline

**Date:** 2026-07-29
**Author:** Andrea Katherín Carranza-Díaz
**Status:** Draft — pending team validation
**Repo:** RuFaS-MyForageSystem
**Branch:** research/andrea-msf-prototype

## Why

RUFAS treats each field as a flat point — the simulation engine
computes runoff without considering the actual topography of the
terrain. When we run simulations without topographic data, the model
can recommend applying manure on a day that appears safe but that on
a sloped field would generate significant runoff toward a
watercourse.

Jérémie Durand's LiDAR API (verified 2026-07-24 with two Quebec
fields: Saint-Zotique 36-1 at 1.298° slope and field 32-1 at 1.249°
slope) resolves this gap. It uses MRNF Quebec LiDAR data to compute
slope and aspect for any field polygon that MSF already tracks. This
change wires the API into the simulation loop so per-field
topographic realism becomes the default, and establishes the first
entry point in the codebase for the geomatic products required to
support field-specific decisions.

## What Changes

- Add a **topographic input service** that calls Jérémie's LiDAR API
  with a field geometry and returns slope, aspect, and a STAC ID.

- Add a **STAC ID cache** in Supabase so re-simulating the same field
  within a sweep does not repeat API calls (cold call ~7 s, cached
  ~1.4 s).

- Add a **field CSV writer** that materializes API responses into the
  `angle_of_slope` and `angle_of_slope_aspect` columns of the RUFAS
  Zone CSV, consumed by `input_manager` via the existing CSV pipeline.

- Add **unit conversion logic** — the API returns slope in degrees;
  RUFAS SCS-CN uses fraction (m/m); Terranimo uses percent. Conversion
  is centralized in the service to prevent silent misuse downstream.

- Add **error handling** for API failures (network, invalid geometry,
  timeout, no LiDAR coverage) with a fail-fast default and clear
  logging.

- Modify `run_prototype.py`, `run_prototype_delayed.py`,
  `run_prototype_injection.py`, and `run_multiyr_sweep.py` to accept
  a field geometry as input and orchestrate the API call → CSV write
  → RUFAS simulation flow.

## Not in scope

- **Modifying RUFAS core.** The hardcoded
  `SLOPE_FACTOR_FOR_LAND = 0.05` in `Soil/Water` remains untouched in
  this change. See Open Questions.
- **Aspect-driven radiation modeling.** RUFAS validates aspect but
  does not appear to consume it in current equations. Feeding aspect
  for future use only.
- **Terranimo compaction integration.** Waiting for external model
  decision.
- **Multi-objective optimization.** Requires compaction model first.
- **Fields outside Quebec.** LiDAR coverage is provincial.
- **Batch geometries.** This change handles one field at a time.
  Multi-field orchestration is a future spec.

## Impact

### Files added

- `prototype_msf/geomatic_client.py` — HTTP client for Jérémie's API,
  with response caching by STAC ID.
- `prototype_msf/field_geometry_loader.py` — loads and validates a
  field geometry (GeoJSON) from disk.
- `prototype_msf/field_csv_writer.py` — materializes API responses
  into RUFAS Zone CSV columns.
- `prototype_msf/unit_conversions.py` — centralizes slope degree ↔
  fraction ↔ percent conversion.
- `prototype_msf/tests/test_geomatic_client.py` — unit tests with
  mocked API responses.

### Files modified

- `prototype_msf/run_prototype.py` — accepts field geometry
  parameter, orchestrates API call → CSV write → RUFAS flow.
- `prototype_msf/run_prototype_delayed.py`,
  `run_prototype_injection.py` — same orchestration pattern.
- `prototype_msf/run_multiyr_sweep.py` — uses STAC cache to avoid
  repeat API calls across years of the same field.

### Files unchanged

- All of `RUFAS/`. This change stays out of the core (see Open
  Questions). The field geometry parameter is optional — existing
  simulations remain reproducible without the API.
- Existing prototype outputs (`multiyr_sweep_results_full.csv`,
  analysis scripts).

### Dependencies

- No new Python packages beyond what the Open-Meteo bridge already
  brought in (`requests` for HTTP, `json` for parsing).
- Supabase client for cache reads/writes (already used elsewhere in
  the project).

### Documentation

- Update `prototype_msf/README.md` with instructions for running a
  simulation with a real field geometry.

### Testing

- Unit tests for `geomatic_client.py` with mocked API responses:
  success, timeout, invalid geometry, malformed JSON, no LiDAR
  coverage.
- One regression test using the two verified Quebec fields
  (Saint-Zotique 36-1 and field 32-1). Slope values must match what
  was recorded on 2026-07-24 within 0.001° tolerance.
- No changes to existing RUFAS test coverage.

### Data audit trail

- Every API response is logged with STAC ID, timestamp, and geometry
  hash so the source of any simulation input is traceable — per the
  no-fabrication rule in root CLAUDE.md.

### Deployment

- No production deployment. Prototype work in `prototype_msf/` on
  `research/andrea-msf-prototype` branch.
- Follows the ingestion pipeline patterns established by Rami (AWS
  Step Functions, Lambda, S3) — no new pipeline architecture.

## Open Questions

**Q1 — Unit conversion boundaries.**
The API returns slope in degrees. RUFAS SCS-CN expects fraction
(m/m). Terranimo (when integrated later) expects percent. The
conversion must happen exactly once, at a documented boundary.
*Resolution path:* implement all conversions in
`unit_conversions.py`, document the expected unit at every function
signature that touches slope, and add tests that catch silent
misuse.

**Q2 — Hardcoded slope constant.**
RUFAS Soil/Water uses a hardcoded `SLOPE_FACTOR_FOR_LAND = 0.05`
constant. We do not know whether this is a deliberate scientific
simplification or a leftover placeholder. If it is a placeholder,
this change delivers the input but does not consume it in the
affected equations — a follow-up spec would replace the constant.
*Resolution path:* email Kevin Panke-Buisse (USDA) — he confirmed
the RUFAS modules are stable and can clarify design intent.

**Q3 — CSV input propagation.**
RUFAS accepts `angle_of_slope` as a Zone-level input via CSV, but
we have not confirmed that changing this value actually affects
simulation outputs. It is possible the CSV value is loaded but
silently overridden by the constant of Q2.
*Resolution path:* controlled experiment before implementation —
two identical simulations with different slope values (e.g. 0.05
vs 0.30), compare outputs. If results differ, CSV input is
respected. If identical, the change scope must expand.

**Q4 — Client-side cache location.**
STAC IDs are geometry-derived and Jérémie's server caches responses
across sessions. Adding a Supabase-side cache would avoid 6–8 s
cold calls on the first invocation for a field. Cost: added
schema complexity.
*Resolution path:* discuss with Bilal — recommendation is to cache
if we anticipate ≥10 fields per farm and each field is queried in
multiple sweeps per year.

**Q5 — Fallback for fields without LiDAR coverage.**
Fields outside Quebec or recently added farms may have no MRNF
LiDAR record.
*Resolution path:* fail-fast with an explicit error and log the
gap. Do not silently default to flat-field — that would violate
the no-fabrication rule.

**Q6 — Disjoint MultiPolygon behavior.**
Fields with multiple non-contiguous rings have not been tested
against the API.
*Resolution path:* controlled test with a synthetic MultiPolygon
before production use.

## References

- Jérémie Durand, McGill — LiDAR MRNF Quebec API (personal
  communication, 2026)
- MRNF Quebec — LiDAR provincial data source (public)
- Kevin Panke-Buisse, USDA — RUFAS module stability confirmed
  (email, 2026-07-24)
- Williams 1975 — MUSLE erosion model (basis of RUFAS sediment)
- Neitsch 2011 — SWAT soil-water (basis of RUFAS SCS-CN runoff)
- Vadas & Powell 2013 — SurPhos (RUFAS phosphorus module)
- prototype_msf/slope_aspect_api.md (commit c34d86b) — verified
  API behavior
- jeremie_slope_36-1.json, jeremie_aspect_36-1.json,
  jeremie_slope_32-1.json — authoritative API responses
  (C:\Proyectos\)
- Root CLAUDE.md — data integrity and pipeline reuse conventions

## Design ready

Once Q1–Q6 are answered and the SLOPE_FACTOR_FOR_LAND experiment
(Q3) confirms input propagation, this change is ready for
implementation via the tasks in `tasks.md`.
