"""
terranimo_client — Python client for the Terranimo REST API v1, MSFourrager

Wraps https://services.terranimo.world/api/v1 for the MSF compaction
workstream. Endpoint paths and schema names are transcribed from the
OpenAPI 3.0.4 spec; see config.py for provenance.

Pass-through mode: no unit conversion is performed anywhere. Parameter names
carry the unit the caller must supply, and returned values are stored exactly
as the API sent them. See models.py and the consolidated status note.

Block 1 provides construction, auth, error mapping and ``ping()``.
Block 2 adds the four calculation methods. Catalog lookups and the test suite
follow — see README.md.
"""

from .client import TerranimoClient
from .exceptions import (
    TerranimoAuthError,
    TerranimoError,
    TerranimoServerError,
    TerranimoTimeoutError,
    TerranimoValidationError,
)
from .models import (
    VERDICT_VALUES,
    PrecompressionResult,
    TyreCompactionResult,
    VanGenuchtenMatricPotentialResult,
    VanGenuchtenWaterContentResult,
)

__version__ = "0.3.0"

__all__ = [
    # client
    "TerranimoClient",
    # exceptions
    "TerranimoError",
    "TerranimoAuthError",
    "TerranimoValidationError",
    "TerranimoServerError",
    "TerranimoTimeoutError",
    # models
    "VanGenuchtenWaterContentResult",
    "VanGenuchtenMatricPotentialResult",
    "PrecompressionResult",
    "TyreCompactionResult",
    "VERDICT_VALUES",
    "__version__",
]
