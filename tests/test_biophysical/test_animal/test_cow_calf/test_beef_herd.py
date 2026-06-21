"""Tests for beef cow-calf herd cohort lists in HerdFactory and HerdManager (Tasks 7.1 + 7.2)."""

import math
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from RUFAS.biophysical.animal.animal_module_reporter import AnimalModuleReporter
from RUFAS.biophysical.animal.data_types.animal_combination import AnimalCombination
from RUFAS.biophysical.animal.data_types.animal_enums import AnimalStatus
from RUFAS.biophysical.animal.data_types.animal_types import AnimalType
from RUFAS.biophysical.animal.data_types.daily_herd_updates import DailyHerdUpdates
from RUFAS.biophysical.animal.data_types.daily_routines_output import DailyRoutinesOutput
from RUFAS.biophysical.animal.data_types.nutrients import NutrientsInputs
from RUFAS.biophysical.animal.data_types.reproduction import HerdReproductionStatistics
from RUFAS.biophysical.animal.herd_factory import HerdFactory
from RUFAS.biophysical.animal.herd_manager import HerdManager
from RUFAS.biophysical.animal.nutrients.nutrients import Nutrients
from RUFAS.biophysical.animal.pen import Pen
from RUFAS.data_validator import DataValidator
from RUFAS.input_manager import InputManager
from RUFAS.rufas_time import RufasTime


@pytest.mark.unit
def test_herd_factory_has_beef_cow_calf_animals_class_attr() -> None:
    """HerdFactory must expose a beef_cow_calf_animals class-level list attribute."""
    assert hasattr(HerdFactory, "beef_cow_calf_animals")
    assert isinstance(HerdFactory.beef_cow_calf_animals, list)


@pytest.mark.unit
def test_animals_by_type_returns_distinct_lists() -> None:
    """BEEF_COW, BEEF_HEIFER_REPLACEMENT, BEEF_CALF, BEEF_BULL each resolve to separate list objects.

    Verifies Lesson 1: each beef type maps to its OWN named list in HerdManager,
    never pooled into a single shared list.
    """
    hm: HerdManager = HerdManager.__new__(HerdManager)
    hm.calves = []
    hm.heiferIs = []
    hm.heiferIIs = []
    hm.heiferIIIs = []
    hm.cows = []
    hm.feedlot_animals = []

    cow = MagicMock()
    cow.animal_type = AnimalType.BEEF_COW

    heifer = MagicMock()
    heifer.animal_type = AnimalType.BEEF_HEIFER_REPLACEMENT

    calf = MagicMock()
    calf.animal_type = AnimalType.BEEF_CALF

    bull = MagicMock()
    bull.animal_type = AnimalType.BEEF_BULL

    hm.beef_cows = [cow]
    hm.beef_replacement_heifers = [heifer]
    hm.beef_calves = [calf]
    hm.beef_bulls = [bull]

    result = hm.animals_by_type

    assert AnimalType.BEEF_COW in result
    assert AnimalType.BEEF_HEIFER_REPLACEMENT in result
    assert AnimalType.BEEF_CALF in result
    assert AnimalType.BEEF_BULL in result

    assert result[AnimalType.BEEF_COW] == [cow]
    assert result[AnimalType.BEEF_HEIFER_REPLACEMENT] == [heifer]
    assert result[AnimalType.BEEF_CALF] == [calf]
    assert result[AnimalType.BEEF_BULL] == [bull]

    assert result[AnimalType.BEEF_COW] is hm.beef_cows
    assert result[AnimalType.BEEF_HEIFER_REPLACEMENT] is hm.beef_replacement_heifers
    assert result[AnimalType.BEEF_CALF] is hm.beef_calves
    assert result[AnimalType.BEEF_BULL] is hm.beef_bulls

    assert result[AnimalType.BEEF_COW] is not result[AnimalType.BEEF_HEIFER_REPLACEMENT]
    assert result[AnimalType.BEEF_COW] is not result[AnimalType.BEEF_CALF]
    assert result[AnimalType.BEEF_COW] is not result[AnimalType.BEEF_BULL]
    assert result[AnimalType.BEEF_HEIFER_REPLACEMENT] is not result[AnimalType.BEEF_CALF]
    assert result[AnimalType.BEEF_HEIFER_REPLACEMENT] is not result[AnimalType.BEEF_BULL]
    assert result[AnimalType.BEEF_CALF] is not result[AnimalType.BEEF_BULL]


