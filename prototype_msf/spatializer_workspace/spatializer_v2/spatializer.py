"""
spatializer.py — Spatializer v0.2, MSFourrager

Splits an agricultural field into internal zones for per-zone RUFAS runs.

Two modes are foreseen:

* ``external_points`` — IMPLEMENTED. The caller supplies representative
  points, each with its own area share and soil/slope values. No raster is
  needed, so this mode works today.
* ``auto_cluster`` — NOT IMPLEMENTED. k-means over a LiDAR slope raster.
  Blocked: the raster cannot be fetched (see ``lidar_client.download_asset``
  and ``notes_exploration.md`` section 5).

Zone labelling reuses the v0.1 slope classification so that v0.1 and v0.2
produce comparable zone names.

See spatializer_design.md for the integration contract.
"""

from typing import Any, Dict, List

# ============================================================
# Slope thresholds (PLACEHOLDERS — pending Quebec validation)
# Carried over unchanged from Spatializer v0.1 for label continuity.
# ============================================================

SLOPE_THRESHOLD_FLAT_MAX = 3.0  # % — flat zone if slope < this
SLOPE_THRESHOLD_MEDIUM_MAX = 8.0  # % — medium zone if flat < slope <= this
# Above 8% -> steep zone

MASS_BALANCE_TOLERANCE = 1e-9

REQUIRED_FIELD_KEYS = ("field_id", "total_area_ha", "points")
REQUIRED_POINT_KEYS = ("field_size_fraction", "slope_pct", "soil")
REQUIRED_SOIL_KEYS = ("clay_pct", "silt_pct", "OM_pct", "bulk_density")


def classify_slope(slope_pct: float) -> str:
    """Return zone label based on slope value. Identical to v0.1."""
    if slope_pct < SLOPE_THRESHOLD_FLAT_MAX:
        return "zone_flat"
    elif slope_pct <= SLOPE_THRESHOLD_MEDIUM_MAX:
        return "zone_medium"
    else:
        return "zone_steep"


