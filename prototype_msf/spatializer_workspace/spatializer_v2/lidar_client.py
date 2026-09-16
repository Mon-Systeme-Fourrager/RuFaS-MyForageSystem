"""
lidar_client.py — Spatializer v0.2, MSFourrager

Client for Jérémie Durand's LiDAR services (MRNF Quebec), in two layers:

* **STAC** (``/stac-api``) — discovery. Which items exist, their bbox, nodata,
  dtype, and the asset path.
* **raster-api** (``/raster-api``) — pixel access, served by TiTiler.
  Metadata, statistics and point sampling are computed server-side with GDAL.

No raster is ever downloaded and ``rasterio`` is never imported: all pixel
access is HTTP. See ``notes_raster_api.md`` for verified response samples.

Asset addressing
----------------
raster-api's ``url`` parameter is a **path on the server's filesystem**, not a
public URL. The value STAC publishes in ``assets[].href`` (``/data/{id}.tif``)
is exactly what raster-api expects, and can be passed through unchanged.
Passing a public https:// URL fails with HTTP 500 / "HTTP response code: 404".
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple

import requests

# ============================================================
# API constants (verified live 2026-09-03)
# notes_exploration.md section 1, notes_raster_api.md sections 1-7
# ============================================================

BASE_URL = "https://agri-sdss.duckdns.org/stac-api"
RASTER_API_URL = "https://agri-sdss.duckdns.org/raster-api"
LIDAR_COLLECTION = "lidar_quebec"

# The STAC browser UI at /stac/ returns HTTP 200 + HTML for ANY sub-path.
# Requesting JSON explicitly guards against parsing that shell as data.
_JSON_HEADERS = {"Accept": "application/json"}

DEFAULT_TIMEOUT_S = 30  # PLACEHOLDER — no SLA documented by the provider
STATISTICS_TIMEOUT_S = 90  # PLACEHOLDER — statistics is slower than info
DEFAULT_PAGE_LIMIT = 100  # PLACEHOLDER — no documented server maximum


class LidarClientError(RuntimeError):
    """Raised when a Lidar service returns an unusable response."""


def asset_path_for_item(item_id: str) -> str:
    """
    Build the server-side asset path raster-api expects for a STAC item id.

    Verified: raster-api ``url`` takes a server filesystem path, and STAC item
    ids map one-to-one onto ``/data/{id}.tif``.
    """
    if not item_id or not isinstance(item_id, str):
        raise ValueError(f"item_id must be a non-empty string, got: {item_id!r}")
    return f"/data/{item_id}.tif"


# ============================================================
# STAC layer — discovery
# ============================================================


def _get_json(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    GET a URL and return parsed JSON.

    Raises
    ------
    LidarClientError
        If the response is not HTTP 200, or is not JSON. A non-JSON 200 means
        the request hit the STAC Browser SPA rather than the API.
    """
    response = requests.get(url, headers=_JSON_HEADERS, params=params, timeout=DEFAULT_TIMEOUT_S)
    if response.status_code != 200:
        raise LidarClientError(f"HTTP {response.status_code} from {url}")
    content_type = response.headers.get("content-type", "")
    if "json" not in content_type:
        raise LidarClientError(
            f"Expected JSON from {url}, got '{content_type}'. "
            "This usually means the URL resolved to the STAC Browser SPA, not the API."
        )
    return response.json()


