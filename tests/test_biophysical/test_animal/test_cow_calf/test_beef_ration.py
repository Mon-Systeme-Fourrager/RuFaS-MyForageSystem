"""Tests for Step 6 — beef ration registration, seasonal selection, optimizer constraints (PR-C).

RED tests must FAIL before Step 6 is implemented and PASS (GREEN) after.
"""

from __future__ import annotations

import types
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from RUFAS.biophysical.animal.data_types.animal_combination import AnimalCombination
from RUFAS.biophysical.animal.data_types.animal_types import AnimalType
from RUFAS.biophysical.animal.ration.ration_manager import RationManager
from RUFAS.biophysical.animal.ration.ration_optimizer import RationOptimizer

# ── helpers ──────────────────────────────────────────────────────────────────


VALID_RATION_CONFIG: dict[str, object] = {
    "rations": [],
    "beef_lactating_pasture_ration": {"301": 60.0, "302": 40.0},
    "beef_dry_gestating_ration": {"303": 100.0},
    "beef_creep_feed_ration": {"304": 100.0},
    "beef_replacement_heifer_ration": {"305": 100.0},
}

SENTINEL_LACTATING: dict[int, float] = {999: 50.0, 998: 50.0}
SENTINEL_DRY: dict[int, float] = {997: 100.0}
SENTINEL_CREEP: dict[int, float] = {996: 100.0}
SENTINEL_HEIFER: dict[int, float] = {995: 100.0}


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def restore_ration_manager_beef_state() -> Generator[None, None, None]:
    """Snapshot and restore all four beef ration ClassVars after each test (Lesson 5)."""
    original_attrs = {
        name: value
        for name, value in RationManager.__dict__.items()
        if not name.startswith("__") and not isinstance(value, (types.FunctionType, classmethod, staticmethod))
    }
    original_names = set(original_attrs.keys())
    yield
    for name in list(RationManager.__dict__.keys()):
        if name.startswith("__"):
            continue
        if isinstance(RationManager.__dict__[name], (types.FunctionType, classmethod, staticmethod)):
            continue
        if name not in original_names:
            try:
                delattr(RationManager, name)
            except AttributeError:
                pass
    for name, value in original_attrs.items():
        setattr(RationManager, name, value)


def _make_minimal_ration_optimizer() -> RationOptimizer:
    """Build a RationOptimizer with stub constraints set."""
    optimizer = RationOptimizer()
    mock_ration_config = MagicMock()
    mock_ration_config.nutrient_standard.__eq__ = lambda self, other: False
    mock_ration_config.nutrient_standard.__is__ = lambda self, other: False
    from RUFAS.data_structures.feed_storage_to_animal_connection import NutrientStandard

    mock_ration_config.nutrient_standard = NutrientStandard.NRC
    optimizer.set_constraints(mock_ration_config)
    return optimizer


# ── Task 6.1: Register four beef rations ──────────────────────────────────────


def test_set_ration_feeds_registers_beef_rations() -> None:
    """Happy path: all four beef rations are stored on the class after set_ration_feeds."""
    RationManager.set_ration_feeds(VALID_RATION_CONFIG)  # type: ignore[arg-type]

    assert RationManager.beef_lactating_pasture_ration == {301: 60.0, 302: 40.0}
    assert RationManager.beef_dry_gestating_ration == {303: 100.0}
    assert RationManager.beef_creep_feed_ration == {304: 100.0}
    assert RationManager.beef_replacement_heifer_ration == {305: 100.0}


@pytest.mark.parametrize(
    "ration_key",
    [
        "beef_lactating_pasture_ration",
        "beef_dry_gestating_ration",
        "beef_creep_feed_ration",
        "beef_replacement_heifer_ration",
    ],
)
def test_set_ration_feeds_rejects_negative_percentage(ration_key: str) -> None:
    """set_ration_feeds raises ValueError when any beef ration percentage is negative."""
    config: dict[str, object] = {
        "rations": [],
        "beef_lactating_pasture_ration": {"301": 100.0},
        "beef_dry_gestating_ration": {"302": 100.0},
        "beef_creep_feed_ration": {"303": 100.0},
        "beef_replacement_heifer_ration": {"304": 100.0},
    }
    config[ration_key] = {"301": -5.0, "302": 105.0}

    with pytest.raises(ValueError, match="non-negative"):
        RationManager.set_ration_feeds(config)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "ration_key",
    [
        "beef_lactating_pasture_ration",
        "beef_dry_gestating_ration",
        "beef_creep_feed_ration",
        "beef_replacement_heifer_ration",
    ],
)
def test_set_ration_feeds_rejects_bad_sum(ration_key: str) -> None:
    """set_ration_feeds raises ValueError when a beef ration does not sum to 100%."""
    config: dict[str, object] = {
        "rations": [],
        "beef_lactating_pasture_ration": {"301": 100.0},
        "beef_dry_gestating_ration": {"302": 100.0},
        "beef_creep_feed_ration": {"303": 100.0},
        "beef_replacement_heifer_ration": {"304": 100.0},
    }
    config[ration_key] = {"301": 60.0, "302": 20.0}  # sums to 80, not 100

    with pytest.raises(ValueError, match="100"):
        RationManager.set_ration_feeds(config)  # type: ignore[arg-type]


