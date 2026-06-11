"""Tests for feedlot herd and pen infrastructure."""

import pytest
from pytest_mock import MockerFixture
from RUFAS.biophysical.animal.data_types.animal_combination import AnimalCombination
from RUFAS.biophysical.animal.data_types.animal_types import AnimalType


def _make_minimal_pen(mocker: MockerFixture) -> "Pen":  # type: ignore[name-defined]  # noqa: F821
    """Build a minimal feedlot Pen, patching bedding init to avoid InputManager dependency."""
    from RUFAS.biophysical.animal.pen import Pen

    mocker.patch.object(Pen, "_initialize_beddings")
    return Pen(
        pen_id=10,
        pen_name="Feedlot Pen A",
        vertical_dist_to_milking_parlor=0.0,
        horizontal_dist_to_milking_parlor=0.0,
        number_of_stalls=100,
        housing_type="Open_Lot",
        pen_type="open_lot",
        animal_combination=AnimalCombination.FEEDLOT_FINISHING,
        max_stocking_density=1.0,
        minutes_away_for_milking=0,
        first_parlor_processor=None,
        parlor_stream_name=None,
        manure_streams=[],
    )


@pytest.mark.unit
def test_pen_has_mud_condition_attribute(mocker: MockerFixture) -> None:
    """Pen must expose a mud_condition attribute."""
    pen = _make_minimal_pen(mocker)
    assert hasattr(pen, "mud_condition")


@pytest.mark.unit
def test_pen_mud_condition_defaults_to_none(mocker: MockerFixture) -> None:
    """Pen.mud_condition must default to 'none' when not specified."""
    pen = _make_minimal_pen(mocker)
    assert pen.mud_condition == "none"


@pytest.mark.unit
def test_herd_manager_feedlot_animals_in_animals_by_type() -> None:
    """animals_by_type must include FEEDLOT_STEER and FEEDLOT_HEIFER keys."""
    from RUFAS.biophysical.animal.herd_manager import HerdManager

    hm: HerdManager = HerdManager.__new__(HerdManager)
    hm.calves = []
    hm.heiferIs = []
    hm.heiferIIs = []
    hm.heiferIIIs = []
    hm.cows = []
    hm.feedlot_animals = []

    result = hm.animals_by_type
    assert AnimalType.FEEDLOT_STEER in result
    assert AnimalType.FEEDLOT_HEIFER in result


@pytest.mark.unit
def test_herd_manager_feedlot_animals_maps_to_same_list() -> None:
    """FEEDLOT_STEER and FEEDLOT_HEIFER must both map to the same feedlot_animals list."""
    from RUFAS.biophysical.animal.herd_manager import HerdManager

    hm: HerdManager = HerdManager.__new__(HerdManager)
    hm.calves = []
    hm.heiferIs = []
    hm.heiferIIs = []
    hm.heiferIIIs = []
    hm.cows = []
    hm.feedlot_animals = []

    result = hm.animals_by_type
    assert result[AnimalType.FEEDLOT_STEER] is hm.feedlot_animals
    assert result[AnimalType.FEEDLOT_HEIFER] is hm.feedlot_animals


@pytest.mark.unit
def test_reporter_report_feedlot_performance_is_callable() -> None:
    """AnimalModuleReporter must expose a callable report_feedlot_performance classmethod."""
    from RUFAS.biophysical.animal.animal_module_reporter import AnimalModuleReporter

    assert hasattr(AnimalModuleReporter, "report_feedlot_performance")
    assert callable(AnimalModuleReporter.report_feedlot_performance)
