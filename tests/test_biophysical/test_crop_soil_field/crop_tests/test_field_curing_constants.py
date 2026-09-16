"""Tests for RUFAS/biophysical/field/crop/field_curing_constants.py.

Covers the module importing cleanly plus every constant defined by Task 1
(DAFOSYM respiration/rain terms + unit conversions) and Task 2 (Rotz & Chen
1985 drying-rate coefficients) of
``PLAN_add-preharvest-field-curing-phase.md``.
"""

import pytest

from RUFAS.biophysical.field.crop import field_curing_constants as fcc


@pytest.mark.unit
def test_celsius_to_fahrenheit_scale_exists() -> None:
    """CELSIUS_TO_FAHRENHEIT_SCALE must be 9/5."""
    assert fcc.CELSIUS_TO_FAHRENHEIT_SCALE == pytest.approx(9.0 / 5.0)


@pytest.mark.unit
def test_celsius_to_fahrenheit_offset_exists() -> None:
    """CELSIUS_TO_FAHRENHEIT_OFFSET must be 32.0."""
    assert fcc.CELSIUS_TO_FAHRENHEIT_OFFSET == pytest.approx(32.0)


@pytest.mark.unit
def test_mm_to_inches_divisor_exists() -> None:
    """MM_TO_INCHES_DIVISOR must be 25.4."""
    assert fcc.MM_TO_INCHES_DIVISOR == pytest.approx(25.4)


@pytest.mark.unit
def test_field_curing_respiration_coefficient_exists() -> None:
    """FIELD_CURING_RESPIRATION_COEFFICIENT must be 0.00239 (DAFOSYM Eq.7)."""
    assert fcc.FIELD_CURING_RESPIRATION_COEFFICIENT == pytest.approx(0.00239)


@pytest.mark.unit
def test_field_curing_respiration_moisture_threshold_exists() -> None:
    """FIELD_CURING_RESPIRATION_MOISTURE_THRESHOLD must be 0.27 (DAFOSYM Eq.7)."""
    assert fcc.FIELD_CURING_RESPIRATION_MOISTURE_THRESHOLD == pytest.approx(0.27)


@pytest.mark.unit
def test_field_curing_respiration_temp_coefficient_f_exists() -> None:
    """FIELD_CURING_RESPIRATION_TEMP_COEFFICIENT_F must be 0.038 (DAFOSYM Eq.7)."""
    assert fcc.FIELD_CURING_RESPIRATION_TEMP_COEFFICIENT_F == pytest.approx(0.038)


@pytest.mark.unit
def test_field_curing_rain_leaf_loss_coefficient_exists() -> None:
    """FIELD_CURING_RAIN_LEAF_LOSS_COEFFICIENT must be 0.094 (DAFOSYM Eq.9)."""
    assert fcc.FIELD_CURING_RAIN_LEAF_LOSS_COEFFICIENT == pytest.approx(0.094)


@pytest.mark.unit
def test_field_curing_rain_leaf_loss_cap_fraction_exists() -> None:
    """FIELD_CURING_RAIN_LEAF_LOSS_CAP_FRACTION must be 0.15 (DAFOSYM Eq.9)."""
    assert fcc.FIELD_CURING_RAIN_LEAF_LOSS_CAP_FRACTION == pytest.approx(0.15)


@pytest.mark.unit
def test_field_curing_leaching_rain_coefficient_exists() -> None:
    """FIELD_CURING_LEACHING_RAIN_COEFFICIENT must be 0.28 (DAFOSYM Eq.10)."""
    assert fcc.FIELD_CURING_LEACHING_RAIN_COEFFICIENT == pytest.approx(0.28)


@pytest.mark.unit
def test_field_curing_leaching_cp_multiplier_exists() -> None:
    """FIELD_CURING_LEACHING_CP_MULTIPLIER must be 1.2 (DAFOSYM Eq.11)."""
    assert fcc.FIELD_CURING_LEACHING_CP_MULTIPLIER == pytest.approx(1.2)


