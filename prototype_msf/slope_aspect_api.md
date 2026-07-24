# Slope and aspect API - McGill (Jeremie Durand)

Provided by Jeremie Durand, McGill, 2026-07-24. Development server; report
bugs to him.

Source data: MRNF Quebec LiDAR. Slope is a native product of that dataset at
2 m resolution. Aspect is NOT native - computed on the fly from the DTM via
`gdaldem aspect` at 1 m resolution (proof of concept).

## Endpoint

POST https://agri-sdss.duckdns.org/process-api/processes/lidar-fetch/execution?f=json

Docs: https://agri-sdss.duckdns.org/process-api/processes/lidar-fetch

## Request

Content-Type: application/json

    {
      "inputs": {
        "farm_geometry": { "type": "Polygon", "coordinates": [[[lon, lat], ...]] },
        "products": ["slope"]
      }
    }

`farm_geometry` is standard GeoJSON, WGS84 lon/lat.
`products` accepts ["slope"], ["aspect"], or both. Both is slower.

## Response - slope

    "slope": {
      "mean_degrees": 5.914061069488525,
      "mean_percent": 10.666373252868652
    }

Also returns a COG GeoTIFF href, a STAC item id, the bbox, and band metadata
with nodata = -9999.

## Response - aspect

    "aspect": {
      "mean_degrees": 341.83677558017496
    }

Downslope compass bearing: 0 = North, increasing clockwise.

Direction bands, per the reference table Jeremie provided:

    337.5-22.5   N       157.5-202.5  S
    22.5-67.5    NE      202.5-247.5  SW
    67.5-112.5   E       247.5-292.5  W
    112.5-157.5  SE      292.5-337.5  NW

## Latency

| Product | First call per field | Subsequent |
|---|---|---|
| slope | a few seconds | cached, near-instant |
| aspect | a few minutes | cached, near-instant |

Aspect is slow because it fetches elevation data before running gdaldem.
Cached server-side per geometry.

## Why both matter

RUFAS models neither:

- **Slope.** Used in soil_erosion.py (MUSLE) for sediment yield, but the
  dissolved-N runoff coefficient in leaching_runoff_erosion.py is flat
  regardless of slope.
- **Aspect.** snow.py has no aspect term at all. South-facing fields lose
  snow before north-facing ones, which shifts the spring application window.

## Input source

Field polygons live in farms_farmfieldyearly.polygon in MSF (PostGIS). They
need converting to GeoJSON before the call - ST_AsGeoJSON() on the Supabase
side, or an equivalent client-side conversion.

## Caching

Aspect does not change over time; slope changes only if the field boundary
changes. One call per field is enough and results should be stored rather
than re-requested.

## Status

NOT INTEGRATED. This file records the interface only. Nothing in the
prototype calls this API, and no value from it has been used in any
calculation.