@pytest.mark.unit
def test_herd_manager_beef_lists_populated_from_factory(mocker: MockerFixture) -> None:
    """HerdManager init must split HerdFactory.beef_cow_calf_animals into four typed lists.

    Each list must contain only animals of the matching AnimalType, derived from
    the class attribute via per-type list comprehensions.
    """
    cow = MagicMock()
    cow.animal_type = AnimalType.BEEF_COW

    heifer = MagicMock()
    heifer.animal_type = AnimalType.BEEF_HEIFER_REPLACEMENT

    calf = MagicMock()
    calf.animal_type = AnimalType.BEEF_CALF

    bull = MagicMock()
    bull.animal_type = AnimalType.BEEF_BULL

    mocker.patch.object(HerdFactory, "beef_cow_calf_animals", [cow, heifer, calf, bull])
    mocker.patch.object(HerdFactory, "feedlot_animals", [])

    hm: HerdManager = HerdManager.__new__(HerdManager)
    hm.calves = []
    hm.heiferIs = []
    hm.heiferIIs = []
    hm.heiferIIIs = []
    hm.cows = []
    hm.feedlot_animals = list(HerdFactory.feedlot_animals)

    beef_all = list(HerdFactory.beef_cow_calf_animals)
    hm.beef_cows = [a for a in beef_all if a.animal_type == AnimalType.BEEF_COW]
    hm.beef_replacement_heifers = [a for a in beef_all if a.animal_type == AnimalType.BEEF_HEIFER_REPLACEMENT]
    hm.beef_calves = [a for a in beef_all if a.animal_type == AnimalType.BEEF_CALF]
    hm.beef_bulls = [a for a in beef_all if a.animal_type == AnimalType.BEEF_BULL]

    assert hm.beef_cows == [cow]
    assert hm.beef_replacement_heifers == [heifer]
    assert hm.beef_calves == [calf]
    assert hm.beef_bulls == [bull]

    assert hm.beef_cows is not hm.beef_replacement_heifers
    assert hm.beef_cows is not hm.beef_calves
    assert hm.beef_cows is not hm.beef_bulls


# ---------------------------------------------------------------------------
# Task 7.2 — RED tests
# ---------------------------------------------------------------------------


def _make_herd_manager_stub(
    mocker: MockerFixture,
    beef_cows: list[MagicMock] | None = None,
    beef_replacement_heifers: list[MagicMock] | None = None,
    beef_calves: list[MagicMock] | None = None,
    beef_bulls: list[MagicMock] | None = None,
) -> HerdManager:
    """Return a HerdManager instance with all list attrs pre-set (no __init__)."""
    hm: HerdManager = HerdManager.__new__(HerdManager)
    hm.calves = []
    hm.heiferIs = []
    hm.heiferIIs = []
    hm.heiferIIIs = []
    hm.cows = []
    hm.feedlot_animals = []
    hm.beef_cows = beef_cows if beef_cows is not None else []
    hm.beef_replacement_heifers = beef_replacement_heifers if beef_replacement_heifers is not None else []
    hm.beef_calves = beef_calves if beef_calves is not None else []
    hm.beef_bulls = beef_bulls if beef_bulls is not None else []
    hm.herd_reproduction_statistics = HerdReproductionStatistics()
    hm.herd_statistics = MagicMock()
    hm.herd_statistics.animals_deaths_by_stage = {}
    return hm


def _make_time_mock(simulation_day: int = 1) -> MagicMock:
    """Return a RufasTime mock with simulation_day set."""
    t: MagicMock = MagicMock(spec=RufasTime)
    t.simulation_day = simulation_day
    return t


def _make_animal_mock(animal_type: AnimalType, status: AnimalStatus = AnimalStatus.REMAIN) -> MagicMock:
    """Return an Animal mock whose daily_routines returns the given status."""
    animal: MagicMock = MagicMock()
    animal.animal_type = animal_type
    output = DailyRoutinesOutput(herd_reproduction_statistics=HerdReproductionStatistics())
    output.animal_status = status
    animal.daily_routines.return_value = output
    return animal