@pytest.mark.unit
def test_field_curing_rnl_max_exists() -> None:
    """FIELD_CURING_RNL_MAX must be 0.99 (numerical guard, not a DAFOSYM value)."""
    assert fcc.FIELD_CURING_RNL_MAX == pytest.approx(0.99)


@pytest.mark.unit
def test_drying_rate_solar_application_coefficient_exists() -> None:
    """DRYING_RATE_SOLAR_APPLICATION_COEFFICIENT must be 9.30 (Rotz & Chen 1985 Eq.5)."""
    assert fcc.DRYING_RATE_SOLAR_APPLICATION_COEFFICIENT == pytest.approx(9.30)


@pytest.mark.unit
def test_drying_rate_dry_bulb_coefficient_exists() -> None:
    """DRYING_RATE_DRY_BULB_COEFFICIENT must be 5.42 (Rotz & Chen 1985 Eq.5)."""
    assert fcc.DRYING_RATE_DRY_BULB_COEFFICIENT == pytest.approx(5.42)


@pytest.mark.unit
def test_drying_rate_soil_moisture_coefficient_exists() -> None:
    """DRYING_RATE_SOIL_MOISTURE_COEFFICIENT must be 66.4 (Rotz & Chen 1985 Eq.5)."""
    assert fcc.DRYING_RATE_SOIL_MOISTURE_COEFFICIENT == pytest.approx(66.4)


@pytest.mark.unit
def test_drying_rate_day_intercept_exists() -> None:
    """DRYING_RATE_DAY_INTERCEPT must be 2.06 (Rotz & Chen 1985 Eq.5)."""
    assert fcc.DRYING_RATE_DAY_INTERCEPT == pytest.approx(2.06)


@pytest.mark.unit
def test_drying_rate_day_slope_exists() -> None:
    """DRYING_RATE_DAY_SLOPE must be 0.97 (Rotz & Chen 1985 Eq.5)."""
    assert fcc.DRYING_RATE_DAY_SLOPE == pytest.approx(0.97)


@pytest.mark.unit
def test_drying_rate_application_denominator_intercept_exists() -> None:
    """DRYING_RATE_APPLICATION_DENOMINATOR_INTERCEPT must be 1.55 (Rotz & Chen 1985 Eq.5)."""
    assert fcc.DRYING_RATE_APPLICATION_DENOMINATOR_INTERCEPT == pytest.approx(1.55)


@pytest.mark.unit
def test_drying_rate_application_denominator_slope_exists() -> None:
    """DRYING_RATE_APPLICATION_DENOMINATOR_SLOPE must be 21.9 (Rotz & Chen 1985 Eq.5)."""
    assert fcc.DRYING_RATE_APPLICATION_DENOMINATOR_SLOPE == pytest.approx(21.9)


@pytest.mark.unit
def test_drying_rate_denominator_constant_exists() -> None:
    """DRYING_RATE_DENOMINATOR_CONSTANT must be 3037.0 (Rotz & Chen 1985 Eq.5)."""
    assert fcc.DRYING_RATE_DENOMINATOR_CONSTANT == pytest.approx(3037.0)


@pytest.mark.unit
def test_mj_per_m2_day_to_w_per_m2_exists() -> None:
    """MJ_PER_M2_DAY_TO_W_PER_M2 must be the 1e6/86400 J/s <-> J/day identity."""
    assert fcc.MJ_PER_M2_DAY_TO_W_PER_M2 == pytest.approx(1_000_000.0 / 86_400.0)


@pytest.mark.unit
def test_swath_moisture_equilibrium_fraction_exists() -> None:
    """SWATH_MOISTURE_EQUILIBRIUM_FRACTION must be 0.0 (Rotz & Chen 1985)."""
    assert fcc.SWATH_MOISTURE_EQUILIBRIUM_FRACTION == pytest.approx(0.0)
