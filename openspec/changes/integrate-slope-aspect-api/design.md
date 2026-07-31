# Design — Slope/Aspect API Integration

## Context

The MSFourrager prototype currently runs RUFAS simulations with
generic topographic assumptions. This design document specifies how
Jérémie Durand's LiDAR API becomes the source of truth for slope and
aspect per field, and how the resulting values flow through the
existing RUFAS input pipeline without modifying RUFAS core.

The change targets `prototype_msf/` only. If a future spec promotes
this pattern into RUFAS core, the full `dev-msf` CI gates apply
then (mypy strict, Black 120, two reviewers, changelog).

## What we know about the API — verified on disk

*Source: `C:\Proyectos\jeremie_*.json`*
*Documentation: `prototype_msf/slope_aspect_api.md` (commit c34d86b)*

### Confirmed behavior

- **Input:** field polygon as GeoJSON — Polygon or MultiPolygon
- **Output:** slope (degrees), aspect (degrees from North)
- **STAC ID:** deterministic, geometry-derived — usable as cache key
- **MultiPolygon:** accepted without client-side unwrap
- **Latency:** 6–8 s cold, ~1.4 s cached (server-side cache persists
  across sessions)

### Verified with real MSF field polygons

| Field | Area | Slope | Aspect | STAC ID | Cold latency |
|---|---|---|---|---|---|
| 36-1 | 18.87 ha | 1.298° (2.30%) | 80.18° (E) | `lidar_slope_geom_e6df18cd` | 7.08 s |
| 32-1 | 12.47 ha | 1.249° (2.22%) | — | `lidar_slope_geom_6f481eb4` | 8.39 s |

## What we know about RUFAS current state

*Source: read-only inspection by Claude Code, 2026-07-29*

- RUFAS accepts one slope input: `average_subbasin_slope` (fraction
  m/m, default 0.05), declared in the `SoilData` dataclass at
  `RUFAS/biophysical/field/soil/soil_data.py:199`. Populated from
  `input/data/soil/example_soil.json`.
- Companion field: `slope_length` (meters, default 3) at the same
  dataclass, line 226. Used alongside `average_subbasin_slope` by
  the same MUSLE consumer.
- Sole consumer: `RUFAS/biophysical/field/soil/soil_erosion.py:86`
  passes both fields to `_determine_topographic_factor` for MUSLE
  sediment yield. No other RUFAS module reads either field.
- No aspect input exists in RUFAS. No field, no variable, no
  validation, no consumer equation. `RUFAS/data_validator.py`
  contains zero slope or aspect references.
- No Zone CSV, no `angle_of_slope` column, no CSV-based field-input
  format exists in RUFAS.
- No script under `prototype_msf/` currently passes slope or aspect
  to RUFAS.

## Architecture

```
   MSF field polygon (GeoJSON)
              │
              ▼
   geomatic_client.py ─── STAC cache (Supabase, optional)
              │
              ▼
   API call → slope°, aspect°, STAC ID
              │
              ▼
   unit_conversions.py (degrees → fraction for RUFAS)
              │
              ▼
   soil_json_writer.py → example_soil.json (existing RUFAS input)
              │
              ▼
   RUFAS TaskManager.start() → input pipeline
              │
              ▼
   RUFAS simulation
              │
              ▼
   Manure timing recommendation
```

## Design decisions

### D1 — Unit conversion is centralized

**Decision:** all slope-unit conversions happen in
`unit_conversions.py`, with explicit function names indicating the
unit boundary.

**Rationale:** Q1 in the proposal identifies that three components
speak three different units (degrees from API, fraction for MUSLE,
percent for Terranimo). Silent conversion at ambiguous boundaries
is the classic source of hard-to-detect scientific bugs. A single
module with clear function names makes the boundary auditable.

**Interface:**
```python
def degrees_to_fraction(slope_deg: float) -> float: ...
def degrees_to_percent(slope_deg: float) -> float: ...
def fraction_to_percent(slope_frac: float) -> float: ...
```

### D2 — Cache in Supabase, keyed by STAC ID

**Decision:** cache API responses in a Supabase table keyed by STAC
ID, with columns for slope, aspect, timestamp, and geometry hash.

**Rationale:** Q3 in the proposal weighs client-side caching. The
STAC ID being deterministic per geometry means we can safely cache
without invalidation logic — the same field always produces the
same STAC ID. Cold calls at 6–8 s per field become intolerable at
scale (multi-year sweep × N fields).

