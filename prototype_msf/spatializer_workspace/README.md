# Spatializer Workspace (MSFourrager)

Development workspace for the MSFourrager Spatializer
pipeline.

## Setup

1. Copy `.env.example` to `.env` and fill in credentials:
   `TERRANIMO_API_KEY=<your-terranimo-api-key>`

2. Install dependencies (see individual module READMEs).

## Modules

- `terranimo_client/` — Python client for Terranimo API (v0.3.0)
- `weather_client/` — Open-Meteo bridge
- `spatializer_v2/` — Main pipeline
  - `evaluators/` — Compaction, Weather, Runoff
  - `adapters/` — RUFAS ↔ Evaluator bridges
  - `scripts/` — Test runners

## Status

Work in progress. See CHANGELOG in terranimo_client/ for
versioning.

### Recent verification

**Confirmed by Stefan Gfeller (BFH, Terranimo) on 2026-09-15:**
- `matricPotential` unit is bar (not cbar) in all calculate 
  endpoints (VG forward, precompression, tyre_for_compaction).

**Documented from OpenAPI spec:**
- `tyreLoad` unit is kg (open question Q2: mass or force — 
  see Questions-log.md).
- RUFAS provides whole-tractor mass (`Tractor.mass_kg`), which 
  must be divided per wheel before passing to the API.

**Empirically verified (2026-09-10):**
- Van Genuchten forward output is in m³/m³ (volumetric fraction, 
  not percentage).

**Open questions with Stefan (pending response as of 2026-09-16):**
- Output unit of `preCompressionOfSoil` (spec declares bar; 
  behavior under investigation).
- Output unit of VG inverse endpoint (spec does not declare).
- Model validity for clay > 18% (calibration range 5-18%, 
  Stefan meeting 2026-08-17).