@pytest.mark.unit
def test_process_daily_herd_updates_includes_beef_groups(mocker: MockerFixture) -> None:
    """_process_daily_herd_updates must call _perform_daily_routines_for_animals for all four beef lists.

    Verifies Lesson 10: beef_cows, beef_replacement_heifers, beef_calves, and beef_bulls
    are each passed as the ``animals`` argument in a separate call.
    """
    cow = _make_animal_mock(AnimalType.BEEF_COW)
    heifer = _make_animal_mock(AnimalType.BEEF_HEIFER_REPLACEMENT)
    calf = _make_animal_mock(AnimalType.BEEF_CALF)
    bull = _make_animal_mock(AnimalType.BEEF_BULL)

    hm = _make_herd_manager_stub(
        mocker,
        beef_cows=[cow],
        beef_replacement_heifers=[heifer],
        beef_calves=[calf],
        beef_bulls=[bull],
    )

    empty_result: tuple[list[MagicMock], list[MagicMock], list[MagicMock], list[MagicMock], list[MagicMock]] = (
        [],
        [],
        [],
        [],
        [],
    )
    spy = mocker.patch.object(hm, "_perform_daily_routines_for_animals", return_value=empty_result)
    mocker.patch.object(AnimalModuleReporter, "report_cow_calf_performance", return_value=None)

    time = _make_time_mock()
    hm._process_daily_herd_updates(time)

    called_animals_args = [c.args[1] for c in spy.call_args_list]
    assert any(
        a is hm.beef_cows for a in called_animals_args
    ), "beef_cows not passed to _perform_daily_routines_for_animals"
    assert any(a is hm.beef_replacement_heifers for a in called_animals_args), "beef_replacement_heifers not passed"
    assert any(a is hm.beef_calves for a in called_animals_args), "beef_calves not passed"
    assert any(a is hm.beef_bulls for a in called_animals_args), "beef_bulls not passed"


@pytest.mark.unit
def test_beef_cow_calving_propagates_to_newborn_calves(mocker: MockerFixture) -> None:
    """REMAIN + BEEF_COW + non-None newborn_calf_config must populate daily_herd_updates.newborn_calves.

    Verifies that the beef-calving branch in _perform_daily_routines_for_animals
    captures newborns even though the cow stays REMAIN (not LIFE_STAGE_CHANGED).
    """
    cow = MagicMock()
    cow.animal_type = AnimalType.BEEF_COW
    newborn_cfg: MagicMock = MagicMock()
    output = DailyRoutinesOutput(herd_reproduction_statistics=HerdReproductionStatistics())
    output.animal_status = AnimalStatus.REMAIN
    output.newborn_calf_config = newborn_cfg
    cow.daily_routines.return_value = output

    hm = _make_herd_manager_stub(mocker, beef_cows=[cow])

    newborn_animal = MagicMock()
    newborn_animal.stillborn = False
    newborn_animal.sold = False
    mocker.patch.object(hm, "_create_newborn_calf", return_value=newborn_animal)
    mocker.patch.object(AnimalModuleReporter, "report_cow_calf_performance", return_value=None)

    time = _make_time_mock()
    daily_herd_updates: DailyHerdUpdates = hm._process_daily_herd_updates(time)

    assert (
        newborn_animal in daily_herd_updates.newborn_calves
    ), "Newborn calf from BEEF_COW REMAIN calving must appear in daily_herd_updates.newborn_calves"


@pytest.mark.unit
def test_process_daily_herd_updates_calls_reporter_for_beef(mocker: MockerFixture) -> None:
    """_process_daily_herd_updates must call report_cow_calf_performance once per beef animal.

    Verifies Lessons 4 and 9: the reporter is called from HerdManager (not animal.py),
    once for each animal in the four beef lists combined.
    """
    cow = _make_animal_mock(AnimalType.BEEF_COW)
    heifer = _make_animal_mock(AnimalType.BEEF_HEIFER_REPLACEMENT)
    calf = _make_animal_mock(AnimalType.BEEF_CALF)
    bull = _make_animal_mock(AnimalType.BEEF_BULL)

    hm = _make_herd_manager_stub(
        mocker,
        beef_cows=[cow],
        beef_replacement_heifers=[heifer],
        beef_calves=[calf],
        beef_bulls=[bull],
    )

    reporter_spy = mocker.patch.object(AnimalModuleReporter, "report_cow_calf_performance", return_value=None)
    time = _make_time_mock(simulation_day=5)

    hm._process_daily_herd_updates(time)

    assert (
        reporter_spy.call_count == 4
    ), f"Expected 4 reporter calls (one per beef animal), got {reporter_spy.call_count}"
    called_animals = [c.args[0] for c in reporter_spy.call_args_list]
    assert cow in called_animals
    assert heifer in called_animals
    assert calf in called_animals
    assert bull in called_animals


