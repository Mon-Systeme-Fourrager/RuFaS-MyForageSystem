"""
weather_client — Python client for the Open-Meteo forecast API, MSFourrager

Wraps https://api.open-meteo.com/v1/forecast for the MSF Weather factor.
No API key is required.

Pass-through units: no conversion is performed anywhere. Each result carries
the API's own unit strings alongside the values.

Used by ``spatializer_v2.evaluators.weather.WeatherEvaluator``.
"""

from .client import OpenMeteoClient
from .config import (
    BASE_URL,
    DEFAULT_CURRENT_VARIABLES,
    DEFAULT_FORECAST_HOURS,
    DEFAULT_HOURLY_VARIABLES,
    DEFAULT_TIMEOUT_SECONDS,
    WIND_SPEED_UNIT,
)
from .exceptions import (
    WeatherError,
    WeatherHTTPError,
    WeatherTimeoutError,
    WeatherValidationError,
)
from .models import CurrentResult, ForecastResult

__version__ = "0.1.0"

__all__ = [
    # client
    "OpenMeteoClient",
    # exceptions
    "WeatherError",
    "WeatherHTTPError",
    "WeatherTimeoutError",
    "WeatherValidationError",
    # models
    "ForecastResult",
    "CurrentResult",
    # config
    "BASE_URL",
    "DEFAULT_HOURLY_VARIABLES",
    "DEFAULT_CURRENT_VARIABLES",
    "DEFAULT_FORECAST_HOURS",
    "DEFAULT_TIMEOUT_SECONDS",
    "WIND_SPEED_UNIT",
    "__version__",
]
