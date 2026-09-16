"""
models.py — Open-Meteo client, MSFourrager

Typed return values for the forecast endpoint.

Values are stored exactly as the API returned them. This module performs
**no unit conversion**, matching the pass-through design of
``terranimo_client``. Units travel alongside the values in ``units``, taken
from the API's own ``hourly_units`` / ``current_units`` block, so a caller
never has to assume one.

Confirmed live on 2026-09-11:
    precipitation_probability  [%]
    relative_humidity_2m       [%]
    temperature_2m             [°C]
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .exceptions import WeatherValidationError


@dataclass
class ForecastResult:
    """
    Hourly forecast for one point.

    Attributes
    ----------
    latitude, longitude
        Coordinates **the API actually served**, which are snapped to its
        model grid and therefore differ from what was requested — a request
        for 45.4059, -73.9430 came back as 45.398304, -73.95152. Keep both
        in mind when reporting provenance.
    timezone
        IANA timezone resolved by the API (``timezone=auto``).
    utc_offset_seconds
        Offset applied to the timestamps in :attr:`times`.
    elevation
        Model grid-cell elevation in metres.
    times
        ISO8601 local timestamps, one per forecast hour.
    values
        Variable name to its hourly series. Each list is the same length as
        :attr:`times` and index-aligned with it. Entries may be ``None``
        where the model has no value.
    units
        Variable name to the unit string the API declared for it.
    raw_response
        Full decoded response body.

    Raises
    ------
    WeatherValidationError
        If any series length does not match ``times``. An index-misaligned
        series would silently pair a value with the wrong hour.
    """

    latitude: float
    longitude: float
    timezone: str
    utc_offset_seconds: int
    elevation: float
    times: List[str]
    values: Dict[str, List[Optional[float]]]
    units: Dict[str, str]
    raw_response: Dict[str, Any] = field(repr=False)

    def __post_init__(self) -> None:
        n = len(self.times)
        for name, series in self.values.items():
            if len(series) != n:
                raise WeatherValidationError(
                    f"Series '{name}' has {len(series)} entries but there are "
                    f"{n} timestamps; the forecast is index-misaligned"
                )

    def series(self, variable: str) -> List[Optional[float]]:
        """
        Return the hourly series for ``variable``.

        Raises
        ------
        WeatherValidationError
            If the variable is absent — which happens when it was never
            requested, or when the API served the point but had no data for
            it.
        """
        if variable not in self.values:
            raise WeatherValidationError(
                f"Variable {variable!r} not in forecast "
                f"(available: {sorted(self.values)})"
            )
        return self.values[variable]

    def window(self, variable: str, hours: int) -> List[float]:
        """
        Return the first ``hours`` non-``None`` values of ``variable``.

        ``None`` entries are dropped rather than substituted, so an
        aggregate over the result reflects only hours the model actually
        produced.

        Raises
        ------
        WeatherValidationError
            If ``hours`` is not positive, or the window contains no usable
            value.
        """
        if hours <= 0:
            raise WeatherValidationError(f"hours must be positive, got {hours}")
        values = [v for v in self.series(variable)[:hours] if v is not None]
        if not values:
            raise WeatherValidationError(
                f"No non-null values for {variable!r} in the first {hours} hours"
            )
        return values


@dataclass
class CurrentResult:
    """
    Current conditions for one point.

    Attributes
    ----------
    latitude, longitude
        Coordinates served by the API (grid-snapped, see
        :class:`ForecastResult`).
    timezone
        IANA timezone resolved by the API.
    time
        ISO8601 local timestamp of the observation.
    interval_seconds
        Update interval the API reports for the current block (900 s
        observed on 2026-09-11).
    values
        Variable name to scalar value.
    units
        Variable name to the unit string the API declared for it.
    raw_response
        Full decoded response body.
    """

    latitude: float
    longitude: float
    timezone: str
    time: str
    interval_seconds: int
    values: Dict[str, Optional[float]]
    units: Dict[str, str]
    raw_response: Dict[str, Any] = field(repr=False)

    def value(self, variable: str) -> Optional[float]:
        """
        Return the current value of ``variable``.

        Raises
        ------
        WeatherValidationError
            If the variable is absent from the response.
        """
        if variable not in self.values:
            raise WeatherValidationError(
                f"Variable {variable!r} not in current conditions "
                f"(available: {sorted(self.values)})"
            )
        return self.values[variable]
