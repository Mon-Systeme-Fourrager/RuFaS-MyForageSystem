# weather_client

**Version 0.1.0**

Python client for the [Open-Meteo](https://open-meteo.com/en/docs) forecast API, built for the MSFourrager Weather factor.

## Overview

Open-Meteo serves hourly weather forecasts worldwide with no API key and no registration. This client wraps the variables the Spatializer's `WeatherEvaluator` needs — air temperature, wind speed, precipitation, precipitation probability and relative humidity, the set required by the thresholds of Brassard et al. 2026 (IRDA-MAPAQ) — as a thin transport layer: it validates coordinates, maps failures onto typed exceptions, and returns decoded responses unchanged. It performs **no unit conversion**; every result carries the API's own unit strings beside the values, so a caller never has to assume one. Design mirrors `terranimo_client`.

## Installation

Python 3.9 or newer.

```bash
pip install requests
```

Already present in the `anaconda3` base environment (requests 2.32.5). Import from the repo root, `C:\Proyectos\terranimo-test\`:

```python
from weather_client import OpenMeteoClient
```

## Configuration

None. No API key, no `.env`, no registration.

## Usage

```python
import logging
from weather_client import OpenMeteoClient, WeatherError

logging.basicConfig(level=logging.INFO)
client = OpenMeteoClient()

client.ping()                                   # True, or raises

fc = client.get_forecast(45.4059, -73.9430, hours=24)
print(fc.units)          # {'precipitation_probability': '%', 'relative_humidity_2m': '%', ...}
print(max(fc.window("precipitation_probability", 24)))
print(min(fc.window("temperature_2m", 24)))

cur = client.get_current(45.4059, -73.9430)
print(cur.value("temperature_2m"), cur.units["temperature_2m"])
```

`ForecastResult.window(variable, hours)` returns the first *N* non-`None` values of a series — the aggregation primitive the evaluator uses. `None` entries are dropped rather than substituted, so an aggregate reflects only hours the model actually produced.

### Exceptions

| Exception | Trigger |
| --- | --- |
| `WeatherError` | Base class; transport failures, unparseable bodies |
| `WeatherHTTPError` | Non-2xx response, or a 200 carrying `error: true` |
| `WeatherTimeoutError` | Request exceeded the timeout |
| `WeatherValidationError` | Client-side rejection, or a malformed/misaligned response |

Each carries `.status_code`, `.response_text` and `.reason`. The `reason` matters: Open-Meteo returns HTTP 400 for *every* caller-side problem, so the status alone never says what went wrong.

## Verified behaviour

Confirmed against the live API on **2026-09-11**. Nothing below is taken from documentation alone.

| Behaviour | Observed |
| --- | --- |
| Response shape | `hourly.time` array plus one same-length array per variable |
| Units | Declared in `hourly_units` / `current_units`, returned alongside values |
| `temperature_2m` | `°C` |
| `wind_speed_10m` | **`km/h` by default** — `m/s` only because the client sends `wind_speed_unit=ms` |
| `precipitation` | `mm` |
| `precipitation_probability` | `%` |
| `relative_humidity_2m` | `%` — integers, e.g. `60` |
| `soil_moisture_0_to_1cm` | `m³/m³` — volumetric, e.g. `0.296`, **not** a percentage |
| Errors | HTTP 400 with `{"error": true, "reason": "..."}` |
| Invalid latitude | `"Latitude must be in range of -90 to 90°. Given: 999.0."` |
| Unknown variable | HTTP 400, `reason` naming the rejected string |
| Request with no variables | HTTP 200, metadata only — used by `ping()` |
| Round-trip latency | ~0.44 s for a 3-hour, 3-variable request |

**Coordinates are grid-snapped.** A request for `45.4059, -73.9430` came back as `45.398304, -73.95152`. `ForecastResult.latitude/longitude` are what the API served, not what was asked for — use them when recording provenance.

## Known limitations

- **`soil_moisture_0_to_1cm` is volumetric water content (m³/m³), not saturation.** Converting it to a "% saturation" requires dividing by porosity, which the API does not provide. The variable was dropped from the defaults on 2026-09-11 for that reason *and* because soil state belongs to RUFAS, not to a weather provider. It remains requestable via the `variables=` argument.
- **`wind_speed_10m` defaults to km/h, not m/s.** Montreal returned 16.2 km/h = 4.50 m/s on 2026-09-11. The client always sends `wind_speed_unit=ms` so values arrive in m/s, the unit the `WeatherEvaluator` thresholds use. Without it a routine breeze reads 3.6x too fast and trips the 8 m/s stop. The API echoes the unit in `hourly_units` — verify it there.
- **No health endpoint.** `ping()` issues a minimal metadata-only forecast request instead.
- **No retries**, no rate-limit handling. The free tier publishes a fair-use limit that this client does not track.
- **Forecast uncertainty is not modelled.** The API returns point values with no confidence interval; accuracy degrades with horizon.