def spatialize_field_external_points(field: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Build zones from caller-supplied representative points.

    No clustering is performed. Each point becomes one zone, carrying the area
    share the caller assigned to it. This is the mode to use while the LiDAR
    raster is unavailable.

    Parameters
    ----------
    field
        dict with:
            field_id : str
            total_area_ha : float, must be positive
            points : list of dicts, each with
                field_size_fraction : float, non-negative
                slope_pct : float
                soil : dict with clay_pct, silt_pct, OM_pct, bulk_density

    Returns
    -------
    dict
        Zone label to zone data. Labels come from ``classify_slope``; when two
        points fall in the same slope class the label is suffixed
        (``zone_flat_2``) so no point is silently dropped.

    Raises
    ------
    ValueError
        If a required key is missing, ``total_area_ha`` is not positive,
        ``points`` is empty, a fraction is negative, or the fractions do not
        sum to 1.0.
    """
    for key in REQUIRED_FIELD_KEYS:
        if key not in field:
            raise ValueError(f"Missing required field: {key}")

    if field["total_area_ha"] <= 0:
        raise ValueError(f"total_area_ha must be positive: {field['total_area_ha']}")

    points = field["points"]
    if not isinstance(points, list) or not points:
        raise ValueError("points must be a non-empty list")

    zones: Dict[str, Dict[str, Any]] = {}
    fraction_total = 0.0

    for position, point in enumerate(points):
        for key in REQUIRED_POINT_KEYS:
            if key not in point:
                raise ValueError(f"points[{position}] missing required key: {key}")

        for key in REQUIRED_SOIL_KEYS:
            if key not in point["soil"]:
                raise ValueError(f"points[{position}] missing required soil parameter: {key}")

        fraction = point["field_size_fraction"]
        if fraction < 0.0:
            raise ValueError(f"points[{position}] field_size_fraction must be non-negative, got {fraction}")

        fraction_total += fraction

        label = _unique_label(classify_slope(point["slope_pct"]), zones)
        zones[label] = {
            "field_size_fraction": fraction,
            "slope_pct": point["slope_pct"],
            "clay_pct": point["soil"]["clay_pct"],
            "silt_pct": point["soil"]["silt_pct"],
            "OM_pct": point["soil"]["OM_pct"],
            "bulk_density": point["soil"]["bulk_density"],
        }

    if abs(fraction_total - 1.0) > MASS_BALANCE_TOLERANCE:
        raise ValueError(f"field_size_fraction values must sum to 1.0, got {fraction_total}")

    # Invariant check — mirrors v0.1.
    total_fraction = sum(z["field_size_fraction"] for z in zones.values())
    assert abs(total_fraction - 1.0) < MASS_BALANCE_TOLERANCE, (
        f"Mass balance violation: sum of fractions = {total_fraction}"
    )

    return zones


def _unique_label(base_label: str, existing: Dict[str, Any]) -> str:
    """
    Return ``base_label``, or a numbered variant if it is already taken.

    Two representative points can share a slope class. Suffixing keeps both
    rather than overwriting one, which would break the mass balance.
    """
    if base_label not in existing:
        return base_label
    suffix = 2
    while f"{base_label}_{suffix}" in existing:
        suffix += 1
    return f"{base_label}_{suffix}"


def spatialize_field_auto_cluster(field: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Cluster a field into zones from a LiDAR slope raster.

    Raises
    ------
    NotImplementedError
        Always. This mode needs per-pixel slope values, and the raster cannot
        currently be fetched.

    Notes
    -----
    Verified 2026-09-03 (notes_exploration.md section 5): STAC asset hrefs are
    relative paths that return HTTP 404, and the API declares no asset-serving
    route. Until Jérémie exposes the assets there is no slope raster to cluster
    over, so no clustering logic is written here — an implementation against a
    guessed raster shape could not be tested.

    Use ``spatialize_field_external_points`` in the meantime.
    """
    raise NotImplementedError(
        "auto_cluster mode requires a LiDAR slope raster, which cannot currently be "
        "downloaded: STAC asset hrefs are relative paths (/data/*.tif) that return "
        "HTTP 404, and the API declares no asset-serving route. Awaiting Jérémie's "
        "server fix on asset routes. See notes_exploration.md section 5. "
        "Use spatialize_field_external_points() instead."
    )


# ============================================================
# Demo with a dummy field (mirrors the v0.1 __main__ block)
# ============================================================

if __name__ == "__main__":
    dummy_field = {
        "field_id": "test_field_002",
        "total_area_ha": 18.87,
        "points": [
            {
                "field_size_fraction": 0.6,
                "slope_pct": 1.8,
                "soil": {"clay_pct": 25.0, "silt_pct": 40.0, "OM_pct": 3.5, "bulk_density": 1.35},
            },
            {
                "field_size_fraction": 0.4,
                "slope_pct": 5.4,
                "soil": {"clay_pct": 22.0, "silt_pct": 43.0, "OM_pct": 3.1, "bulk_density": 1.42},
            },
        ],
    }

    print("=" * 60)
    print("Spatializer v0.2 — external_points demo")
    print("=" * 60)
    print("\nInput field:")
    print(f"  ID: {dummy_field['field_id']}")
    print(f"  Area: {dummy_field['total_area_ha']} ha")
    print(f"  Representative points: {len(dummy_field['points'])}")

    result_zones = spatialize_field_external_points(dummy_field)

    print(f"\nOutput zones ({len(result_zones)}):")
    for zone_name, zone_data in result_zones.items():
        print(f"\n  {zone_name}:")
        for key, val in zone_data.items():
            print(f"    {key}: {val}")

    print(
        "\nMass balance check: "
        f"sum(fractions) = {sum(z['field_size_fraction'] for z in result_zones.values())}"
    )
    print("=" * 60)
