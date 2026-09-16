"""
client.py — Open-Meteo client, MSFourrager

Transport layer for the Open-Meteo forecast API.

Every behaviour encoded here was verified against the live API on
2026-09-11 before being written; nothing is inferred from documentation.
See README.md, "Verified behaviour".

Design mirrors ``terranimo_client``: pass-through units, typed dataclasses,
raw JSON preserved, a clean exception hierarchy, and no retries.

Reference: https://open-meteo.com/en/docs
"""

import logging
from typing import Any, Dict, Iterable, Optional

import requests

from .config import (
    BASE_URL,
    DEFAULT_CURRENT_VARIABLES,
    DEFAULT_FORECAST_HOURS,
    DEFAULT_HOURLY_VARIABLES,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_TIMEZONE,
    MAX_FORECAST_HOURS,
    PING_LATITUDE,
    PING_LONGITUDE,
    WIND_SPEED_UNIT,
)
from .exceptions import (
    WeatherError,
    WeatherHTTPError,
    WeatherTimeoutError,
    WeatherValidationError,
)
from .models import CurrentResult, ForecastResult

logger = logging.getLogger(__name__)


class OpenMeteoClient:
    """
    Thin, synchronous client for the Open-Meteo forecast API.

    No authentication is required on the free tier, so the client holds no
    credentials. It performs no retries: one call in, one call out.

    Examples
    --------
    >>> client = OpenMeteoClient()
    >>> client.ping()
    True
    >>> fc = client.get_forecast(45.4059, -73.9430, hours=24)
    >>> max(fc.window("precipitation_probability", 24))
    0.0
    >>> fc.units["relative_humidity_2m"]
    '%'
    """

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        base_url: str = BASE_URL,
    ) -> None:
        """
        Initialize the client.

        Parameters
        ----------
        timeout
            Per-request timeout in seconds.
        base_url
            API endpoint. Overridable for testing against a stub.

        Raises
        ------
        ValueError
            If ``timeout`` is not positive.
        """
        if timeout <= 0:
            raise ValueError(f"timeout must be positive, got {timeout}")
        self.base_url: str = base_url
        self.timeout: int = timeout

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(base_url={self.base_url!r}, "
            f"timeout={self.timeout})"
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    @staticmethod
    def _validate_coordinates(latitude: float, longitude: float) -> None:
        """
        Reject coordinates the API would reject, without a round trip.

        Raises
        ------
        WeatherValidationError
            If latitude is outside [-90, 90] or longitude outside
            [-180, 180].
        """
        if not -90.0 <= latitude <= 90.0:
            raise WeatherValidationError(
                f"latitude must be in [-90, 90], got {latitude}"
            )
        if not -180.0 <= longitude <= 180.0:
            raise WeatherValidationError(
                f"longitude must be in [-180, 180], got {longitude}"
            )

    def _get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Issue one GET and map failures onto Weather exceptions.

        Parameters
        ----------
        params
            Query parameters, sent as-is.

        Returns
        -------
        Dict[str, Any]
            Decoded response body.

        Raises
        ------
        WeatherTimeoutError
            The request exceeded ``self.timeout``.
        WeatherHTTPError
            The API answered non-2xx. Open-Meteo uses HTTP 400 for every
            caller-side problem; the ``reason`` field carries the detail.
        WeatherError
            Transport failure that is not a timeout, or an unparseable body.
        """
        logger.info("GET %s params=%s", self.base_url, sorted(params))
        try:
            response = requests.get(
                self.base_url, params=params, timeout=self.timeout
            )
        except requests.Timeout as exc:
            raise WeatherTimeoutError(
                f"GET {self.base_url} timed out after {self.timeout}s"
            ) from exc
        except requests.RequestException as exc:
            raise WeatherError(f"GET {self.base_url} failed: {exc}") from exc

        logger.info(
            "GET %s -> HTTP %d (%d bytes)",
            self.base_url,
            response.status_code,
            len(response.content),
        )

        try:
            body = response.json()
        except ValueError as exc:
            if response.ok:
                raise WeatherError(
                    f"Response from {response.url} is not valid JSON: {exc}",
                    status_code=response.status_code,
                    response_text=response.text,
                ) from exc
            body = None

        if not response.ok:
            reason = body.get("reason") if isinstance(body, dict) else None
            raise WeatherHTTPError(
                f"GET {self.base_url} returned HTTP {response.status_code}",
                status_code=response.status_code,
                response_text=response.text or None,
                reason=reason,
            )

        # A 200 can still carry an error flag; guard rather than assume.
        if isinstance(body, dict) and body.get("error"):
            raise WeatherHTTPError(
                f"GET {self.base_url} returned an error payload",
                status_code=response.status_code,
                response_text=response.text,
                reason=body.get("reason"),
            )
        if not isinstance(body, dict):
            raise WeatherError(
                f"Expected a JSON object from {response.url}, "
                f"got {type(body).__name__}",
                status_code=response.status_code,
            )
        return body

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def ping(self) -> bool:
        """
        Check that the API is reachable and answering.

        Issues a minimal request with no variables requested, which the API
        answers with metadata only (confirmed live 2026-09-11). There is no
        dedicated health endpoint and no authentication to verify.

        Returns
        -------
        bool
            ``True`` when the API answered 2xx with a JSON object.

        Raises
        ------
        WeatherTimeoutError
            No answer within the timeout.
        WeatherError
            Any other failure.

        Notes
        -----
        Failures raise rather than returning ``False``, so "the service is
        down" stays distinguishable from "the service said no".
        """
        self._get({"latitude": PING_LATITUDE, "longitude": PING_LONGITUDE})
        logger.info("Ping OK")
        return True

    def get_forecast(
        self,
        latitude: float,
        longitude: float,
        hours: int = DEFAULT_FORECAST_HOURS,
        variables: Optional[Iterable[str]] = None,
    ) -> ForecastResult:
        """
        Fetch the hourly forecast for one point.

        Parameters
        ----------
        latitude, longitude
            Decimal degrees. Validated client-side before the request.
        hours
            Forecast window. Sent as the API's ``forecast_hours``.
        variables
            Hourly variable names. Defaults to
            :data:`~weather_client.config.DEFAULT_HOURLY_VARIABLES`.

        Returns
        -------
        ForecastResult
            Timestamps, one series per variable, and the API's own units.

        Raises
        ------
        WeatherValidationError
            Bad coordinates, a non-positive or oversized window, an empty
            variable list, or a response whose series are index-misaligned.
        WeatherHTTPError
            The API rejected the request (HTTP 400 with a ``reason``).
        WeatherTimeoutError
            No answer within the timeout.

        Notes
        -----
        The returned ``latitude``/``longitude`` are the API's grid-snapped
        coordinates, not the ones requested.

        ``wind_speed_unit=ms`` is always sent, so ``wind_speed_10m`` comes
        back in m/s rather than the API default of km/h. See
        :data:`~weather_client.config.WIND_SPEED_UNIT`.
        """
        self._validate_coordinates(latitude, longitude)
        if hours <= 0:
            raise WeatherValidationError(f"hours must be positive, got {hours}")
        if hours > MAX_FORECAST_HOURS:
            raise WeatherValidationError(
                f"hours must be <= {MAX_FORECAST_HOURS}, got {hours}"
            )

        names = list(variables) if variables is not None else list(DEFAULT_HOURLY_VARIABLES)
        if not names:
            raise WeatherValidationError("variables must not be empty")

        body = self._get(
            {
                "latitude": latitude,
                "longitude": longitude,
                "hourly": ",".join(names),
                "forecast_hours": hours,
                "timezone": DEFAULT_TIMEZONE,
                "wind_speed_unit": WIND_SPEED_UNIT,
            }
        )

        hourly = body.get("hourly")
        if not isinstance(hourly, dict) or "time" not in hourly:
            raise WeatherValidationError(
                f"Response has no usable 'hourly' block "
                f"(keys: {sorted(body)})"
            )
        units = body.get("hourly_units") or {}

        return ForecastResult(
            latitude=body["latitude"],
            longitude=body["longitude"],
            timezone=body.get("timezone", ""),
            utc_offset_seconds=body.get("utc_offset_seconds", 0),
            elevation=body.get("elevation", float("nan")),
            times=list(hourly["time"]),
            values={k: list(v) for k, v in hourly.items() if k != "time"},
            units={k: v for k, v in units.items() if k != "time"},
            raw_response=body,
        )

    def get_current(
        self,
        latitude: float,
        longitude: float,
        variables: Optional[Iterable[str]] = None,
    ) -> CurrentResult:
        """
        Fetch current conditions for one point.

        Parameters
        ----------
        latitude, longitude
            Decimal degrees. Validated client-side before the request.
        variables
            Current variable names. Defaults to
            :data:`~weather_client.config.DEFAULT_CURRENT_VARIABLES`.

        Returns
        -------
        CurrentResult
            Scalar values plus the API's own units.

        Raises
        ------
        WeatherValidationError
            Bad coordinates, an empty variable list, or a response with no
            usable ``current`` block.
        WeatherHTTPError
            The API rejected the request.
        WeatherTimeoutError
            No answer within the timeout.
        """
        self._validate_coordinates(latitude, longitude)
        names = list(variables) if variables is not None else list(DEFAULT_CURRENT_VARIABLES)
        if not names:
            raise WeatherValidationError("variables must not be empty")

        body = self._get(
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": ",".join(names),
                "timezone": DEFAULT_TIMEZONE,
                "wind_speed_unit": WIND_SPEED_UNIT,
            }
        )

        current = body.get("current")
        if not isinstance(current, dict) or "time" not in current:
            raise WeatherValidationError(
                f"Response has no usable 'current' block (keys: {sorted(body)})"
            )
        units = body.get("current_units") or {}
        skip = ("time", "interval")

        return CurrentResult(
            latitude=body["latitude"],
            longitude=body["longitude"],
            timezone=body.get("timezone", ""),
            time=current["time"],
            interval_seconds=current.get("interval", 0),
            values={k: v for k, v in current.items() if k not in skip},
            units={k: v for k, v in units.items() if k not in skip},
            raw_response=body,
        )
