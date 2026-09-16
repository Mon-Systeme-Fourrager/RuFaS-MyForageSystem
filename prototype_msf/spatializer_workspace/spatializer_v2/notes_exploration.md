# Spatializer v0.2 — LiDAR STAC API exploration

**Date:** 2026-09-03
**Env:** base anaconda, Python 3.13
**Status:** exploration only, no production code written
**Outcome:** STAC metadata fully accessible. **Raster download is BLOCKED** — see §5.

---

## 1. Endpoints — the documented URL is not the API

| URL | Result |
|---|---|
| `https://agri-sdss.duckdns.org/stac/` | HTTP 200 **text/html** — STAC Browser SPA, not JSON |
| `https://agri-sdss.duckdns.org/stac` (no slash) | redirects to port **8080** → ConnectTimeout |
| **`https://agri-sdss.duckdns.org/stac-api/`** | **HTTP 200 application/json — this is the API** |

The `/stac/` SPA returns HTTP 200 + HTML for *any* sub-path
(`/stac/collections`, `/stac/search`, `/stac/data/x.tif` all return the
same 1118-byte shell). Do not treat a 200 from `/stac/` as success.

**Base URL for the client: `https://agri-sdss.duckdns.org/stac-api`**

Implementation: `stac-fastapi`, STAC version 1.0.0.
Conformance includes OGC API Features core + CQL2 filtering.

**No authentication required** — all calls succeeded with no credentials,
as Jérémie stated. No 401/403 seen anywhere.

## 2. Listing items in lidar_quebec

    GET /stac-api/collections                                  -> 3 collections
    GET /stac-api/collections/lidar_quebec/items?limit=10       -> FeatureCollection

Collections present:

| id | title | bbox | license |
|---|---|---|---|
| `demo_collection` | demo_collection | Ontario/Quebec | na |
| **`lidar_quebec`** | Quebec LiDAR Derived Products | `[-79.75, 41.75, -56.0, 63.0]` | OGL-Canada-2.0 |
| `sentinel2_eo_products` | Sentinel-2 EO Products | | proprietary |

`lidar_quebec` temporal extent: `2015-01-01T00:00:00Z` → open (null).

**Item naming:** `lidar_{product}_geom_{hash8}` where products observed are
`dtm`, `slope`, `hillshade`, `chm`. The same `{hash8}` recurs across products
for one geometry (e.g. `4468ba43` has all four). This matches the
deterministic geometry-hash behaviour documented in
`prototype_msf/slope_aspect_api.md`.

Each item carries exactly **one** asset, keyed by product name.

**Pagination:** token-based via `links[rel=next]`.
`numberMatched` / `numberReturned` are **null** — the API does not report a
total count, so the collection cannot be sized without walking every page.

## 3. Fetching a specific item

    GET /stac-api/collections/lidar_quebec/items/lidar_slope_geom_a2e4c82b

HTTP 200. Verbatim response detail:

    bbox:          [-71.83, 45.22, -71.78, 45.27]
    geometry:      Polygon
    proj:epsg:     4326
    platform:      lidar-mrnf
    instruments:   ['lidar']
    lidar:source:  MRNF Quebec open data
    lidar:product: slope
    created:       2026-08-04T21:44:09.932660Z

    assets.slope:
      type:  image/tiff; application=geotiff; profile=cloud-optimized
      href:  /data/lidar_slope_geom_a2e4c82b.tif
      roles: ['data']
      title: Slope (degrees and percent)
      raster:bands: [{'nodata': -9999,
                      'data_type': 'float32',
                      'description': 'Terrain slope in degrees computed from DTM (2 m resolution)'}]

Metadata needed for clustering is therefore available **without** downloading
the raster: nodata sentinel (`-9999`), dtype (`float32`), source resolution
(2 m), and bbox.

## 4. Dependency check (base anaconda)

| Package | Status |
|---|---|
| requests | 2.32.5 |
| numpy | 2.3.5 |
| scikit-learn | 1.7.2 |
| **rasterio** | **MISSING** |
| **pyproj** | **MISSING** |
| pystac_client | MISSING (optional — plain `requests` is sufficient) |
| shapely | MISSING (optional) |

