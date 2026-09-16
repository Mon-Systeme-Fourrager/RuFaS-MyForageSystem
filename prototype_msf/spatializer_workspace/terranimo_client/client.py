"""
client.py — Terranimo API client, MSFourrager

Transport layer for the Terranimo REST API v1.

Source of truth for endpoints, schemas and status codes is the OpenAPI 3.0.4
specification:
    https://services.terranimo.world/swagger/v1/swagger.json
Local snapshot verified semantically identical to live on 2026-09-10:
    MSF-Notes/Terranimo/05-References/terranimo_openapi_LIVE_2026-09-10.json

Scope of this block
-------------------
Construction, authentication, error mapping, and the ``/ping`` health check.
Calculation methods (Van Genuchten, precompression, compaction risk) are
deliberately absent — see the roadmap in README.md.

Unit warning
------------
This client does NOT convert units. Stefan Gfeller (BFH) confirmed on
2026-09-15 that ``matricPotential`` is in bar on every calculate endpoint,
matching the spec; the one ``[hPa]`` declaration belongs to a soils catalog
endpoint, not a calculation. Output units are a separate matter:
``preCompressionOfSoil``, ``soilStress`` and ``soilStrength`` are declared
``[bar]`` but remain unconfirmed, so absolute values returned by the API
must not be treated as validated. See:
    MSF-Notes/Terranimo/00-Terranimo-Status-Consolidated-2026-09-10.md
"""

import logging
import os
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

from .config import (
    API_KEY_ENV_VAR,
    BASE_URL,
    DEFAULT_TIMEOUT_SECONDS,
    ENDPOINT_PING,
    ENDPOINT_PRECOMPRESSION,
    ENDPOINT_TYRE_COMPACTION,
    ENDPOINT_VG_MATRIC_POTENTIAL,
    ENDPOINT_VG_WATER_CONTENT,
)
from .exceptions import (
    TerranimoAuthError,
    TerranimoError,
    TerranimoServerError,
    TerranimoTimeoutError,
    TerranimoValidationError,
)
from .models import (
    PrecompressionResult,
    TyreCompactionResult,
    VanGenuchtenMatricPotentialResult,
    VanGenuchtenWaterContentResult,
)

logger = logging.getLogger(__name__)