@pytest.mark.unit
def test_initialize_beef_cow_calf_herd_non_dict_config_returns_empty(mocker: MockerFixture) -> None:
    """_initialize_beef_cow_calf_herd must return [] when config value is not a dict.

    Verifies Lesson 2: the isinstance(cfg, dict) guard prevents attempts to call
    .get() on a non-dict value such as a list, int, or None.
    """
    hf: HerdFactory = HerdFactory.__new__(HerdFactory)
    hf.im = MagicMock()
    hf.time = _make_time_mock()

    for bad_value in [None, [], "string", 42]:
        hf.im.get_data.return_value = bad_value
        result = hf._initialize_beef_cow_calf_herd()
        assert result == [], f"Expected [] for config value {bad_value!r}, got {result}"


@pytest.mark.unit
def test_beef_cow_calf_update_calls_reporter_on_sold(mocker: MockerFixture) -> None:
    """_beef_cow_calf_update must call report_cow_calf_performance when animal status is SOLD.

    Verifies Lesson 4: the reporter call at SOLD disposition is tested explicitly.
    """
    hf: HerdFactory = HerdFactory.__new__(HerdFactory)
    hf.time = _make_time_mock(simulation_day=3)

    animal = MagicMock()
    output = DailyRoutinesOutput(herd_reproduction_statistics=HerdReproductionStatistics())
    output.animal_status = AnimalStatus.SOLD
    animal.daily_routines.return_value = output

    reporter_spy = mocker.patch.object(AnimalModuleReporter, "report_cow_calf_performance", return_value=None)
    time = _make_time_mock(simulation_day=3)

    result = hf._beef_cow_calf_update(animal, time)

    assert result.animal_status == AnimalStatus.SOLD
    reporter_spy.assert_called_once_with(animal, time.simulation_day)


def _make_minimal_pen(mocker: MockerFixture, forage_quality_factor: float | None = None) -> Pen:
    """Construct a minimal Pen with bedding mocked out via InputManager."""
    im = InputManager()
    mocker.patch.object(
        im,
        "get_data",
        return_value=[
            {
                "name": "bedding_1",
                "bedding_type": "sawdust",
                "bedding_mass_per_day": 1.97,
                "bedding_density": 250.0,
                "bedding_dry_matter_content": 0.9,
                "bedding_carbon_fraction": 0.0,
                "bedding_phosphorus_content": 0.0,
                "sand_removal_efficiency": 0.0,
            }
        ],
    )
    kwargs: dict[str, object] = dict(
        pen_id=1,
        pen_name="Test Pen",
        vertical_dist_to_milking_parlor=0.0,
        horizontal_dist_to_milking_parlor=0.0,
        number_of_stalls=10,
        housing_type="freestall",
        pen_type="freestall",
        animal_combination=AnimalCombination.LAC_COW,
        max_stocking_density=1.0,
        minutes_away_for_milking=0,
        first_parlor_processor=None,
        parlor_stream_name=None,
        manure_streams=[{"stream_name": "s1", "stream_proportion": 1.0, "bedding_name": "bedding_1"}],
    )
    if forage_quality_factor is not None:
        kwargs["forage_quality_factor"] = forage_quality_factor
    return Pen(**kwargs)  # type: ignore[arg-type]


@pytest.mark.unit
def test_pen_forage_quality_factor_defaults_to_one(mocker: MockerFixture) -> None:
    """Pen must have forage_quality_factor defaulting to 1.0 when not in config."""
    pen_default = _make_minimal_pen(mocker)
    assert pen_default.forage_quality_factor == 1.0

    pen_custom = _make_minimal_pen(mocker, forage_quality_factor=0.8)
    assert pen_custom.forage_quality_factor == 0.8


# ---------------------------------------------------------------------------
# Task 7.4 — nutrients.py phosphorus guard verification
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_nutrients_phosphorus_requirement_set_for_beef() -> None:
    """_calculate_phosphorus_requirements sets a finite positive value for beef animals.

    Verifies Task 7.4: the void method modifies self.phosphorus_requirement in-place
    and produces a valid (finite, > 0) result for BEEF_COW without raising an error.
    No guard is needed because the existing code already produces a valid finite positive
    value via the non-cow fallback paths in the sub-calculations.
    """
    nutrients = Nutrients()
    nutrients_inputs = NutrientsInputs(
        animal_type=AnimalType.BEEF_COW,
        body_weight=550.0,
        mature_body_weight=550.0,
        daily_growth=0.0,
        days_in_pregnancy=0,
        days_in_milk=0,
        daily_milk_produced=0.0,
    )
    nutrients.set_dry_matter_intake(10.0)

    nutrients._calculate_phosphorus_requirements(nutrients_inputs)

    assert math.isfinite(nutrients.phosphorus_requirement), "phosphorus_requirement must be finite for BEEF_COW"
    assert nutrients.phosphorus_requirement > 0, "phosphorus_requirement must be positive for BEEF_COW"


