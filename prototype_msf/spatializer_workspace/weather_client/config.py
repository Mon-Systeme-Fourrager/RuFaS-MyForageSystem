"""
config.py — Open-Meteo client, MSFourrager

Static configuration for the Open-Meteo forecast API.

Everything here was verified against the live API on 2026-09-11 (see
README.md "Verified behaviour"). Nothing is inferred from documentation
alone.

Reference: https://open-meteo.com/en/docs
"""

from typing import Final, Tuple

# --------------------------------------------------------------------------
# Service
# --------------------------------------------------------------------------

#: Forecast endpoint. No API key is required on the free tier.
BASE_URL: Final[str] = "https://api.open-meteo.com/v1/forecast"

#: Per-request timeout in seconds. Observed round-trip on 2026-09-11 was
#: ~0.44 s for a 3-hour, 3-variable request.
DEFAULT_TIMEOUT_SECONDS: Final[int] = 30

# --------------------------------------------------------------------------
# Variables
# --------------------------------------------------------------------------

#: Hourly variables requested when the caller does not specify any.
#: These are exactly the variables the WeatherEvaluator needs, whose
#: thresholds come from Brassard et al. 2026 (IRDA-MAPAQ).
#:
#: Units returned by the API (confirmed live 2026-09-11):
#:     temperature_2m             [°C]
#:     wind_speed_10m             [m/s]  -- ONLY because WIND_SPEED_UNIT is sent
#:     precipitation              [mm]
#:     precipitation_probability  [%]
#:     relative_humidity_2m       [%]    -- context only, not scored
#:
#: NOTE: ``soil_moisture_0_to_1cm`` was used here until 2026-09-11 and was
#: removed for two reasons. It is soil state, not weather — that input
#: belongs to RUFAS. And the API returns it in m³/m³ (observed 0.073-0.399),
#: not as a percentage of saturation, so percentage thresholds built on it
#: could never fire. It remains requestable via ``variables=``.
DEFAULT_HOURLY_VARIABLES: Final[Tuple[str, ...]] = (
    "temperature_2m",
    "wind_speed_10m",
    "precipitation",
    "precipitation_probability",
    "relative_humidity_2m",
)

#: Current-conditions variables requested when the caller does not specify.
DEFAULT_CURRENT_VARIABLES: Final[Tuple[str, ...]] = (
    "temperature_2m",
    "wind_speed_10m",
    "precipitation",
    "relative_humidity_2m",
)

#: Wind speed unit sent on every request.
#:
#: **This is load-bearing, not cosmetic.** Open-Meteo defaults ``wind_speed_10m``
#: to **km/h**: Montreal on 2026-09-11 returned 16.2 km/h, which is 4.50 m/s.
#: Every wind threshold in the WeatherEvaluator is expressed in m/s per
#: Brassard et al. 2026, so without this parameter a routine 16 km/h breeze
#: would read as 16 m/s and trip the 8 m/s categorical stop — a factor-3.6
#: error that silently condemns every location. The API echoes the unit back
#: in ``hourly_units``; verify it there rather than assuming.
WIND_SPEED_UNIT: Final[str] = "ms"

#: Default forecast window in hours.
DEFAULT_FORECAST_HOURS: Final[int] = 48

#: Upper bound accepted by the API's ``forecast_hours`` parameter.
#: The free tier serves up to 16 days of forecast.
MAX_FORECAST_HOURS: Final[int] = 384

# --------------------------------------------------------------------------
# Request defaults
# --------------------------------------------------------------------------

#: ``timezone=auto`` makes the API resolve the local timezone from the
#: coordinates and return local ISO8601 timestamps. Without it, times come
#: back in GMT, which would silently shift a "next 24 hours" window.
DEFAULT_TIMEZONE: Final[str] = "auto"

#: Coordinates used by ``ping()``. Null Island — chosen because it is a
#: valid, always-served point that costs the API nothing to compute.
PING_LATITUDE: Final[float] = 0.0
PING_LONGITUDE: Final[float] = 0.0
