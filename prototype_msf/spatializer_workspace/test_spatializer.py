"""
Tests for spatializer.py v0.1

Run with:
    python test_spatializer.py

Or with pytest:
    pytest test_spatializer.py -v
"""

import pytest
from spatializer import spatialize_field, classify_slope


# ============================================================
# Helper — build a valid dummy field
# ============================================================

def make_field(slope=4.0, area=10.0):
    """Return a valid field dict with given slope and area."""
    return {
        "field_id": "test_field",
        "total_area_ha": area,
        "mean_slope_pct": slope,
        "soil": {
            "clay_pct": 25.0,
            "silt_pct": 40.0,
            "OM_pct": 3.5,
            "bulk_density": 1.35,
        }
    }


# ============================================================
# Test 1 — Slope classification (3 zones)
# ============================================================

def test_flat_zone():
    """Slope < 3% should classify as zone_flat"""
    field = make_field(slope=1.5)
    zones = spatialize_field(field)
    assert "zone_flat" in zones
    assert zones["zone_flat"]["field_size_fraction"] == 1.0


def test_medium_zone():
    """Slope between 3% and 8% should classify as zone_medium"""
    field = make_field(slope=4.2)
    zones = spatialize_field(field)
    assert "zone_medium" in zones
    assert zones["zone_medium"]["field_size_fraction"] == 1.0


def test_steep_zone():
    """Slope > 8% should classify as zone_steep"""
    field = make_field(slope=12.0)
    zones = spatialize_field(field)
    assert "zone_steep" in zones
    assert zones["zone_steep"]["field_size_fraction"] == 1.0


# ============================================================
# Test 2 — Boundary conditions (edge cases at thresholds)
# ============================================================

def test_boundary_flat_to_medium():
    """Slope exactly at 3.0 should be classified as medium (not flat)"""
    field = make_field(slope=3.0)
    zones = spatialize_field(field)
    assert "zone_medium" in zones


def test_boundary_medium_to_steep():
    """Slope exactly at 8.0 should be classified as medium (not steep)"""
    field = make_field(slope=8.0)
    zones = spatialize_field(field)
    assert "zone_medium" in zones


def test_slope_just_above_steep():
    """Slope 8.01 should classify as steep"""
    field = make_field(slope=8.01)
    zones = spatialize_field(field)
    assert "zone_steep" in zones


# ============================================================
# Test 3 — Mass balance invariant
# ============================================================

def test_mass_balance():
    """Sum of field_size_fractions must always equal 1.0"""
    for slope in [0.5, 3.0, 5.0, 8.0, 15.0, 25.0]:
        field = make_field(slope=slope)
        zones = spatialize_field(field)
        total = sum(z["field_size_fraction"] for z in zones.values())
        assert abs(total - 1.0) < 1e-9, f"Slope {slope}: total = {total}"


# ============================================================
# Test 4 — Soil parameters preserved (no fabrication)
# ============================================================

def test_soil_params_preserved():
    """Soil params must be inherited exactly from input, no fabrication"""
    field = make_field(slope=5.0)
    zones = spatialize_field(field)
    zone = list(zones.values())[0]
    
    assert zone["clay_pct"] == field["soil"]["clay_pct"]
    assert zone["silt_pct"] == field["soil"]["silt_pct"]
    assert zone["OM_pct"] == field["soil"]["OM_pct"]
    assert zone["bulk_density"] == field["soil"]["bulk_density"]
    assert zone["slope_pct"] == field["mean_slope_pct"]


# ============================================================
# Test 5 — Input validation (errors expected)
# ============================================================

def test_missing_field_id():
    """Missing field_id should raise ValueError"""
    field = make_field()
    del field["field_id"]
    with pytest.raises(ValueError, match="field_id"):
        spatialize_field(field)


def test_missing_soil_param():
    """Missing soil parameter should raise ValueError"""
    field = make_field()
    del field["soil"]["clay_pct"]
    with pytest.raises(ValueError, match="clay_pct"):
        spatialize_field(field)


def test_negative_area():
    """Negative area should raise ValueError"""
    field = make_field(area=-5.0)
    with pytest.raises(ValueError, match="total_area_ha"):
        spatialize_field(field)


def test_zero_area():
    """Zero area should raise ValueError"""
    field = make_field(area=0.0)
    with pytest.raises(ValueError, match="total_area_ha"):
        spatialize_field(field)


# ============================================================
# Test 6 — Classify slope helper (unit