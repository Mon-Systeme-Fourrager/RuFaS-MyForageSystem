"""
Spatializer v0.1 — MSFourrager

Splits an agricultural field into 1-3 topographic zones based on 
mean slope. Prototype version — uses scalar mean slope, assigns 
100% of field to single dominant zone.

See spatializer_design.md for full contract and rationale.
"""

from typing import Dict, Any


# ============================================================
# Slope thresholds (PLACEHOLDERS — pending Quebec validation)
# ============================================================

SLOPE_THRESHOLD_FLAT_MAX = 3.0    # % — flat zone if slope < this
SLOPE_THRESHOLD_MEDIUM_MAX = 8.0  # % — medium zone if flat < slope <= this
# Above 8% → steep zone


def classify_slope(slope_pct: float) -> str:
    """Return zone label based on slope value."""
    if slope_pct < SLOPE_THRESHOLD_FLAT_MAX:
        return "zone_flat"
    elif slope_pct <= SLOPE_THRESHOLD_MEDIUM_MAX:
        return "zone_medium"
    else:
        return "zone_steep"


def spatialize_field(field: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Split a field into topographic zones.
    
    v0.1: uses scalar mean slope, assigns 100% of field to the 
    dominant zone. Multi-zone splitting requires slope raster 
    (planned for v0.2).
    
    Args:
        field: dict with field_id, total_area_ha, mean_slope_pct, soil
    
    Returns:
        dict of zones, each with field_size_fraction + soil params
    
    Raises:
        ValueError: if required fields missing or invalid
    """
    
    # Validation
    required = ["field_id", "total_area_ha", "mean_slope_pct", "soil"]
    for key in required:
        if key not in field:
            raise ValueError(f"Missing required field: {key}")
    
    soil_required = ["clay_pct", "silt_pct", "OM_pct", "bulk_density"]
    for key in soil_required:
        if key not in field["soil"]:
            raise ValueError(f"Missing required soil parameter: {key}")
    
    if field["total_area_ha"] <= 0:
        raise ValueError(f"total_area_ha must be positive: {field['total_area_ha']}")
    
    # Classify
    zone_label = classify_slope(field["mean_slope_pct"])
    
    # Build zone dict (100% of field in dominant zone for v0.1)
    zones = {
        zone_label: {
            "field_size_fraction": 1.0,
            "slope_pct": field["mean_slope_pct"],
            "clay_pct": field["soil"]["clay_pct"],
            "silt_pct": field["soil"]["silt_pct"],
            "OM_pct": field["soil"]["OM_pct"],
            "bulk_density": field["soil"]["bulk_density"],
        }
    }
    
    # Invariant check
    total_fraction = sum(z["field_size_fraction"] for z in zones.values())
    assert abs(total_fraction - 1.0) < 1e-9, (
        f"Mass balance violation: sum of fractions = {total_fraction}"
    )
    
    return zones


# ============================================================
# Test with dummy field
# ============================================================

if __name__ == "__main__":
    # Dummy field: loam Quebec, moderate slope
    dummy_field = {
        "field_id": "test_field_001",
        "total_area_ha": 12.5,
        "mean_slope_pct": 4.2,
        "soil": {
            "clay_pct": 25.0,
            "silt_pct": 40.0,
            "OM_pct": 3.5,
            "bulk_density": 1.35,
        }
    }
    
    print("=" * 60)
    print("Spatializer v0.1 — dummy test")
    print("=" * 60)
    print(f"\nInput field:")
    print(f"  ID: {dummy_field['field_id']}")
    print(f"  Area: {dummy_field['total_area_ha']} ha")
    print(f"  Mean slope: {dummy_field['mean_slope_pct']}%")
    print(f"  Soil: clay={dummy_field['soil']['clay_pct']}%, "
          f"silt={dummy_field['soil']['silt_pct']}%, "
          f"BD={dummy_field['soil']['bulk_density']}")
    
    zones = spatialize_field(dummy_field)
    
    print(f"\nOutput zones ({len(zones)}):")
    for zone_name, zone_data in zones.items():
        print(f"\n  {zone_name}:")
        for key, val in zone_data.items():
            print(f"    {key}: {val}")
    
    print(f"\nMass balance check: "
          f"sum(fractions) = {sum(z['field_size_fraction'] for z in zones.values())}")
    print("=" * 60)