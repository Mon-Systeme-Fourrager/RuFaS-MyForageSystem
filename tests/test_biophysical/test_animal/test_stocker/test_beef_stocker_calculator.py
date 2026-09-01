"""Tests for BeefStockerRequirementsCalculator — Step 3 NRC 2016 benchmarks.

All four NRC 2016 benchmark scenarios (SK-MAINT-1, SK-GROW-1, SK-DMI-1, SK-MP-1)
are verified against analytically-derived values from NRC 2016 Ch.10-12 equations.
Do NOT use BeefGEM outputs as test oracle (NRC 2000 / monthly timestep mismatch).

Also verifies:
- StockerRequirementsInputs type-guard (non-stocker animal_type raises ValueError)
- Weight/sex input validation (NaN, zero, non-finite raise ValueError)
- NotImplementedError guards on BeefNRCRequirementsCalculator and
  BeefCowCalfRequirementsCalculator when passed stocker animal types
"""

from __future__ import annotations

import math

import pytest

from RUFAS.biophysical.animal.animal_module_constants import AnimalModuleConstants
from RUFAS.biophysical.animal.data_types.animal_enums import Sex
from RUFAS.biophysical.animal.data_types.animal_types import AnimalType
from RUFAS.biophysical.animal.nutrients.beef_cow_calf_requirements_calculator import (
    BeefCowCalfRequirementsCalculator,
    CowCalfRequirementsInputs,
)
from RUFAS.biophysical.animal.nutrients.beef_nrc_requirements_calculator import (
    BeefNRCRequirementsCalculator,
)
from RUFAS.biophysical.animal.nutrients.beef_stocker_requirements_calculator import (
    BeefStockerRequirementsCalculator,
    StockerRequirementsInputs,
)

# ---------------------------------------------------------------------------
# NRC 2016 benchmark scenario — 280 kg Angus steer (source: NRC 2016 Ch.10-12)
# ---------------------------------------------------------------------------

_BENCHMARK_BW = 280.0  # kg live weight
_BENCHMARK_MBW = 520.0  # kg, beef_mature_cow_weight_kg (NOT stocker exit weight)
_BENCHMARK_ADG = 0.80  # kg/d
_BENCHMARK_NE_DIET = 1.0  # Mcal/kg DM forage (Eq.10-5 input)
_BENCHMARK_TEMP = 20.0  # °C thermoneutral — a2 cold-stress term = 0

# Analytically-derived expected values from NRC 2016 equations:
# SK-MAINT-1: NEm = SBW^0.75 × 0.077 × BE × SEX (no mud, thermoneutral)
#   SBW=268.8, SBW^0.75≈66.39, BE=1.0 (Angus), SEX=1.00 (steer)
#   NEm = 66.39 × 0.077 = 5.112 Mcal/d
_SK_MAINT_1_EXPECTED_NEM = 5.112  # Mcal/d  (tolerance ±3%)

# SK-GROW-1: NEg via NRC 2016 Eq.12-3
#   MSBW=499.2, EQSBW=257.46, EQEBW=229.39, EBG=0.7648
#   NEg = 0.0635 × 229.39^0.75 × 0.7648^1.097 ≈ 2.789 Mcal/d
_SK_GROW_1_EXPECTED_NEG = 2.789  # Mcal/d  (tolerance ±3%)

# SK-DMI-1: DMI via NRC 2016 Eq.10-5 (stocker formula, no intercept, no lact)
#   BW^0.75=68.45, ne_c=1.0
#   ne_m_intake = 68.45 × (0.04997 × 1.0² + 0.04631 × 1.0) = 68.45 × 0.09628 = 6.592
#   DMI = 6.592 / 1.0 = 6.592 kg/d
_SK_DMI_1_EXPECTED_DMI = 6.592  # kg/d  (tolerance ±3%)

# SK-MP-1: MP via NRC 2016 Ch.6 / Box 12-1
#   NPg=132.38 g/d, eff_g=0.5405, MPm=260.10 g/d, MPg=244.93 g/d, MP≈505.0 g/d
_SK_MP_1_EXPECTED_MP = 505.0  # g/d  (tolerance ±5%)