class TerranimoClient:
    """
    Thin, synchronous client for the Terranimo REST API v1.

    The client holds no session state beyond credentials and transport
    settings, and performs no retries: one call in, one call out.

    Examples
    --------
    >>> client = TerranimoClient()            # key from .env
    >>> client.ping()
    True
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        base_url: str = BASE_URL,
    ) -> None:
        """
        Initialize the client.

        Parameters
        ----------
        api_key
            Bearer token. When ``None``, a ``.env`` file is loaded from the
            current working directory and the token is read from the
            ``TERRANIMO_API_KEY`` environment variable.
        timeout
            Per-request timeout in seconds.
        base_url
            API root. Overridable for testing against a stub.

        Raises
        ------
        TerranimoAuthError
            If no API key was passed and none could be resolved from the
            environment. Failing here is deliberate: an unauthenticated
            client would fail on every one of the 48 operations.
        ValueError
            If ``timeout`` is not a positive number.
        """
        if timeout <= 0:
            raise ValueError(f"timeout must be positive, got {timeout}")

        if api_key is None:
            # override=False: a token already exported in the environment
            # wins over the .env file.
            load_dotenv(override=False)
            api_key = os.getenv(API_KEY_ENV_VAR)
            logger.debug(
                "API key resolved from environment variable %s", API_KEY_ENV_VAR
            )

        if not api_key:
            raise TerranimoAuthError(
                f"No API key provided and {API_KEY_ENV_VAR} is unset or empty. "
                f"Pass api_key= explicitly, or place {API_KEY_ENV_VAR}=<token> "
                f"in a .env file in the working directory."
            )

        self.api_key: str = api_key
        self.base_url: str = base_url.rstrip("/")
        self.timeout: int = timeout

        # accept: text/plain matches what was verified working in the
        # 2026-08-26 session. The spec also offers application/json and
        # text/json for every response; bodies are JSON either way.
        self.headers: Dict[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "accept": "text/plain",
        }

    def __repr__(self) -> str:
        """Return a representation that never exposes the API key."""
        return (
            f"{type(self).__name__}(base_url={self.base_url!r}, "
            f"timeout={self.timeout}, api_key=<redacted>)"
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """
        Issue one HTTP request and map failures onto Terranimo exceptions.

        Returns the raw :class:`requests.Response` so callers can decide
        whether to parse a body — ``/ping`` has none.

        Parameters
        ----------
        method
            HTTP verb, e.g. ``"GET"`` or ``"POST"``.
        endpoint
            Path relative to ``base_url``, e.g. ``"/ping"``.
        payload
            JSON request body, or ``None`` for bodyless requests.

        Raises
        ------
        TerranimoTimeoutError
            The request exceeded ``self.timeout``.
        TerranimoAuthError
            HTTP 401 or 403.
        TerranimoValidationError
            HTTP 400.
        TerranimoServerError
            HTTP 500 or above.
        TerranimoError
            Any other non-2xx status, or a transport failure that is not a
            timeout (DNS, refused connection, TLS).
        """
        url = f"{self.base_url}{endpoint}"
        logger.info(
            "%s %s (payload keys: %s)",
            method,
            url,
            sorted(payload) if payload else "none",
        )

        try:
            response = requests.request(
                method,
                url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            raise TerranimoTimeoutError(
                f"{method} {url} timed out after {self.timeout}s"
            ) from exc
        except requests.RequestException as exc:
            raise TerranimoError(f"{method} {url} failed: {exc}") from exc

        logger.info(
            "%s %s -> HTTP %d (%d bytes)",
            method,
            url,
            response.status_code,
            len(response.content),
        )

        self._raise_for_status(response, method, url)
        return response

    @staticmethod
    def _raise_for_status(
        response: requests.Response, method: str, url: str
    ) -> None:
        """
        Translate a non-2xx response into the matching Terranimo exception.

        The response body is attached verbatim: for 400/401/403/500 the spec
        returns a ``ProblemDetails`` object, which is where the actual reason
        lives.
        """
        status = response.status_code
        if 200 <= status < 300:
            return

        body = response.text or None
        message = f"{method} {url} returned HTTP {status}"

        if status in (401, 403):
            raise TerranimoAuthError(
                message, status_code=status, response_text=body
            )
        if status == 400:
            raise TerranimoValidationError(
                message, status_code=status, response_text=body
            )
        if status >= 500:
            raise TerranimoServerError(
                message, status_code=status, response_text=body
            )
        raise TerranimoError(message, status_code=status, response_text=body)

    @staticmethod
    def _parse_json(response: requests.Response) -> Dict[str, Any]:
        """
        Parse a response body as JSON.

        Terranimo serves JSON under ``text/plain`` when that is the requested
        accept type, so content-type is not checked — only parseability.

        Raises
        ------
        TerranimoError
            If the body is empty or is not valid JSON.
        """
        if not response.content:
            raise TerranimoError(
                f"Expected a JSON body from {response.url} "
                f"but the response was empty",
                status_code=response.status_code,
            )
        try:
            return response.json()
        except ValueError as exc:
            raise TerranimoError(
                f"Response from {response.url} is not valid JSON: {exc}",
                status_code=response.status_code,
                response_text=response.text,
            ) from exc

    def _post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        POST ``payload`` to ``endpoint`` and return the decoded JSON body.

        Parameters
        ----------
        endpoint
            Path relative to ``base_url``, e.g.
            ``config.ENDPOINT_PRECOMPRESSION``.
        payload
            Request body. Sent as-is: no unit conversion, no defaulting, no
            key renaming. The spec documents zero examples and marks nothing
            required, so validation is left to the API.

        Returns
        -------
        Dict[str, Any]
            Decoded response body.

        Raises
        ------
        TerranimoError
            Or one of its subclasses — see :meth:`_request`.
        """
        response = self._request("POST", endpoint, payload)
        return self._parse_json(response)

    def _get(self, endpoint: str) -> Dict[str, Any]:
        """
        GET ``endpoint`` and return the decoded JSON body.

        Not suitable for ``/ping``, whose 200 response carries no body per
        the spec — use :meth:`ping` instead.

        Raises
        ------
        TerranimoError
            Or one of its subclasses — see :meth:`_request`.
        """
        response = self._request("GET", endpoint)
        return self._parse_json(response)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def ping(self) -> bool:
        """
        Check that the API is reachable and the Bearer token is accepted.

        Endpoint: ``GET /api/v1/ping``. The spec declares the 200 response
        with no content, so this returns a bool rather than a body.

        Returns
        -------
        bool
            ``True`` when the API answered 2xx.

        Raises
        ------
        TerranimoAuthError
            The token was rejected (401/403).
        TerranimoTimeoutError
            No answer within the timeout.
        TerranimoError
            Any other failure.

        Notes
        -----
        Failures raise rather than returning ``False``, so a caller can tell
        "the service is down" apart from "your token is wrong".
        """
        self._request("GET", ENDPOINT_PING)
        logger.info("Ping OK")
        return True

    # ------------------------------------------------------------------ #
    # Calculations
    #
    # Pass-through mode: every value below is sent to the API verbatim.
    # No unit conversion is performed anywhere in this class. Parameter
    # names carry the unit the caller is expected to supply; where that
    # unit is not yet confirmed, the docstring says so explicitly.
    # ------------------------------------------------------------------ #

    def van_genuchten_water_content(
        self,
        matric_potential_bar: float,
        clay_pct: float,
        silt_pct: float,
        organic_matter_pct: float,
        bulk_density_g_per_cm3: float,
        top_soil: bool,
    ) -> VanGenuchtenWaterContentResult:
        """
        Calculate water content from matric potential (Mualem-Van Genuchten).

        Endpoint: ``/calculations/calculate_mualem_van_genuchten_for_water_content``
        Request schema: ``MualemVanGenuchtenForWaterContentCalculationRequest``

        Parameters
        ----------
        matric_potential_bar
            Matric potential in bar, confirmed by Stefan Gfeller (BFH) on
            2026-09-15 and matching the spec's ``[bar]`` declaration. The
            value is sent verbatim — this client does not convert it.
        clay_pct
            Clay content ``[%]``.
        silt_pct
            Silt content ``[%]``.
        organic_matter_pct
            Organic matter content ``[%]``.
        bulk_density_g_per_cm3
            Bulk density ``[g/cm3]``.
        top_soil
            ``True`` for topsoil, ``False`` for subsoil. The spec types this
            as ``boolean`` here — but as ``number`` on the matric-potential
            variant, a known spec inconsistency.

        Returns
        -------
        VanGenuchtenWaterContentResult

        Raises
        ------
        TerranimoValidationError
            The API rejected the payload (HTTP 400).
        TerranimoAuthError
            Authentication failed (HTTP 401/403).
        TerranimoServerError
            Terranimo-side failure (HTTP 500+).
        TerranimoTimeoutError
            No response within the timeout.
        TerranimoError
            Any other failure, including a response missing ``result``.
        """
        payload = {
            "matricPotential": matric_potential_bar,
            "clayPercentage": clay_pct,
            "siltPercentage": silt_pct,
            "organicMatterPercentage": organic_matter_pct,
            "bulkDensity": bulk_density_g_per_cm3,
            "topSoil": top_soil,
        }
        response_json = self._post(ENDPOINT_VG_WATER_CONTENT, payload)
        return VanGenuchtenWaterContentResult(
            water_content_pct=self._require_field(
                response_json, "result", ENDPOINT_VG_WATER_CONTENT
            ),
            raw_response=response_json,
        )

    def van_genuchten_matric_potential(
        self,
        water_content_pct: float,
        clay_pct: float,
        silt_pct: float,
        organic_matter_pct: float,
        bulk_density_g_per_cm3: float,
        top_soil: float,
    ) -> VanGenuchtenMatricPotentialResult:
        """
        Calculate matric potential from water content (Mualem-Van Genuchten).

        Useful as a coherence oracle: it reveals which matric potential
        actually corresponds to a given water content for a given soil, so
        a caller can detect physically contradictory inputs before feeding
        them to the precompression endpoint. Skipping that check on
        2026-08-26 produced artifact outputs from contradictory inputs.

        Endpoint: ``/calculations/calculate_mualem_van_genuchten_for_matric_potential``
        Request schema: ``MualemVanGenuchtenForMatricPotentialCalculationRequest``

        Parameters
        ----------
        water_content_pct
            Water content ``[%]`` (field ``waterContent``).
        clay_pct
            Clay content ``[%]`` (field ``clay``).
        silt_pct
            Silt content ``[%]`` (field ``silt``; the spec's description
            misspells it "Slit").
        organic_matter_pct
            Organic matter content ``[%]`` (field ``organicMatter``).
        bulk_density_g_per_cm3
            Bulk density ``[g/cm3]``.
        top_soil
            Topsoil flag. **This endpoint types it ``number``/``double``**,
            unlike the water-content variant which types it ``boolean``.
            A known spec inconsistency; pass a number here.

        Returns
        -------
        VanGenuchtenMatricPotentialResult
            The unit of the returned matric potential is unresolved: the
            spec gives the response no unit, and it is not established that
            Stefan's 2026-09-15 confirmation of bar (for inputs) covers it.
            Read as bar, values measured on 2026-09-10 (81-1902 for 25 %
            water content, depending on ``topSoil``) would be implausible.
            The value is stored as-is; the result field is unsuffixed.

        Raises
        ------
        TerranimoValidationError
            The API rejected the payload (HTTP 400).
        TerranimoAuthError
            Authentication failed (HTTP 401/403).
        TerranimoServerError
            Terranimo-side failure (HTTP 500+).
        TerranimoTimeoutError
            No response within the timeout.
        TerranimoError
            Any other failure, including a response missing ``result``.

        Notes
        -----
        This request uses short field names (``clay``, ``silt``,
        ``organicMatter``, ``waterContent``) where every other calculation
        schema uses ``*Percentage`` names. That asymmetry is in the spec, not
        a transcription slip.
        """
        payload = {
            "waterContent": water_content_pct,
            "clay": clay_pct,
            "silt": silt_pct,
            "organicMatter": organic_matter_pct,
            "bulkDensity": bulk_density_g_per_cm3,
            "topSoil": top_soil,
        }
        response_json = self._post(ENDPOINT_VG_MATRIC_POTENTIAL, payload)
        return VanGenuchtenMatricPotentialResult(
            matric_potential=self._require_field(
                response_json, "result", ENDPOINT_VG_MATRIC_POTENTIAL
            ),
            raw_response=response_json,
        )

    def precompression(
        self,
        water_content_pct: float,
        matric_potential_bar: float,
        clay_pct: float,
        silt_pct: float,
        organic_matter_pct: float,
        bulk_density_g_per_cm3: float,
        top_soil: bool,
    ) -> PrecompressionResult:
        """
        Calculate soil precompression — endpoint 1 of the compaction chain.

        Endpoint: ``/calculations/calculate_precompression_of_soil``
        Request schema: ``SoilPrecompressionRequest``

        Parameters
        ----------
        water_content_pct
            Water content ``[%]`` (field ``waterContentPercentage``).
        matric_potential_bar
            Matric potential in bar, confirmed by Stefan Gfeller (BFH) on
            2026-09-15; matches the spec. Sent verbatim, unconverted.
        clay_pct
            Clay content ``[%]``.
        silt_pct
            Silt content ``[%]``.
        organic_matter_pct
            Organic matter content ``[%]``.
        bulk_density_g_per_cm3
            Bulk density ``[g/cm3]``. **This is what actually discriminates
            topsoil from subsoil** — see ``top_soil`` below.
        top_soil
            Topsoil flag (``boolean`` per the spec). Testing on 2026-08-26
            showed this flag has **no effect on the result**: identical
            inputs with ``True`` and ``False`` returned identical values
            across three pairs. Vary ``bulk_density_g_per_cm3`` instead to
            model a different layer.

        Returns
        -------
        PrecompressionResult

        Raises
        ------
        TerranimoValidationError
            The API rejected the payload (HTTP 400).
        TerranimoAuthError
            Authentication failed (HTTP 401/403).
        TerranimoServerError
            Terranimo-side failure (HTTP 500+).
        TerranimoTimeoutError
            No response within the timeout.
        TerranimoError
            Any other failure, including a response missing
            ``preCompressionOfSoil``.

        Notes
        -----
        The chain needs this called **twice** — once with the topsoil bulk
        density and once with the subsoil's — to obtain the two values that
        :meth:`tyre_for_compaction` takes as ``precompression_top_layer_bar``
        and ``precompression_bar``.
        """
        payload = {
            "waterContentPercentage": water_content_pct,
            "matricPotential": matric_potential_bar,
            "clayPercentage": clay_pct,
            "siltPercentage": silt_pct,
            "organicMatterPercentage": organic_matter_pct,
            "bulkDensity": bulk_density_g_per_cm3,
            "topSoil": top_soil,
        }
        response_json = self._post(ENDPOINT_PRECOMPRESSION, payload)
        return PrecompressionResult(
            precompression_bar=self._require_field(
                response_json, "preCompressionOfSoil", ENDPOINT_PRECOMPRESSION
            ),
            raw_response=response_json,
        )

    def tyre_for_compaction(
        self,
        tyre_uid: str,
        tyre_load_kg: int,
        tyre_pressure_bar: float,
        tyre_pressure_recommended_bar: float,
        recent_tillage: bool,
        precompression_top_layer_bar: float,
        precompression_bar: float,
        matric_potential_bar: float,
    ) -> TyreCompactionResult:
        """
        Calculate the compaction-risk decision for a tyre — endpoint 2.

        Endpoint: ``/calculations/calculate_tyre_for_compaction_risc_decision``
        Request schema: ``CalculateWheelForCompactionRiscDecisionRequest``

        This is the wheeled-machine variant. A separate endpoint,
        ``calculate_track_for_compaction_risc_decision``, handles tracked
        machines and is not wrapped by this client.

        Parameters
        ----------
        tyre_uid
            Terranimo tyre UID from the tyre catalog (field ``tyreUID``).
            The catalog supplies the tyre's width, diameter and static loaded
            radius internally, so the caller does not provide that geometry.
        tyre_load_kg
            Wheel load ``[kg]`` (field ``tyreLoad``, typed ``integer``).
        tyre_pressure_bar
            Actual inflation pressure ``[bar]`` (field ``tyrePressure``).
        tyre_pressure_recommended_bar
            Recommended inflation pressure ``[bar]`` (field
            ``tyrePressureRecommended``). Both pressures travel together
            because the model's central variable is their ratio.
        recent_tillage
            Whether the field was recently tilled (field ``recentTillage``).
        precompression_top_layer_bar
            Precompression of layer 1, from :meth:`precompression` run with
            the topsoil bulk density (field ``preCompressionOfSoilTopLayer``).
        precompression_bar
            Precompression of layer 4, from :meth:`precompression` run with
            the subsoil bulk density (field ``preCompressionOfSoil``).
        matric_potential_bar
            Matric potential of layer 4, in bar (Stefan Gfeller, 2026-09-15;
            matches the spec). Sent verbatim, unconverted.

        Returns
        -------
        TyreCompactionResult
            Carries ``verdict`` (``"good"``/``"ok"``/``"bad"``) plus the
            absolute stress and strength.

        Raises
        ------
        TerranimoValidationError
            The API rejected the payload (HTTP 400).
        TerranimoAuthError
            Authentication failed (HTTP 401/403).
        TerranimoServerError
            Terranimo-side failure (HTTP 500+).
        TerranimoTimeoutError
            No response within the timeout.
        TerranimoError
            Any other failure, including a response missing a field.

        Notes
        -----
        **Consume the verdict, not the absolute values.** The stress/strength
        comparison is internally consistent whichever pressure unit the API
        means, so the categorical result stands while the absolute numbers
        await unit confirmation. Do not surface stress or strength to
        producers.
        """
        payload = {
            "tyreUID": tyre_uid,
            "tyreLoad": tyre_load_kg,
            "tyrePressure": tyre_pressure_bar,
            "tyrePressureRecommended": tyre_pressure_recommended_bar,
            "recentTillage": recent_tillage,
            "preCompressionOfSoilTopLayer": precompression_top_layer_bar,
            "preCompressionOfSoil": precompression_bar,
            "matricPotential": matric_potential_bar,
        }
        response_json = self._post(ENDPOINT_TYRE_COMPACTION, payload)
        return TyreCompactionResult(
            soil_stress_bar=self._require_field(
                response_json, "soilStress", ENDPOINT_TYRE_COMPACTION
            ),
            soil_strength_bar=self._require_field(
                response_json, "soilStrength", ENDPOINT_TYRE_COMPACTION
            ),
            verdict=self._require_field(
                response_json, "result", ENDPOINT_TYRE_COMPACTION
            ),
            raw_response=response_json,
        )

    @staticmethod
    def _require_field(
        response_json: Dict[str, Any], key: str, endpoint: str
    ) -> Any:
        """
        Return ``response_json[key]``, or raise a Terranimo error.

        The spec marks **no** response property as required, so a field can
        legitimately be absent. Failing here with the endpoint and the keys
        actually received beats a bare ``KeyError`` from deep inside a
        pipeline.

        Raises
        ------
        TerranimoError
            If ``key`` is missing from the response.
        """
        if key not in response_json:
            raise TerranimoError(
                f"Response from {endpoint} has no {key!r} field "
                f"(received keys: {sorted(response_json)})"
            )
        return response_json[key]
