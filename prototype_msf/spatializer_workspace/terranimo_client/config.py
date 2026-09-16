"""
config.py — Terranimo API client, MSFourrager

Static configuration for the Terranimo REST API v1.

Every constant here is transcribed from the OpenAPI 3.0.4 specification:
    https://services.terranimo.world/swagger/v1/swagger.json
Local snapshot (verified semantically identical to live on 2026-09-10):
    MSF-Notes/Terranimo/05-References/terranimo_openapi_LIVE_2026-09-10.json

Nothing in this module is inferred. Endpoint paths are copied verbatim from
the spec's ``paths`` keys, minus the ``/api/v1`` prefix carried by BASE_URL.
"""

from typing import Final

# --------------------------------------------------------------------------
# Service
# --------------------------------------------------------------------------

#: Root of the Terranimo REST API v1. Endpoint constants below are relative
#: to this and are joined by TerranimoClient without a trailing slash.
BASE_URL: Final[str] = "https://services.terranimo.world/api/v1"

# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------

#: GET. Liveness + auth check. Spec declares a 200 with NO response body.
ENDPOINT_PING: Final[str] = "/ping"

#: POST. Computes matric potential from water content.
#: Request schema: MualemVanGenuchtenForMatricPotentialCalculationRequest
ENDPOINT_VG_MATRIC_POTENTIAL: Final[str] = (
    "/calculations/calculate_mualem_van_genuchten_for_matric_potential"
)

#: POST. Computes water content from matric potential.
#: Request schema: MualemVanGenuchtenForWaterContentCalculationRequest
ENDPOINT_VG_WATER_CONTENT: Final[str] = (
    "/calculations/calculate_mualem_van_genuchten_for_water_content"
)

#: POST. Endpoint 1 of the compaction chain.
#: Request schema: SoilPrecompressionRequest -> SoilPrecompressionResponse
ENDPOINT_PRECOMPRESSION: Final[str] = "/calculations/calculate_precompression_of_soil"

#: POST. Endpoint 2 of the compaction chain. Returns soilStress, soilStrength
#: and the categorical result (good | ok | bad).
#: Request schema: CalculateWheelForCompactionRiscDecisionRequest
ENDPOINT_TYRE_COMPACTION: Final[str] = (
    "/calculations/calculate_tyre_for_compaction_risc_decision"
)

# --------------------------------------------------------------------------
# Transport
# --------------------------------------------------------------------------

#: Per-request timeout. Stefan quoted "<30 sec per call" in the 2026-08-17
#: meeting; the spec itself documents no timing guarantee.
DEFAULT_TIMEOUT_SECONDS: Final[int] = 30

#: Environment variable holding the Bearer token. Loaded from a .env file
#: when TerranimoClient is constructed without an explicit api_key.
API_KEY_ENV_VAR: Final[str] = "TERRANIMO_API_KEY"