def test_set_ration_feeds_allows_empty_creep_feed() -> None:
    """An empty creep feed ration ({}) is valid and skips validation."""
    config: dict[str, object] = {
        "rations": [],
        "beef_lactating_pasture_ration": {"301": 100.0},
        "beef_dry_gestating_ration": {"302": 100.0},
        "beef_creep_feed_ration": {},
        "beef_replacement_heifer_ration": {"304": 100.0},
    }
    RationManager.set_ration_feeds(config)  # type: ignore[arg-type]
    assert RationManager.beef_creep_feed_ration == {}


def test_set_ration_feeds_is_atomic() -> None:
    """If any beef ration is invalid, no class attribute is modified (atomic commit)."""
    RationManager.beef_lactating_pasture_ration = SENTINEL_LACTATING
    RationManager.beef_dry_gestating_ration = SENTINEL_DRY
    RationManager.beef_creep_feed_ration = SENTINEL_CREEP
    RationManager.beef_replacement_heifer_ration = SENTINEL_HEIFER

    bad_config: dict[str, object] = {
        "rations": [],
        "beef_lactating_pasture_ration": {"301": 60.0, "302": 20.0},  # sums to 80
        "beef_dry_gestating_ration": {"302": 100.0},
        "beef_creep_feed_ration": {"303": 100.0},
        "beef_replacement_heifer_ration": {"304": 100.0},
    }

    with pytest.raises(ValueError):
        RationManager.set_ration_feeds(bad_config)  # type: ignore[arg-type]

    assert RationManager.beef_lactating_pasture_ration is SENTINEL_LACTATING
    assert RationManager.beef_dry_gestating_ration is SENTINEL_DRY
    assert RationManager.beef_creep_feed_ration is SENTINEL_CREEP
    assert RationManager.beef_replacement_heifer_ration is SENTINEL_HEIFER


# ── Task 6.2: Seasonal ration selection ───────────────────────────────────────


@pytest.fixture()
def mock_animal_lactating_cow() -> MagicMock:
    """Mock Animal: BEEF_COW with calf at side (lactating)."""
    animal = MagicMock()
    animal.animal_type = AnimalType.BEEF_COW
    animal.calf_at_side = MagicMock()
    return animal


@pytest.fixture()
def mock_animal_dry_cow() -> MagicMock:
    """Mock Animal: BEEF_COW without calf at side (dry/gestating)."""
    animal = MagicMock()
    animal.animal_type = AnimalType.BEEF_COW
    animal.calf_at_side = None
    return animal


@pytest.fixture()
def mock_animal_replacement_heifer() -> MagicMock:
    """Mock Animal: BEEF_HEIFER_REPLACEMENT."""
    animal = MagicMock()
    animal.animal_type = AnimalType.BEEF_HEIFER_REPLACEMENT
    animal.calf_at_side = None
    return animal


@pytest.fixture()
def mock_animal_bull() -> MagicMock:
    """Mock Animal: BEEF_BULL."""
    animal = MagicMock()
    animal.animal_type = AnimalType.BEEF_BULL
    animal.calf_at_side = None
    return animal


def test_get_beef_seasonal_ration_lactating_cow(mock_animal_lactating_cow: MagicMock) -> None:
    """A BEEF_COW with calf_at_side returns the beef_lactating_pasture_ration."""
    RationManager.beef_lactating_pasture_ration = SENTINEL_LACTATING
    RationManager.beef_dry_gestating_ration = SENTINEL_DRY

    result = RationManager.get_beef_seasonal_ration(mock_animal_lactating_cow)

    assert result is SENTINEL_LACTATING


