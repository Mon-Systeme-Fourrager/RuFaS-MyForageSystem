"""Tests for feedlot lifecycle in the Animal class."""

import pytest
from unittest.mock import MagicMock
from pytest_mock import MockerFixture
from RUFAS.biophysical.animal.animal import Animal
from RUFAS.biophysical.animal.data_types.animal_types import AnimalType
from RUFAS.biophysical.animal.data_types.animal_enums import AnimalStatus
from RUFAS.biophysical.animal.data_types.animal_events import AnimalEvents
from RUFAS.biophysical.animal.animal_module_constants import AnimalModuleConstants


def _make_feedlot_animal(
    animal_type: AnimalType = AnimalType.FEEDLOT_STEER,
    body_weight: float = 320.0,
    days_on_feed: int = 0,
) -> Animal:
    """Construct a minimal feedlot animal via __new__ with required attributes set."""

    animal: Animal = Animal.__new__(Animal)
    animal.animal_type = animal_type
    animal.body_weight = body_weight
    animal.days_on_feed = days_on_feed
    animal.days_born = 365 + days_on_feed
    animal.entry_weight = body_weight
    animal.cumulative_dmi = 0.0
    animal.receiving_stress = days_on_feed <= AnimalModuleConstants.RECEIVING_PERIOD_DAYS
    animal.step_up_phase = ""
    animal.events = AnimalEvents()
    animal.sold_at_day = None
    animal.cull_reason = ""
    animal.om = MagicMock()
    return animal


@pytest.mark.unit
def test_feedlot_steer_has_days_on_feed() -> None:
    """FEEDLOT_STEER animal must have an integer days_on_feed attribute."""
    animal = _make_feedlot_animal()
    assert hasattr(animal, "days_on_feed")
    assert isinstance(animal.days_on_feed, int)


@pytest.mark.unit
def test_feedlot_steer_has_step_up_phase() -> None:
    """FEEDLOT_STEER animal must have a step_up_phase string attribute."""
    animal = _make_feedlot_animal()
    assert hasattr(animal, "step_up_phase")
    assert isinstance(animal.step_up_phase, str)


@pytest.mark.unit
def test_feedlot_steer_has_receiving_stress() -> None:
    """FEEDLOT_STEER animal must have a boolean receiving_stress attribute."""
    animal = _make_feedlot_animal()
    assert hasattr(animal, "receiving_stress")
    assert isinstance(animal.receiving_stress, bool)


@pytest.mark.unit
def test_feedlot_steer_has_entry_weight() -> None:
    """FEEDLOT_STEER animal must have an entry_weight float attribute."""
    animal = _make_feedlot_animal(body_weight=320.0)
    assert hasattr(animal, "entry_weight")
    assert isinstance(animal.entry_weight, float)


@pytest.mark.unit
def test_update_step_up_phase_starter_at_day_0() -> None:
    """_update_step_up_phase must set 'starter' when days_on_feed <= STEP_UP_STARTER_END_DAY."""
    animal = _make_feedlot_animal(days_on_feed=0)
    animal._update_step_up_phase()  # type: ignore[attr-defined]
    assert animal.step_up_phase == "starter"


@pytest.mark.unit
def test_update_step_up_phase_starter_at_boundary() -> None:
    """_update_step_up_phase must still be 'starter' on the last starter day (day 7)."""
    animal = _make_feedlot_animal(days_on_feed=AnimalModuleConstants.STEP_UP_STARTER_END_DAY)
    animal._update_step_up_phase()  # type: ignore[attr-defined]
    assert animal.step_up_phase == "starter"


@pytest.mark.unit
def test_update_step_up_phase_transition_at_day_14() -> None:
    """_update_step_up_phase must set 'transition' when 8 <= days_on_feed <= 21."""
    animal = _make_feedlot_animal(days_on_feed=14)
    animal._update_step_up_phase()  # type: ignore[attr-defined]
    assert animal.step_up_phase == "transition"


@pytest.mark.unit
def test_update_step_up_phase_finisher_after_21_days() -> None:
    """_update_step_up_phase must set 'finisher' when days_on_feed > STEP_UP_TRANSITION_END_DAY."""
    animal = _make_feedlot_animal(days_on_feed=30)
    animal._update_step_up_phase()  # type: ignore[attr-defined]
    assert animal.step_up_phase == "finisher"


@pytest.mark.unit
def test_receiving_stress_true_within_receiving_period() -> None:
    """receiving_stress must be True when days_on_feed <= RECEIVING_PERIOD_DAYS."""
    animal = _make_feedlot_animal(days_on_feed=10)
    assert animal.receiving_stress is True


@pytest.mark.unit
def test_receiving_stress_false_after_receiving_period() -> None:
    """receiving_stress must be False when days_on_feed > RECEIVING_PERIOD_DAYS (21)."""
    animal = _make_feedlot_animal(days_on_feed=25)
    assert animal.receiving_stress is False


