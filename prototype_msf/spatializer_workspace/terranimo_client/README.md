# terranimo_client

**Version 0.3.0** — Blocks 1 and 2 complete.

Python client for the [Terranimo](https://terranimo.world) REST API v1, built for the MSFourrager compaction workstream.

## Overview

Terranimo is a soil-compaction model developed at BFH Bern. It answers one question MSF cannot answer from RUFAS alone: given a soil state and a machine, is driving on this field today acceptable? The API exposes 48 operations; this client wraps the handful MSF actually needs, and does so as a thin transport layer — it authenticates, maps HTTP failures onto typed exceptions, and returns decoded response bodies unchanged. It performs **no unit conversion and no payload defaulting**, because the units are not yet settled (see Known limitations). Endpoint paths and schema names are transcribed verbatim from the OpenAPI 3.0.4 spec, whose local snapshot was verified semantically identical to the live spec on 2026-09-10.

## Installation

Python 3.9 or newer.

```bash
pip install requests python-dotenv
```

Both are already present in the `anaconda3` base environment on this machine (requests 2.32.5).

The package is not published. Import it from the repo root, `C:\Proyectos\terranimo-test\`:

```python
from terranimo_client import TerranimoClient
```

## Configuration

The client needs a Bearer token. Academic keys are issued by Stefan Gfeller (BFH Bern).

Create a `.env` file in the directory you run from:

```
TERRANIMO_API_KEY=<your token>
```

`.env` is already listed in `.gitignore`. **Never commit it, and never paste a token into a console** — Spyder logs console input to `~/.spyder-py3/history.py` in plaintext.

Resolution order:

1. `api_key=` passed to the constructor
2. `TERRANIMO_API_KEY` already exported in the environment
3. `TERRANIMO_API_KEY` from `.env` in the current working directory

If none resolves, the constructor raises `TerranimoAuthError` immediately rather than deferring the failure to the first call.

## Unit conventions

The client converts nothing: every value reaches the API exactly as passed, so it must already be in the unit below. Matric-potential input is **bar**, confirmed by Stefan Gfeller (BFH) on 2026-09-15.

| Parameter | Unit | Notes |
| --- | --- | --- |
| `matricPotential` — input to every calculate endpoint this client wraps (precompression, tyre compaction, Van Genuchten forward) | bar | Confirmed by Stefan Gfeller (BFH) 2026-09-15; matches the spec. Passed as `matric_potential_bar`. Field capacity ≈ 0.33 bar, wilting point ≈ 15 bar |
| `wetness` — input to `calculate_sci` | cbar | Not wrapped by this client. A different field, not `matricPotential`. bar = cbar / 100 |
| `soilWaterSuction` — input to `light/calculate_soil_strength` | cBar | Not wrapped by this client. bar = cBar / 100 |
| `matricPotential` — in `SoilWetnessLayerCompact`, served by `soils/soilwetnesslayers/{soilWetnessUid}` | hPa | Soils catalog endpoint, not a calculation. Not wrapped. bar = hPa / 1000 |
| `tyreLoad` | kg | A mass, per wheel. RUFAS provides whole-tractor mass (`Tractor.mass_kg`, `RUFAS/EEE/tractor.py`), which must be split per wheel. A load in kN (the Terranimo model description's `FW`) converts at ×101.97 kg/kN under standard gravity |
| Van Genuchten forward output (`result`) | m³/m³ | Volumetric fraction, **not** a percentage (Stefan, 2026-09-15). Exposed as `water_content_pct` — the suffix is a misnomer, not renamed here |
| Van Genuchten inverse input (`waterContent`) | % | **Not** m³/m³ — asymmetric with the forward output. `0.25` returned HTTP 500 on 2026-09-10; `25.0` works |
| Van Genuchten inverse output (`result`) | unresolved | The spec gives no unit. Read as bar, measured values (81–1902 for 25 % water content) are implausible |
| `preCompressionOfSoil` (output) | bar (per spec) | Actual unit pending confirmation from Stefan |

## Usage

### Health check

```python
import logging
from terranimo_client import TerranimoClient, TerranimoAuthError, TerranimoError

logging.basicConfig(level=logging.INFO)

client = TerranimoClient()          # key from .env
print(client)                       # api_key=<redacted>

try:
    client.ping()                   # True, or raises
except TerranimoAuthError as exc:
    print(f"Token rejected: {exc}")
except TerranimoError as exc:
    print(f"API unreachable: {exc}")
```

`ping()` raises rather than returning `False`, so "the service is down" stays distinguishable from "your token is wrong".

### Van Genuchten — water content

Computes water content from matric potential.

```python
from terranimo_client import TerranimoClient

client = TerranimoClient()
result = client.van_genuchten_water_content(
    matric_potential_bar=0.33,  # field capacity for loam
    clay_pct=25.0,
    silt_pct=40.0,
    organic_matter_pct=3.5,
    bulk_density_g_per_cm3=1.35,
    top_soil=True,
)
print(f"Water content: {result.water_content_pct} m³/m³")  # fraction, despite the _pct name
```

### Van Genuchten — matric potential

The inverse: computes matric potential from water content. Use it as a **coherence oracle** — it tells you which matric potential actually corresponds to a water content for this soil, so you can catch physically contradictory inputs before feeding them downstream. Skipping this check on 2026-08-26 produced artifact outputs from an incoherent pair (35% water content at 0.5 bar, which for a loam is off by an order of magnitude).

Note the two spec quirks this endpoint carries: short field names (`waterContent`, `clay`, `silt`, `organicMatter`) instead of the `*Percentage` names every other schema uses, and `topSoil` typed as a **number** rather than a boolean.

```python
result = client.van_genuchten_matric_potential(
    water_content_pct=25.0,
    clay_pct=25.0,
    silt_pct=40.0,
    organic_matter_pct=3.5,
    bulk_density_g_per_cm3=1.35,
    top_soil=1,  # number here, not bool — spec inconsistency
)
print(f"Matric potential: {result.matric_potential}")  # unit unresolved
```

`matric_potential` is the one result field with no unit suffix. Stefan confirmed bar for matric-potential *inputs* on 2026-09-15, but the spec gives this response no unit and it is not established that the confirmation covers it — read as bar, the values measured on 2026-09-10 (81–1902 for 25 % water content, depending on `topSoil`) would be implausible.

### Precompression — endpoint 1 of the chain

```python
result = client.precompression(
    water_content_pct=25.0,
    matric_potential_bar=0.33,
    clay_pct=25.0,
    silt_pct=40.0,
    organic_matter_pct=3.5,
    bulk_density_g_per_cm3=1.35,  # topsoil
    top_soil=True,
)
print(f"Precompression: {result.precompression_bar}")
```

**The `top_soil` flag does not change the result.** Testing on 2026-08-26 returned identical values for `True` and `False` across three input pairs; only `bulk_density_g_per_cm3` moves the output. To model a different layer, vary the bulk density — not the flag.

### Tyre compaction risk — endpoint 2 of the chain

The chain calls `precompression()` **twice** — once per layer — then feeds both values in:

```python
SOIL = dict(
    water_content_pct=25.0,
    matric_potential_bar=0.33,
    clay_pct=25.0,
    silt_pct=40.0,
    organic_matter_pct=3.5,
)

top = client.precompression(bulk_density_g_per_cm3=1.35, top_soil=True, **SOIL)
sub = client.precompression(bulk_density_g_per_cm3=1.55, top_soil=False, **SOIL)

decision = client.tyre_for_compaction(
    tyre_uid="traction_michelin_agribib_112r24_114_a8",
    tyre_load_kg=3500,
    tyre_pressure_bar=1.5,
    tyre_pressure_recommended_bar=1.5,
    recent_tillage=False,
    precompression_top_layer_bar=top.precompression_bar,
    precompression_bar=sub.precompression_bar,
    matric_potential_bar=0.33,
)

if decision.is_workable:
    print(f"OK to drive ({decision.verdict})")
else:
    print(f"Do not drive ({decision.verdict})")
```

`decision.verdict` is `"good"`, `"ok"` or `"bad"`; `is_workable` is `True` for the first two and fails safe to `False` on anything unrecognised. `soil_stress_bar` and `soil_strength_bar` are available on the result but **must not be shown to producers** — see Known limitations.

### Logging

The client logs through the standard `logging` module under the `terranimo_client.client` logger — never `print`. At `INFO` it emits one line per request (method, URL, payload **keys** only) and one per response (status, byte count). Payload values and the token are never logged.

### Exceptions

| Exception | Trigger |
| --- | --- |
| `TerranimoError` | Base class; also transport failures and unparseable bodies |
| `TerranimoAuthError` | HTTP 401 / 403, or a missing key at construction |
| `TerranimoValidationError` | HTTP 400 |
| `TerranimoServerError` | HTTP 500+ |
| `TerranimoTimeoutError` | Request exceeded the timeout |

Each carries `.status_code` and `.response_text`. The body matters: Terranimo returns a `ProblemDetails` object on 400/401/403/500, and since the spec documents **zero request examples**, that body is usually the only description of what a rejected payload got wrong.

## Known limitations

**Output units are unresolved.** Input units are settled — see [Unit conventions](#unit-conventions). Outputs are not: `preCompressionOfSoil`, `soilStress` and `soilStrength` are declared `[bar]` but unconfirmed, and replaying the August payloads with matric potential in bar (2026-09-16, `stefan_replay_2026-09-16.csv`) returned precompression values of 0.011–0.194, whose plausibility cannot be judged without a sourced reference range. One field in the entire spec is declared `[kPa]` (`SoilStressCalculationResponse.result`) against 33 declared `[bar]`. Consequently:

- Treat the categorical verdict (`good` / `ok` / `bad`) as the reliable output.
- Do **not** surface absolute `soilStress` / `soilStrength` values to producers.
- Any result computed before 2026-09-15 that passed matric potential on a cbar or hPa scale must be recomputed with values in bar.

Full detail: `MSF-Notes\Terranimo\00-Terranimo-Status-Consolidated-2026-09-10.md`.

**No retries.** One call in, one call out. Terranimo has no batch endpoint (0 array request bodies in the spec), so a per-zone, per-day pipeline issues one HTTP call per calculation.

## Roadmap

| Block | Scope | Status |
| --- | --- | --- |
| **1** | Package skeleton, config, exceptions, auth, `ping()` | **DONE** — verified live 2026-09-10 |
| **2** | Calculation methods — Van Genuchten (both variants), precompression, tyre compaction risk | **DONE** |
| **3** | Live testing + chain validation | PENDING |
| **4** | Documentation + Stefan follow-up | PENDING |

Block 3 re-runs the two-endpoint chain with matric potential in bar and compares against the August results. Block 4 closes the remaining output-unit questions with Stefan, per endpoint, and reconciles the older vault notes against whatever he confirms.