def _make_benchmark_inputs(**overrides: object) -> StockerRequirementsInputs:
    """Build a StockerRequirementsInputs with benchmark values and optional overrides."""
    defaults: dict[str, object] = {
        "animal_type": AnimalType.BEEF_STOCKER_STEER,
        "sex": Sex.STEER,
        "body_weight": _BENCHMARK_BW,
        "mature_body_weight": _BENCHMARK_MBW,
        "breed": "Angus",
        "target_adg": _BENCHMARK_ADG,
        "temperature_c": _BENCHMARK_TEMP,
        "ne_diet_concentration": _BENCHMARK_NE_DIET,
        "mud_condition": AnimalModuleConstants.BEEF_MUD_CONDITION_NONE,
    }
    defaults.update(overrides)
    return StockerRequirementsInputs(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# NRC 2016 benchmark tests — write FIRST, confirm RED before implementing
# ---------------------------------------------------------------------------


@pytest.mark.nrc2016
def test_nrc_benchmark_sk_maint_1() -> None:
    """SK-MAINT-1: NEm for 280 kg Angus steer, thermoneutral, no mud.

    Source: NRC 2016 Eq.11-1. NEm = SBW^0.75 × 0.077 × BE × SEX.
    SBW=268.8, BE=1.0 (Angus), SEX=1.00 (steer), a2=0 (thermoneutral).
    Expected ≈ 5.112 Mcal/d, tolerance ±3%.
    """
    result = BeefStockerRequirementsCalculator.calculate_requirements(_make_benchmark_inputs())
    assert result.maintenance_energy == pytest.approx(_SK_MAINT_1_EXPECTED_NEM, rel=0.03)


@pytest.mark.nrc2016
def test_nrc_benchmark_sk_grow_1() -> None:
    """SK-GROW-1: NEg for 280 kg steer at ADG 0.80 kg/d.

    Source: NRC 2016 Eq.12-3. NEg = 0.0635 × EQEBW^0.75 × EBG^1.097.
    EQSBW=257.46 (mature BW=520 kg), EQEBW=229.39, EBG=0.7648.
    Expected ≈ 2.789 Mcal/d, tolerance ±3%.
    """
    result = BeefStockerRequirementsCalculator.calculate_requirements(_make_benchmark_inputs())
    assert result.growth_energy == pytest.approx(_SK_GROW_1_EXPECTED_NEG, rel=0.03)


@pytest.mark.nrc2016
def test_nrc_benchmark_sk_dmi_1() -> None:
    """SK-DMI-1: DMI for 280 kg steer at forage NEm = 1.0 Mcal/kg DM.

    Source: NRC 2016 Eq.10-5 (forage-based growing cattle).
    No pregnancy intercept, no lactation term.
    BW^0.75=68.45, ne_c=1.0, expected ≈ 6.592 kg/d, tolerance ±3%.
    """
    result = BeefStockerRequirementsCalculator.calculate_requirements(_make_benchmark_inputs())
    assert result.dry_matter == pytest.approx(_SK_DMI_1_EXPECTED_DMI, rel=0.03)


@pytest.mark.nrc2016
def test_nrc_benchmark_sk_mp_1() -> None:
    """SK-MP-1: MP for 280 kg steer at ADG 0.80 kg/d.

    Source: NRC 2016 Ch.6 / Box 12-1.
    MPm=3.8×BW^0.75, MPg=NPg/eff_g, eff_g=max(0.492, 0.834-0.00114×EQSBW).
    Expected ≈ 505 g/d, tolerance ±5%.
    """
    result = BeefStockerRequirementsCalculator.calculate_requirements(_make_benchmark_inputs())
    assert result.metabolizable_protein == pytest.approx(_SK_MP_1_EXPECTED_MP, rel=0.05)


# ---------------------------------------------------------------------------
# Type guard — non-stocker animal_type must raise ValueError
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_calculate_requirements_raises_for_feedlot_steer() -> None:
    """FEEDLOT_STEER passed to stocker calculator must raise ValueError."""
    inputs = _make_benchmark_inputs(animal_type=AnimalType.FEEDLOT_STEER)
    with pytest.raises(ValueError, match="stocker"):
        BeefStockerRequirementsCalculator.calculate_requirements(inputs)


@pytest.mark.unit
def test_calculate_requirements_raises_for_cow_calf_type() -> None:
    """BEEF_COW passed to stocker calculator must raise ValueError."""
    inputs = _make_benchmark_inputs(animal_type=AnimalType.BEEF_COW)
    with pytest.raises(ValueError, match="stocker"):
        BeefStockerRequirementsCalculator.calculate_requirements(inputs)


# ---------------------------------------------------------------------------
# Weight validation — body_weight and mature_body_weight must be finite and > 0
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize("bad_bw", [0.0, -1.0, float("nan"), float("inf")])
def test_calculate_requirements_invalid_body_weight(bad_bw: float) -> None:
    """body_weight must be positive and finite; zero/negative/NaN/inf raise ValueError."""
    inputs = _make_benchmark_inputs(body_weight=bad_bw)
    with pytest.raises(ValueError, match="body_weight"):
        BeefStockerRequirementsCalculator.calculate_requirements(inputs)


@pytest.mark.unit
@pytest.mark.parametrize("bad_mbw", [0.0, -1.0, float("nan"), float("inf")])
def test_calculate_requirements_invalid_mature_body_weight(bad_mbw: float) -> None:
    """mature_body_weight must be positive and finite; invalid values raise ValueError."""
    inputs = _make_benchmark_inputs(mature_body_weight=bad_mbw)
    with pytest.raises(ValueError, match="mature_body_weight"):
        BeefStockerRequirementsCalculator.calculate_requirements(inputs)


# ---------------------------------------------------------------------------
# Sex validation — must be a member of SEX_NEm_MULTIPLIER
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_calculate_requirements_valid_sex_female() -> None:
    """Sex.FEMALE (heifer) must be accepted without raising."""
    inputs = _make_benchmark_inputs(animal_type=AnimalType.BEEF_STOCKER_HEIFER, sex=Sex.FEMALE)
    result = BeefStockerRequirementsCalculator.calculate_requirements(inputs)
    assert math.isfinite(result.maintenance_energy)
    assert result.maintenance_energy > 0.0


@pytest.mark.unit
def test_calculate_requirements_stocker_heifer_lower_eqsbw() -> None:
    """BEEF_STOCKER_HEIFER with Sex.FEMALE should produce finite positive requirements."""
    inputs = _make_benchmark_inputs(
        animal_type=AnimalType.BEEF_STOCKER_HEIFER,
        sex=Sex.FEMALE,
        body_weight=260.0,
    )
    result = BeefStockerRequirementsCalculator.calculate_requirements(inputs)
    assert result.growth_energy >= 0.0
    assert result.metabolizable_protein > 0.0


# ---------------------------------------------------------------------------
# Structural checks — pregnancy/lactation fields must be zero for stocker
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_pregnancy_energy_is_zero() -> None:
    """Stocker animals never gestate; pregnancy_energy must be 0.0."""
    result = BeefStockerRequirementsCalculator.calculate_requirements(_make_benchmark_inputs())
    assert result.pregnancy_energy == pytest.approx(0.0)


@pytest.mark.unit
def test_lactation_energy_is_zero() -> None:
    """Stocker animals never lactate; lactation_energy must be 0.0."""
    result = BeefStockerRequirementsCalculator.calculate_requirements(_make_benchmark_inputs())
    assert result.lactation_energy == pytest.approx(0.0)


@pytest.mark.unit
def test_activity_energy_is_zero() -> None:
    """Activity energy is not modelled for stocker; activity_energy must be 0.0."""
    result = BeefStockerRequirementsCalculator.calculate_requirements(_make_benchmark_inputs())
    assert result.activity_energy == pytest.approx(0.0)


@pytest.mark.unit
def test_dmi_clamp_below_min_ne_concentration_returns_same_as_at_clamp() -> None:
    """ne_diet_concentration below BEEF_DMI_MIN_NE_CONCENTRATION is clamped; must not raise.

    Both at-clamp and below-clamp calls must produce the same DMI because
    the floor ensures identical effective ne_c in Eq.10-5.
    """
    at_clamp = BeefStockerRequirementsCalculator.calculate_requirements(
        _make_benchmark_inputs(ne_diet_concentration=AnimalModuleConstants.BEEF_DMI_MIN_NE_CONCENTRATION)
    )
    below_clamp = BeefStockerRequirementsCalculator.calculate_requirements(
        _make_benchmark_inputs(ne_diet_concentration=0.1)
    )
    assert below_clamp.dry_matter == pytest.approx(at_clamp.dry_matter)


# ---------------------------------------------------------------------------
# NotImplementedError guards on existing beef calculators
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_beef_nrc_calc_raises_not_implemented_for_stocker_steer() -> None:
    """BeefNRCRequirementsCalculator must raise NotImplementedError for BEEF_STOCKER_STEER."""
    with pytest.raises(NotImplementedError, match="BeefStockerRequirementsCalculator"):
        BeefNRCRequirementsCalculator.calculate_requirements(
            body_weight=280.0,
            mature_body_weight=520.0,
            animal_type=AnimalType.BEEF_STOCKER_STEER,
            breed="Angus",
            sex=Sex.STEER,
            days_on_feed=0,
            target_adg=0.80,
            implant_adg_factor=1.0,
            housing="Open_Lot",
            mud_condition=AnimalModuleConstants.BEEF_MUD_CONDITION_NONE,
            temperature_c=20.0,
            ne_diet_concentration=1.0,
            process_based_phosphorus_requirement=0.0,
        )


@pytest.mark.unit
def test_beef_nrc_calc_raises_not_implemented_for_stocker_heifer() -> None:
    """BeefNRCRequirementsCalculator must raise NotImplementedError for BEEF_STOCKER_HEIFER."""
    with pytest.raises(NotImplementedError, match="BeefStockerRequirementsCalculator"):
        BeefNRCRequirementsCalculator.calculate_requirements(
            body_weight=260.0,
            mature_body_weight=520.0,
            animal_type=AnimalType.BEEF_STOCKER_HEIFER,
            breed="Angus",
            sex=Sex.FEMALE,
            days_on_feed=0,
            target_adg=0.80,
            implant_adg_factor=1.0,
            housing="Open_Lot",
            mud_condition=AnimalModuleConstants.BEEF_MUD_CONDITION_NONE,
            temperature_c=20.0,
            ne_diet_concentration=1.0,
            process_based_phosphorus_requirement=0.0,
        )


@pytest.mark.unit
def test_beef_cow_calf_calc_raises_not_implemented_for_stocker_steer() -> None:
    """BeefCowCalfRequirementsCalculator must raise NotImplementedError for BEEF_STOCKER_STEER."""
    inputs = CowCalfRequirementsInputs(
        body_weight=280.0,
        mature_body_weight=520.0,
        animal_type=AnimalType.BEEF_STOCKER_STEER,
        breed="Angus",
        sex=Sex.STEER,
        body_condition_score=5.0,
        days_pregnant=None,
        days_in_milk=None,
        parity=0,
        target_adg=0.80,
        mud_condition="none",
        temperature_c=20.0,
        ne_diet_concentration=1.0,
        process_based_phosphorus_requirement=0.0,
    )
    with pytest.raises(NotImplementedError, match="BeefStockerRequirementsCalculator"):
        BeefCowCalfRequirementsCalculator.calculate_requirements(inputs)


@pytest.mark.unit
def test_beef_cow_calf_calc_raises_not_implemented_for_stocker_heifer() -> None:
    """BeefCowCalfRequirementsCalculator must raise NotImplementedError for BEEF_STOCKER_HEIFER."""
    inputs = CowCalfRequirementsInputs(
        body_weight=260.0,
        mature_body_weight=520.0,
        animal_type=AnimalType.BEEF_STOCKER_HEIFER,
        breed="Angus",
        sex=Sex.FEMALE,
        body_condition_score=5.0,
        days_pregnant=None,
        days_in_milk=None,
        parity=0,
        target_adg=0.80,
        mud_condition="none",
        temperature_c=20.0,
        ne_diet_concentration=1.0,
        process_based_phosphorus_requirement=0.0,
    )
    with pytest.raises(NotImplementedError, match="BeefStockerRequirementsCalculator"):
        BeefCowCalfRequirementsCalculator.calculate_requirements(inputs)
