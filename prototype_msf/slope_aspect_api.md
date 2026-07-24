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

## Response

Both products return the same envelope. Fields beyond the documented
mean values, observed 2026-07-25:

    stac_items    array of STAC item ids
    assets        STAC asset dict per product - href, type, roles, title,
                  and raster:bands with data_type, nodata and description
    bbox          WGS84 envelope, matches the input polygon exactly
    products      echo of the request
    <product>     the summary values

### slope

    "slope": {
      "mean_degrees": 1.298465371131897,
      "mean_percent": 2.2963144779205322
    }

### aspect

    "aspect": {
      "mean_degrees": 80.18198580557298
    }

Downslope compass bearing: 0 = North, increasing clockwise.

    337.5-22.5   N       157.5-202.5  S
    22.5-67.5    NE      202.5-247.5  SW
    67.5-112.5   E       247.5-292.5  W
    112.5-157.5  SE      292.5-337.5  NW

### STAC ids are derived from the input geometry

Confirmed 2026-07-25 by calling with a second field:

| Field | STAC id | mean_degrees |
|---|---|---|
| 36-1 | `lidar_slope_geom_e6df18cd` | 1.298465 |
| 32-1 | `lidar_slope_geom_6f481eb4` | 1.248993 |

Different polygon, different 8-character suffix. The suffix is a
deterministic function of the input geometry, so it is usable as a cache key
on the client side: one call per field per polygon version, reusable until
the boundary changes.

## Latency

The documentation Jeremie provided says the first call per field takes a few
seconds for slope and a few minutes for aspect, with subsequent calls served
from cache.

Measured, MSF fields in Saint-Zotique, 2026-07-25:

| Call | Elapsed | Note |
|---|---|---|
| 36-1 slope, first call | 7.08 s | cold |
| 36-1 aspect, first call | 6.27 s | after the slope call on the same geometry |
| 32-1 slope, first call | 8.39 s | cold, different geometry |
| 36-1 slope, re-sent as MultiPolygon | 1.37 s | served from cache |

Aspect was far faster than documented. Two possible reasons, neither
confirmed: the DTM tile may already have been cached server-side, or the
geometry was indexed by the preceding slope call and aspect reused it.
Worth raising with Jeremie.

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

## Tested

Called successfully on 2026-07-25 with a real MSF field polygon.

Field: 36-1, id 1e1d77fe-1c14-4533-8062-8d726b6d7361, 18.87 ha,
Saint-Zotique, Quebec.

    slope   1.30 degrees / 2.30 percent
    aspect  80.18 degrees (East)

The slope is consistent with the terrain: Saint-Zotique sits on the flat
clay plain of the St Lawrence lowlands. On a field this flat, aspect carries
little physical meaning for snowmelt or radiation, though the value is
coherent.

Second field, 32-1 (12.47 ha, adjacent to 36-1): slope 1.25 degrees.

Raw responses kept in C:\Proyectos: jeremie_slope_36-1.json,
jeremie_aspect_36-1.json, jeremie_slope_32-1.json,
jeremie_slope_36-1_multipolygon.json

### Geometry format - MultiPolygon works directly

MSF stores field boundaries as MultiPolygon in EPSG:4326. The API example
shows Polygon, but both are accepted.

Field 36-1 sent both ways, 2026-07-25:

| Sent as | STAC id | mean_degrees | Elapsed |
|---|---|---|---|
| Polygon (unwrapped) | `lidar_slope_geom_e6df18cd` | 1.298465371131897 | 7.08 s |
| MultiPolygon (as stored) | `lidar_slope_geom_e6df18cd` | 1.298465371131897 | 1.37 s |

Identical STAC id and identical value. The API canonicalises the geometry
before hashing, so the two formats collapse to the same cache entry - this
is not a hash of the raw JSON string.

Practical consequence: MSF polygons can be sent as-is, with no unwrapping
step in the client.

A field with genuinely multiple disjoint rings was not tested; both fields
used here have a single ring.

## Status

NOT INTEGRATED. The interface is verified to work, but nothing in the
prototype calls it and no value from it feeds any calculation.