def test_get_beef_seasonal_ration_dry_cow(mock_animal_dry_cow: MagicMock) -> None:
    """A BEEF_COW without calf_at_side returns the beef_dry_gestating_ration."""
    RationManager.beef_lactating_pasture_ration = SENTINEL_LACTATING
    RationManager.beef_dry_gestating_ration = SENTINEL_DRY

    result = RationManager.get_beef_seasonal_ration(mock_animal_dry_cow)

    assert result is SENTINEL_DRY


def test_get_beef_seasonal_ration_replacement_heifer(mock_animal_replacement_heifer: MagicMock) -> None:
    """A BEEF_HEIFER_REPLACEMENT returns the beef_replacement_heifer_ration."""
    RationManager.beef_replacement_heifer_ration = SENTINEL_HEIFER

    result = RationManager.get_beef_seasonal_ration(mock_animal_replacement_heifer)

    assert result is SENTINEL_HEIFER


def test_get_beef_seasonal_ration_bull(mock_animal_bull: MagicMock) -> None:
    """A BEEF_BULL returns the beef_dry_gestating_ration (same as non-lactating cows)."""
    RationManager.beef_dry_gestating_ration = SENTINEL_DRY

    result = RationManager.get_beef_seasonal_ration(mock_animal_bull)

    assert result is SENTINEL_DRY


def test_get_beef_creep_feed_supplement_disabled(mock_animal_lactating_cow: MagicMock) -> None:
    """Returns {} when beef_creep_feeding_enabled is False."""
    from RUFAS.biophysical.animal.animal_config import AnimalConfig

    AnimalConfig.beef_creep_feeding_enabled = False
    RationManager.beef_creep_feed_ration = SENTINEL_CREEP

    result = RationManager.get_beef_creep_feed_supplement(mock_animal_lactating_cow)

    assert result == {}


def test_get_beef_creep_feed_supplement_enabled(mock_animal_lactating_cow: MagicMock) -> None:
    """Returns beef_creep_feed_ration when beef_creep_feeding_enabled is True."""
    from RUFAS.biophysical.animal.animal_config import AnimalConfig

    AnimalConfig.beef_creep_feeding_enabled = True
    RationManager.beef_creep_feed_ration = SENTINEL_CREEP

    result = RationManager.get_beef_creep_feed_supplement(mock_animal_lactating_cow)

    assert result is SENTINEL_CREEP


# ── Task 6.3: RationOptimizer beef constraint branches ────────────────────────


@pytest.fixture()
def optimizer() -> RationOptimizer:
    """Provide a RationOptimizer with constraints initialized for NRC standard."""
    return _make_minimal_ration_optimizer()


def test_select_constraints_beef_cow_calf_pair(optimizer: RationOptimizer) -> None:
    """_select_constraints returns beef_cow_constraints for BEEF_COW_CALF_PAIR."""
    result = optimizer._select_constraints(AnimalCombination.BEEF_COW_CALF_PAIR)
    assert result is optimizer.beef_cow_constraints


def test_select_constraints_beef_replacement(optimizer: RationOptimizer) -> None:
    """_select_constraints returns beef_replacement_constraints for BEEF_REPLACEMENT."""
    result = optimizer._select_constraints(AnimalCombination.BEEF_REPLACEMENT)
    assert result is optimizer.beef_replacement_constraints


@pytest.mark.parametrize(
    "combination",
    [
        AnimalCombination.BEEF_COW_CALF_PAIR,
        AnimalCombination.BEEF_GESTATING,
        AnimalCombination.BEEF_BULL_BATTERY,
        AnimalCombination.BEEF_REPLACEMENT,
    ],
)
def test_handle_failed_constraints_agrees_with_select_constraints(
    optimizer: RationOptimizer,
    combination: AnimalCombination,
    mocker: MockerFixture,
) -> None:
    """handle_failed_constraints uses the same constraint set as _select_constraints for beef combinations."""
    expected_constraints = optimizer._select_constraints(combination)

    mock_find = mocker.patch.object(RationOptimizer, "find_failed_constraints", return_value=[])
    mock_solution = MagicMock()
    mock_ration_config = MagicMock()
    mock_available_feeds: list[object] = []
    mock_requirements = MagicMock()

    optimizer.handle_failed_constraints(
        num_attempts=1,
        solution=mock_solution,
        ration_config=mock_ration_config,
        animal_combination=combination,
        pen_id=1,
        pen_available_feeds=mock_available_feeds,
        average_nutrient_requirements=mock_requirements,
        initial_dry_matter_requirement=10.0,
        initial_protein_requirement=1.0,
        sim_day=1,
    )

    mock_find.assert_called_once()
    _, constraints_used, _ = mock_find.call_args.args
    assert constraints_used is expected_constraints