**Table schema (proposed):**
```sql
CREATE TABLE topographic_cache (
    stac_id TEXT PRIMARY KEY,
    slope_deg REAL NOT NULL,
    aspect_deg REAL,
    geometry_hash TEXT NOT NULL,
    api_response_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    field_reference TEXT
);
```

### D3 — Fail-fast on missing LiDAR coverage

**Decision:** if the API returns no data (field outside Quebec, or
outside MRNF coverage), raise an explicit error. Do not default to
flat-field values.

**Rationale:** Q4 in the proposal. The no-fabrication rule in root
CLAUDE.md requires that missing data be surfaced, not silently
substituted. A flat-field default would silently invalidate results
in a way that violates the audit trail requirement.

### D4 — Follow Rami's ingestion pipeline patterns

**Decision:** the topographic input service integrates with the
existing AWS Step Functions / Lambda / S3 pattern established for
weather data ingestion, not a new architecture.

**Rationale:** explicit requirement from Maxime at the 2026-07-28
weekly. Reuse ensures consistency and simplifies future integration
of other geomatic products (flow accumulation, distance to
watercourse, soil series map).

### D5 — Field geometry loaded from disk, not database

**Decision:** for prototype phase, field geometries are loaded from
GeoJSON files on disk. Database integration is deferred until the
prototype pattern is validated.

**Rationale:** keeps this change scoped. MSF already tracks field
geometries in its production database — that integration is a
future spec.

## Testing strategy

### Unit tests (mocked API)

- Success path — well-formed response returns correct slope, aspect,
  STAC ID.
- Timeout — client raises `APITimeoutError` after configured limit.
- Invalid geometry — client raises `APIGeometryError` with API
  response detail.
- Malformed JSON — client raises `APIResponseError`.
- No LiDAR coverage — client raises `APICoverageError`.

### Regression tests (real API, real geometries)

- Field 36-1 (Saint-Zotique) — slope must equal 1.298° ± 0.001°.
- Field 32-1 — slope must equal 1.249° ± 0.001°.
- STAC IDs must match values recorded 2026-07-24.

### Integration tests

- End-to-end: geometry file → API call → CSV write → RUFAS
  simulation → non-null output.
- Cache hit path: two consecutive calls with same geometry produce
  identical STAC ID; second call latency < 2 s.

### The empirical sensitivity experiment (Q2)

Before implementation begins:

1. Copy `input/data/soil/example_soil.json` to two variants that
   differ only in `average_subbasin_slope` (0.05 vs 0.30, m/m).
2. Wire two `prototype_root_slope*.json` chains pointing to each
   variant.
3. Run `python prototype_msf/run_prototype.py` twice, moving the
   `output/` directory aside between runs (RUFAS overwrites by
   default per `clear_output_directory=True`).
4. Compare `output/CSVs/msf_prototype_saved_variables_*.csv` from
   the two runs on: MUSLE sediment yield, nitrate runoff, per-layer
   nitrogen at day 30.
5. Quantify the delta as a percentage of the baseline. This is the
   sensitivity coefficient the paper will cite.

Result of this experiment must be documented in the spec before
starting the tasks.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Slope input has negligible effect on prototype outputs | Medium | Medium | Q2 empirical sensitivity experiment before coding |
| API downtime blocks all sweeps | Low | High | Fail-fast + logging (Q4) |
| Unit conversion bug (degrees vs fraction) | High | High | Centralized module + tests (D1) |
| MultiPolygon disjoint case breaks | Low | Medium | Q5 test with synthetic geometry |
| Cache invalidation edge case | Low | Low | Deterministic STAC ID makes stale cache impossible |

## Migration path (if this change is later promoted to RUFAS core)

- Move `geomatic_client.py`, `unit_conversions.py`, and
  `soil_json_writer.py` into an appropriate RUFAS submodule under
  strict mypy + Black + two-reviewer gates.
- Refactor tests to conform to RUFAS test conventions.
- Update the RUFAS soil-input pipeline to call the topographic
  service natively instead of relying on pre-populated JSON files.

## Open items (resolve before starting tasks)

- Q1–Q5 in the proposal must be addressed.
- The Q2 empirical sensitivity experiment must be run and its outcome recorded.
- Bilal review of this design document.