`rasterio` and `pyproj` must be installed before any COG reading.
Note `sklearn` is absent from the `rufas` conda env — v0.2 must run on
**base anaconda**, not the RUFAS env.

## 5. BLOCKER — asset hrefs are not resolvable over HTTP

**Step 3.4 (download COG, pixel stats) could not be completed.**

Asset hrefs in `lidar_quebec` are **relative paths with no host**:

    href = /data/lidar_slope_geom_a2e4c82b.tif

Every candidate base was probed:

| URL | HTTP |
|---|---|
| `https://agri-sdss.duckdns.org/data/lidar_slope_geom_a2e4c82b.tif` | **404** |
| `https://agri-sdss.duckdns.org/stac-api/data/...` | **404** |
| `https://agri-sdss.duckdns.org/process-api/data/...` | **404** |
| `https://agri-sdss.duckdns.org/lidar_slope_geom_a2e4c82b.tif` | **404** |
| `https://agri-sdss.duckdns.org/stac/data/...` | 200 — but this is the SPA HTML shell, not the file |

Not an auth problem: plain 404, never 401/403.

**Corroborating evidence that this is server-side, not client-side:**

1. The pattern is consistent across all `lidar_quebec` items tested —
   `lidar_slope_geom_4468ba43`, `lidar_dtm_geom_095dc21f`,
   `lidar_chm_geom_4468ba43` all use `/data/{id}.tif`.
2. `demo_collection` assets use `file:///data/output/raster_cog/*.tif` —
   a **local filesystem URI on the server**, unreachable over HTTP by
   definition. The catalogue was generated with server-local paths.
3. The OpenAPI spec (`/stac-api/api`) declares **12 routes, none of which
   serve assets**:
   `/`, `/conformance`, `/collections`, `/collections/{cid}`,
   `/collections/{cid}/items`, `/collections/{cid}/items/{iid}`,
   `/collections/{cid}/bulk_items`, `/collections/{cid}/queryables`,
   `/queryables`, `/search`, `/_mgmt/ping`, `/_mgmt/health`.

**Conclusion:** the STAC catalogue indexes rasters that are not exposed
through any HTTP route. This must be resolved by Jérémie — no client-side
workaround exists.

### Questions for Jérémie

1. Is there an HTTP route that serves `/data/*.tif`, or is that path
   server-local only?
2. If assets are meant to be public, should `href` be rewritten to an
   absolute URL (e.g. `https://agri-sdss.duckdns.org/<route>/...`)?
3. `demo_collection` uses `file:///` hrefs — is that intentional
   (internal-only collection) or the same defect?
4. Is COG range-request access (`Accept-Ranges: bytes`) supported once the
   route exists? Windowed reads would avoid downloading full tiles.

## 6. Open technical question — CRS

`proj:epsg` is **4326** (geographic, degrees), while the band description
says slope was *"computed from DTM (2 m resolution)"*.

Computing slope in a geographic CRS is a known pitfall — degree units are
not isotropic, so slope is distorted with latitude unless the computation
was done in a projected CRS and the *result* reprojected to 4326. The
metadata does not say which happened.

Worth confirming with Jérémie before slope values feed clustering.
**Not blocking** for pixel clustering itself, but it affects whether the
slope magnitudes are trustworthy.

## 7. Status

| Step | Status |
|---|---|
| 1. Folder structure | done |
| 2. Dependencies | done — `rasterio`, `pyproj` missing |
| 3.1 Base API URL | done — `/stac-api`, not `/stac` |
| 3.2 List items | done |
| 3.3 Fetch item + asset URL | done — href obtained, **not resolvable** |
| 3.4 Download COG + pixel stats | **BLOCKED** — see §5 |

**Cannot yet proceed to write `lidar_client.py`** against real data. The
metadata half of the client (search, item fetch, asset discovery) is fully
specified and could be written now; the fetch-and-read half has no working
endpoint to target.
