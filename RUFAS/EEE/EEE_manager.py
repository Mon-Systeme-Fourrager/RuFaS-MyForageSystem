from typing import Any

from RUFAS.input_manager import InputManager
from RUFAS.output_manager import OutputManager

from .emissions import EmissionsEstimator
from .energy import EnergyEstimator
from .economics.framework import EconomicFramework


class EEEManager:
    """Coordinates the energy, emissions and economics estimations for the EEE module."""

    @staticmethod
    def estimate_all(simulate_animals: bool, simulate_feed: bool, simulate_fields: bool, simulate_manure: bool) -> None:
        """
        Runs all emissions, energy and economics estimations and records their results to the ``OutputManager``.

        Parameters
        ----------
        simulate_animals : bool
            Whether the simulation initialized and used the AnimalManager module.
        simulate_feed : bool
            Whether the simulation initialized and used the FeedManager module
        simulate_fields : bool
            Whether the simulation initialized and used the FieldManager module.
        simulate_manure : bool
            Whether the simulation initialized and used the ManureManager module

        """
        om = OutputManager()
        info_map = {"class": EEEManager.__class__.__name__, "function": EEEManager.estimate_all.__name__}

        if simulate_fields:
            om.add_log("Emissions Processing", "Starting processing of emissions.", info_map)
            emissions_estimator = EmissionsEstimator(
                simulate_animals=simulate_animals,
                simulate_feed=simulate_feed,
                simulate_fields=simulate_fields,
                simulate_manure=simulate_manure,
            )
            emissions_estimator.estimate_farmgrown_feed_emissions()
            om.add_log("Emissions Processing", "Completed processing of emissions.", info_map)

            om.add_log("Energy Processing", "Starting processing of energy.", info_map)
            EnergyEstimator.estimate_all(
                simulate_animals=simulate_animals,
                simulate_feed=simulate_feed,
                simulate_fields=simulate_fields,
                simulate_manure=simulate_manure,
            )
            om.add_log("Energy Processing", "Completed processing of energy.", info_map)

        else:
            om.add_log(
                "No Energy or Emissions processing",
                "Fields not simulated, none of these calculations will be run.",
                info_map,
            )

        EEEManager._estimate_economics(om, info_map)

    @staticmethod
    def _estimate_economics(om: OutputManager, info_map: dict[str, Any]) -> None:
        """
        Runs the economic analysis when the active metadata declares the ``economic_inputs`` input file.

        Economics is opt-in: scenarios without ``economic_inputs`` (e.g. Mon Système Fourrager runs, which carry no
        economic data) skip it with a log entry instead of reporting errors or failing at the end of the simulation.

        Parameters
        ----------
        om : OutputManager
            The output manager that receives the economics logs and errors.
        info_map : dict[str, Any]
            Context information used for logging and error reporting.

        """
        im = InputManager()
        if not im.check_property_exists_in_pool("economic_inputs"):
            om.add_log(
                "No Economics processing",
                "'economic_inputs' is not declared in the active metadata, economic calculations will not be run.",
                info_map,
            )
            return

        if not im.load_runtime_metadata("EEE_econ", eager_termination=True):
            om.add_error(
                "Economics metadata load failure",
                "Failed to load runtime metadata for 'EEE_econ'. Aborting economics estimation.",
                info_map,
            )
            return

        om.add_log("Economics Processing", "Starting processing of economics.", info_map)
        EconomicFramework().run_economic_analysis()
        om.add_log("Economics Processing", "Completed processing of economics.", info_map)