def query_stac_collection(
    collection_name: str = LIDAR_COLLECTION,
    limit: int = DEFAULT_PAGE_LIMIT,
    max_items: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    List items in a STAC collection, following pagination.

    Parameters
    ----------
    collection_name
        Collection id, e.g. ``lidar_quebec``.
    limit
        Page size requested from the server.
    max_items
        Stop after this many items. ``None`` walks every page.

    Returns
    -------
    list of raw STAC item dicts, in server order.

    Notes
    -----
    The API reports ``numberMatched``/``numberReturned`` as null, so the total
    is unknown until pagination is exhausted. Pass ``max_items`` to bound the
    walk.
    """
    url = f"{BASE_URL}/collections/{collection_name}/items"
    params: Optional[Dict[str, Any]] = {"limit": limit}
    items: List[Dict[str, Any]] = []

    while url:
        payload = _get_json(url, params=params)
        page = payload.get("features", [])
        items.extend(page)

        if max_items is not None and len(items) >= max_items:
            return items[:max_items]
        if not page:
            break

        next_link = next((link for link in payload.get("links", []) if link.get("rel") == "next"), None)
        url = next_link.get("href") if next_link else ""
        params = None  # the next href already carries its own query string

    return items


def get_item_metadata(item_id: str, collection_name: str = LIDAR_COLLECTION) -> Dict[str, Any]:
    """
    Fetch one STAC item and extract the fields Spatializer needs.

    Returns
    -------
    dict with keys:
        item_id, collection, bbox, geometry, epsg, product,
        asset_key, asset_href, asset_type, nodata, data_type,
        band_description, resolution_m, mean_degrees, mean_percent

    Notes
    -----
    ``mean_degrees`` and ``mean_percent`` are always ``None`` here. Those are
    returned by the separate *process-api* endpoint
    (``/process-api/processes/lidar-fetch/execution``), not by STAC. The STAC
    item carries no summary statistics. For real statistics use
    ``get_raster_statistics``.

    ``resolution_m`` is parsed out of the free-text band description
    (e.g. "...(2 m resolution)"). It is ``None`` when the text does not match —
    there is no structured resolution field in the item.

    ``asset_href`` is a server-side path and can be passed directly to the
    raster-api functions below.
    """
    if not item_id or not isinstance(item_id, str):
        raise ValueError(f"item_id must be a non-empty string, got: {item_id!r}")

    url = f"{BASE_URL}/collections/{collection_name}/items/{item_id}"
    item = _get_json(url)

    properties = item.get("properties", {})
    assets = item.get("assets", {})

    asset_key = next(iter(assets), None)
    asset = assets.get(asset_key, {}) if asset_key else {}

    bands = asset.get("raster:bands", [])
    band = bands[0] if bands else {}
    band_description = band.get("description")

    return {
        "item_id": item.get("id"),
        "collection": collection_name,
        "bbox": item.get("bbox"),
        "geometry": item.get("geometry"),
        "epsg": properties.get("proj:epsg"),
        "product": properties.get("lidar:product"),
        "asset_key": asset_key,
        "asset_href": asset.get("href"),
        "asset_type": asset.get("type"),
        "nodata": band.get("nodata"),
        "data_type": band.get("data_type"),
        "band_description": band_description,
        "resolution_m": _parse_resolution_m(band_description),
        # Not available from STAC — see Notes.
        "mean_degrees": None,
        "mean_percent": None,
    }


def _parse_resolution_m(description: Optional[str]) -> Optional[float]:
    """
    Extract a metre resolution from a free-text band description.

    Returns ``None`` if the description is absent or does not contain a
    recognisable "<number> m resolution" phrase. No default is substituted.
    """
    if not description:
        return None
    import re

    match = re.search(r"(\d+(?:\.\d+)?)\s*m\s+resolution", description, re.IGNORECASE)
    return float(match.group(1)) if match else None


# ============================================================
# raster-api layer — pixel access (TiTiler, server-side GDAL)
# ============================================================


def _get_raster_json(
    path: str,
    params: Dict[str, Any],
    timeout: int = DEFAULT_TIMEOUT_S,
) -> Dict[str, Any]:
    """
    GET a raster-api endpoint and return parsed JSON.

    Raises
    ------
    LidarClientError
        On any non-200. TiTiler reports *all* failures as HTTP 500 with a JSON
        ``detail`` string — missing file, unreachable remote URL, and point
        outside bounds are indistinguishable by status code alone — so the
        ``detail`` text is surfaced in the message.
    """
    url = f"{RASTER_API_URL}{path}"
    response = requests.get(url, params=params, timeout=timeout)
    if response.status_code != 200:
        detail = ""
        try:
            detail = response.json().get("detail", "")
        except ValueError:
            detail = response.text[:200]
        raise LidarClientError(f"raster-api {path} returned HTTP {response.status_code}: {detail}")
    return response.json()


def get_raster_info(asset_url: str) -> Dict[str, Any]:
    """
    Metadata for a COG: dimensions, dtype, nodata, CRS, overviews.

    Parameters
    ----------
    asset_url
        Server-side asset path, e.g. ``/data/lidar_slope_geom_a2e4c82b.tif``.
        This is the value STAC publishes as ``assets[].href``.

    Returns
    -------
    dict
        Raw TiTiler response. Keys observed: bounds, crs, band_metadata,
        band_descriptions, dtype, nodata_type, colorinterp, scales, offsets,
        driver, count, width, height, overviews, nodata_value.

    Raises
    ------
    ValueError
        If ``asset_url`` is empty.
    LidarClientError
        If the server cannot open the asset.
    """
    if not asset_url:
        raise ValueError("asset_url must be a non-empty string")
    return _get_raster_json("/cog/info", {"url": asset_url})


def get_raster_statistics(asset_url: str, max_size: Optional[int] = None) -> Dict[str, Any]:
    """
    Per-band statistics for a COG.

    Parameters
    ----------
    asset_url
        Server-side asset path.
    max_size
        Longest edge, in pixels, of the decimated read. **TiTiler decimates to
        roughly 1024x1024 by default**, so statistics are not full-resolution
        unless this is raised to the raster's own width/height. Verified: the
        two differ (notes_raster_api.md section 3). ``None`` uses the server
        default.

    Returns
    -------
    dict
        Band name to statistics dict. Per-band keys observed: min, max, mean,
        count, sum, std, median, majority, minority, unique, histogram,
        valid_percent, masked_pixels, valid_pixels, description,
        percentile_2, percentile_98.

    Raises
    ------
    ValueError
        If ``asset_url`` is empty or ``max_size`` is not positive.
    LidarClientError
        If the server cannot open the asset.
    """
    if not asset_url:
        raise ValueError("asset_url must be a non-empty string")
    params: Dict[str, Any] = {"url": asset_url}
    if max_size is not None:
        if max_size <= 0:
            raise ValueError(f"max_size must be positive, got {max_size}")
        params["max_size"] = max_size
    return _get_raster_json("/cog/statistics", params, timeout=STATISTICS_TIMEOUT_S)


def get_point_value(asset_url: str, lon: float, lat: float, band_index: int = 0) -> float:
    """
    Sample one pixel value at a coordinate.

    Parameters
    ----------
    asset_url
        Server-side asset path.
    lon, lat
        Coordinate in the raster's CRS (EPSG:4326 for the LiDAR products).
    band_index
        Which band to read from the returned ``values`` list. Defaults to the
        first; the LiDAR COGs are single-band (``count: 1``).

    Returns
    -------
    float
        The pixel value.

    Raises
    ------
    ValueError
        If ``asset_url`` is empty, or the band index is out of range.
    LidarClientError
        If the server cannot open the asset, or the point falls outside the
        raster bounds (TiTiler reports this as HTTP 500,
        ``"Point is outside dataset bounds"``).
    """
    if not asset_url:
        raise ValueError("asset_url must be a non-empty string")

    payload = _get_raster_json(f"/cog/point/{lon},{lat}", {"url": asset_url})
    values = payload.get("values", [])
    if band_index >= len(values):
        raise ValueError(f"band_index {band_index} out of range; response has {len(values)} band(s)")
    return float(values[band_index])


def sample_points(
    asset_url: str,
    coords: Sequence[Tuple[float, float]],
    band_index: int = 0,
) -> List[float]:
    """
    Sample several coordinates from one raster.

    Parameters
    ----------
    asset_url
        Server-side asset path.
    coords
        Sequence of ``(lon, lat)`` pairs.
    band_index
        Band to read, passed through to ``get_point_value``.

    Returns
    -------
    list of float, in the same order as ``coords``.

    Raises
    ------
    ValueError
        If ``coords`` is empty or an entry is not a 2-tuple.
    LidarClientError
        Propagated from the first failing point, including out-of-bounds.

    Notes
    -----
    **raster-api exposes no batch point endpoint**, so this issues one HTTP
    request per coordinate. Cost is linear in ``len(coords)``; callers sampling
    many points should expect proportional latency.
    """
    if not coords:
        raise ValueError("coords must not be empty")

    values: List[float] = []
    for position, pair in enumerate(coords):
        if len(pair) != 2:
            raise ValueError(f"coords[{position}] must be a (lon, lat) pair, got: {pair!r}")
        lon, lat = pair
        values.append(get_point_value(asset_url, lon, lat, band_index=band_index))
    return values


def list_collections() -> List[str]:
    """
    List collection ids known to raster-api.

    Returns
    -------
    list of str
        Collection ids, e.g. ``lidar_slope_geom_a2e4c82b``. These match STAC
        item ids, so ``asset_path_for_item`` maps them to asset paths.

    Notes
    -----
    The endpoint returns ``{"collections": [{"id", "title"}, ...]}`` — ids and
    titles only, with no bbox, links or asset paths.
    """
    payload = _get_raster_json("/collections", {})
    return [collection["id"] for collection in payload.get("collections", []) if "id" in collection]
