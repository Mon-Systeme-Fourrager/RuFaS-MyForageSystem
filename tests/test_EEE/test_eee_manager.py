import pytest
from pytest_mock import MockerFixture

from RUFAS.EEE.EEE_manager import EEEManager
from RUFAS.EEE.economics.framework import EconomicFramework
from RUFAS.EEE.energy import EnergyEstimator
from RUFAS.input_manager import InputManager
from RUFAS.output_manager import OutputManager


def test_eee_manager_init() -> None:
    """Test initialization of EEEManager class."""
    assert EEEManager() is not None


@pytest.mark.parametrize(
    "simulate_animals,simulate_feed,simulate_fields,simulate_manure,expected_log_count,"
    "expect_emissions,expect_energy",
    [
        (True, True, True, True, 4, True, True),
        (False, True, True, True, 4, True, True),
        (True, False, True, True, 4, True, True),
        (True, True, True, False, 4, True, True),
        (True, True, False, True, 1, False, False),
        (False, False, False, False, 1, False, False),
    ],
)
def test_estimate_all(
    mocker: MockerFixture,
    simulate_animals: bool,
    simulate_feed: bool,
    simulate_fields: bool,
    simulate_manure: bool,
    expected_log_count: int,
    expect_emissions: bool,
    expect_energy: bool,
) -> None:
    """Test estimate_all runs emissions and energy only when fields are simulated."""
    om = OutputManager()
    mock_om_add_log = mocker.patch.object(om, "add_log")
    mock_emissions_init = mocker.patch("RUFAS.EEE.emissions.EmissionsEstimator.__init__", return_value=None)
    mock_estimate_emissions = mocker.patch("RUFAS.EEE.emissions.EmissionsEstimator.estimate_farmgrown_feed_emissions")
    mock_estimate_energy = mocker.patch.object(EnergyEstimator, "estimate_all")
    mock_estimate_economics = mocker.patch.object(EEEManager, "_estimate_economics")

    EEEManager.estimate_all(
        simulate_animals=simulate_animals,
        simulate_feed=simulate_feed,
        simulate_fields=simulate_fields,
        simulate_manure=simulate_manure,
    )

    assert mock_om_add_log.call_count == expected_log_count
    mock_estimate_economics.assert_called_once()

    if expect_emissions:
        mock_emissions_init.assert_called_once_with(
            simulate_animals=simulate_animals,
            simulate_feed=simulate_feed,
            simulate_fields=simulate_fields,
            simulate_manure=simulate_manure,
        )
        mock_estimate_emissions.assert_called_once_with()
    else:
        mock_emissions_init.assert_not_called()
        mock_estimate_emissions.assert_not_called()

    if expect_energy:
        mock_estimate_energy.assert_called_once_with(
            simulate_animals=simulate_animals,
            simulate_feed=simulate_feed,
            simulate_fields=simulate_fields,
            simulate_manure=simulate_manure,
        )
    else:
        mock_estimate_energy.assert_not_called()


@pytest.mark.unit
@pytest.mark.parametrize(
    "economic_inputs_declared,runtime_metadata_loaded,expected_log_names,expect_error,expect_analysis",
    [
        (False, True, ["No Economics processing"], False, False),
        (True, False, [], True, False),
        (True, True, ["Economics Processing", "Economics Processing"], False, True),
    ],
)
def test_estimate_economics(
    mocker: MockerFixture,
    economic_inputs_declared: bool,
    runtime_metadata_loaded: bool,
    expected_log_names: list[str],
    expect_error: bool,
    expect_analysis: bool,
) -> None:
    """Test _estimate_economics runs only when economic_inputs is declared and its runtime metadata loads."""
    om = OutputManager()
    mock_add_log = mocker.patch.object(om, "add_log")
    mock_add_error = mocker.patch.object(om, "add_error")
    mock_exists = mocker.patch.object(
        InputManager, "check_property_exists_in_pool", return_value=economic_inputs_declared
    )
    mock_load_runtime = mocker.patch.object(InputManager, "load_runtime_metadata", return_value=runtime_metadata_loaded)
    mocker.patch.object(EconomicFramework, "__init__", return_value=None)
    mock_analysis = mocker.patch.object(EconomicFramework, "run_economic_analysis")
    info_map = {"class": "EEEManager", "function": "estimate_all"}

    EEEManager._estimate_economics(om, info_map)

    mock_exists.assert_called_once_with("economic_inputs")
    assert [call.args[0] for call in mock_add_log.call_args_list] == expected_log_names
    if economic_inputs_declared:
        mock_load_runtime.assert_called_once_with("EEE_econ", eager_termination=True)
    else:
        mock_load_runtime.assert_not_called()
    assert mock_add_error.called is expect_error
    assert mock_analysis.called is expect_analysis


@pytest.mark.integration
def test_estimate_economics_skips_without_economic_inputs(mocker: MockerFixture) -> None:
    """Test a real InputManager pool without economic_inputs skips economics without logging an error."""
    om = OutputManager()
    mock_add_error = mocker.patch.object(om, "add_error")
    mock_analysis = mocker.patch.object(EconomicFramework, "run_economic_analysis")
    im = InputManager()
    assert im.check_property_exists_in_pool("economic_inputs") is False

    EEEManager._estimate_economics(om, {"class": "EEEManager", "function": "estimate_all"})

    mock_add_error.assert_not_called()
    mock_analysis.assert_not_called()