@pytest.mark.unit
def test_feedlot_life_stage_remain_below_slaughter(mocker: MockerFixture) -> None:
    """_feedlot_life_stage_update must return (REMAIN, None) when below slaughter weight."""
    from RUFAS.biophysical.animal.animal_config import AnimalConfig

    mocker.patch.object(AnimalConfig, "feedlot_slaughter_weight", 580.0)
    mocker.patch.object(AnimalConfig, "feedlot_max_days_on_feed", 220)
    animal = _make_feedlot_animal(body_weight=400.0, days_on_feed=50)
    mock_time = MagicMock()
    mock_time.simulation_day = 50
    status, newborn = animal._feedlot_life_stage_update(mock_time)  # type: ignore[attr-defined]
    assert status == AnimalStatus.REMAIN
    assert newborn is None


@pytest.mark.unit
def test_feedlot_life_stage_sold_at_slaughter_weight(mocker: MockerFixture) -> None:
    """_feedlot_life_stage_update must return SOLD when body_weight >= slaughter_weight."""
    from RUFAS.biophysical.animal.animal_config import AnimalConfig

    mocker.patch.object(AnimalConfig, "feedlot_slaughter_weight", 580.0)
    mocker.patch.object(AnimalConfig, "feedlot_max_days_on_feed", 220)
    animal = _make_feedlot_animal(body_weight=580.0, days_on_feed=180)
    mock_time = MagicMock()
    mock_time.simulation_day = 180
    status, newborn = animal._feedlot_life_stage_update(mock_time)  # type: ignore[attr-defined]
    assert status == AnimalStatus.SOLD
    assert newborn is None
    assert animal.sold_at_day == 180


@pytest.mark.unit
def test_feedlot_life_stage_sold_at_max_days_on_feed(mocker: MockerFixture) -> None:
    """_feedlot_life_stage_update must return SOLD when days_on_feed >= max_days_on_feed."""
    from RUFAS.biophysical.animal.animal_config import AnimalConfig

    mocker.patch.object(AnimalConfig, "feedlot_slaughter_weight", 580.0)
    mocker.patch.object(AnimalConfig, "feedlot_max_days_on_feed", 100)
    animal = _make_feedlot_animal(body_weight=400.0, days_on_feed=100)
    mock_time = MagicMock()
    mock_time.simulation_day = 100
    status, newborn = animal._feedlot_life_stage_update(mock_time)  # type: ignore[attr-defined]
    assert status == AnimalStatus.SOLD
    assert newborn is None
    assert animal.sold_at_day == 100


@pytest.mark.unit
def test_calculate_nutrition_requirements_routes_to_beef_calculator(mocker: MockerFixture) -> None:
    """calculate_nutrition_requirements must call BeefNRCRequirementsCalculator for feedlot."""
    from RUFAS.biophysical.animal.animal import Animal
    from RUFAS.biophysical.animal.data_types.animal_enums import Breed, Sex
    from RUFAS.biophysical.animal.data_types.nutrition_data_structures import NutritionRequirements
    from RUFAS.biophysical.animal.animal_config import AnimalConfig

    mocker.patch.object(AnimalConfig, "feedlot_target_adg", 1.4)
    mocker.patch.object(AnimalConfig, "feedlot_implant_adg_factor", 1.0)
    mocker.patch.object(AnimalConfig, "feedlot_mud_condition", "none")

    animal: Animal = Animal.__new__(Animal)
    animal.animal_type = AnimalType.FEEDLOT_STEER
    animal.body_weight = 400.0
    animal.mature_body_weight = 600.0
    animal.breed = Breed.AN
    animal.sex = Sex.STEER
    animal.days_on_feed = 30
    animal.previous_nutrition_supply = None

    result = animal.calculate_nutrition_requirements(
        housing="Open_Lot",
        walking_distance=0.0,
        previous_temperature=20.0,
        available_feeds=[],
    )
    assert isinstance(result, NutritionRequirements)
    assert result.pregnancy_energy == pytest.approx(0.0)
    assert result.lactation_energy == pytest.approx(0.0)
    assert result.activity_energy == pytest.approx(0.0)
    assert result.maintenance_energy > 0.0
    assert result.growth_energy > 0.0
    assert result.dry_matter > 0.0


@pytest.mark.unit
def test_daily_nutrients_update_sets_phosphorus_for_feedlot() -> None:
    """_daily_nutrients_update must copy nutrition_requirements.phosphorus into nutrients.phosphorus_requirement."""
    from RUFAS.biophysical.animal.data_types.nutrition_data_structures import NutritionRequirements
    from RUFAS.biophysical.animal.nutrients.nutrients import Nutrients

    animal = _make_feedlot_animal()
    animal.nutrients = Nutrients()
    nr = NutritionRequirements.make_empty_nutrition_requirements()
    nr.phosphorus = 18.5
    animal.nutrition_requirements = nr

    animal._daily_nutrients_update()

    assert animal.nutrients.phosphorus_requirement == pytest.approx(18.5)


@pytest.mark.unit
def test_daily_nutrients_update_noop_when_no_nutrition_requirements() -> None:
    """_daily_nutrients_update must not raise when nutrition_requirements is None."""
    from RUFAS.biophysical.animal.nutrients.nutrients import Nutrients

    animal = _make_feedlot_animal()
    animal.nutrients = Nutrients()
    animal.nutrition_requirements = None  # type: ignore[assignment]

    animal._daily_nutrients_update()

    assert animal.nutrients.phosphorus_requirement == pytest.approx(0.0)