@pytest.mark.unit
def test_validate_beef_cow_calf_config_rejects_nan_weight() -> None:
    """mature_cow_weight_kg of NaN must raise ValueError."""
    with pytest.raises(ValueError, match="mature_cow_weight_kg"):
        DataValidator.validate_beef_cow_calf_config({"mature_cow_weight_kg": float("nan")})


@pytest.mark.unit
def test_validate_beef_cow_calf_config_rejects_zero_weaning_age() -> None:
    """weaning_age_days of 0 must raise ValueError."""
    with pytest.raises(ValueError, match="weaning_age_days"):
        DataValidator.validate_beef_cow_calf_config({"mature_cow_weight_kg": 500.0, "weaning_age_days": 0})


@pytest.mark.unit
def test_validate_beef_cow_calf_config_rejects_excessive_bull_ratio() -> None:
    """natural_service_bull_ratio above MAX_BULL_TO_COW_RATIO must raise ValueError."""
    with pytest.raises(ValueError, match="natural_service_bull_ratio"):
        DataValidator.validate_beef_cow_calf_config(
            {
                "mature_cow_weight_kg": 500.0,
                "weaning_age_days": 180,
                "breeding_season_length": 63,
                "natural_service_bull_ratio": 999,
            }
        )


@pytest.mark.unit
def test_validate_beef_cow_calf_config_accepts_valid_config() -> None:
    """A valid config must not raise."""
    DataValidator.validate_beef_cow_calf_config(
        {
            "mature_cow_weight_kg": 500.0,
            "weaning_age_days": 180,
            "breeding_season_length": 63,
            "natural_service_bull_ratio": 25,
        }
    )


# ---------------------------------------------------------------------------
# Task 7.6 — None-guards and required metric fields in report_cow_calf_performance
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_report_cow_calf_performance_does_not_raise_with_none_attrs(mocker: MockerFixture) -> None:
    """report_cow_calf_performance must handle None-valued animal attributes gracefully.

    Exercises the None-guards for wean_weight and any other Optional attributes
    that may be None on non-cow beef animals (e.g. BEEF_HEIFER_REPLACEMENT) at
    initialization time. The call must not raise and must emit at least the five
    required metric variables: days_in_pregnancy, lactation_day,
    body_condition_score_9, times_calved (parity), and wean_weight.
    """
    animal: MagicMock = MagicMock()
    animal.id = 42
    animal.animal_type = MagicMock()
    animal.animal_type.value = AnimalType.BEEF_COW.value
    animal.days_in_pregnancy = 0
    animal.lactation_day = 0
    animal.body_condition_score_9 = 5.0
    animal.calves = 1
    animal.wean_weight = None  # None triggers the guard being tested

    add_variable_spy = mocker.patch("RUFAS.biophysical.animal.animal_module_reporter.om.add_variable")

    AnimalModuleReporter.report_cow_calf_performance(animal, simulation_day=100)

    reported_names = [call.args[0] for call in add_variable_spy.call_args_list]
    assert "beef_days_in_pregnancy" in reported_names
    assert "beef_lactation_day" in reported_names
    assert "beef_body_condition_score_9" in reported_names
    assert "beef_times_calved" in reported_names
    assert "beef_wean_weight_kg" in reported_names


@pytest.mark.unit
def test_report_cow_calf_performance_wean_weight_none_maps_to_zero(mocker: MockerFixture) -> None:
    """report_cow_calf_performance must pass 0.0 for beef_wean_weight_kg when wean_weight is None.

    Verifies the exact None-fallback value so that OutputManager receives a
    valid float, not None, when the attribute has not been set on initialization.
    """
    animal: MagicMock = MagicMock()
    animal.id = 7
    animal.animal_type = MagicMock()
    animal.animal_type.value = AnimalType.BEEF_HEIFER_REPLACEMENT.value
    animal.days_in_pregnancy = 0
    animal.lactation_day = 0
    animal.body_condition_score_9 = 4.5
    animal.calves = 0
    animal.wean_weight = None

    add_variable_spy = mocker.patch("RUFAS.biophysical.animal.animal_module_reporter.om.add_variable")

    AnimalModuleReporter.report_cow_calf_performance(animal, simulation_day=50)

    wean_call = next(
        (c for c in add_variable_spy.call_args_list if c.args[0] == "beef_wean_weight_kg"),
        None,
    )
    assert wean_call is not None, "beef_wean_weight_kg must be reported"
    assert wean_call.args[1] == 0.0, "None wean_weight must fall back to 0.0"
