"""
rufas_to_runoff.py — RUFAS state → RunoffInputs adapter

Extracts soil saturation from the surface layer of a RUFAS field
and combines with slope (from Jérémie's LiDAR API, injected
externally) to build RunoffInputs.

Design decision — surface layer only:
    Runoff risk is driven by whether the topsoil can absorb
    incoming precipitation. RUFAS provides water_filled_pore_space
    per soil layer (default depths: 0-20, 20-50, 50-80, 80-200 mm).
    We use the surface layer (soil_layers[0], 0-20 mm) as the
    single saturation indicator for runoff.

    TODO: Confirm literature reference for topsoil depth relevant
    to runoff (SCS Curve Number, MUSLE, or Quebec-specific
    IRDA-MAPAQ). Depth 0-20 mm is what RUFAS defaults to; may
    differ from agronomic "topsoil" (typically 0-15 or 0-30 cm).

Version: 0.1.0-alpha
"""

from typing import Optional, Any
from spatializer_v2.evaluators.runoff import RunoffInputs
from spatializer_v2.adapters.exceptions import IncompleteRufasStateError

__version__ = "0.1.0-alpha"


def rufas_state_to_runoff_inputs(
    rufas_state: Any,
    field_name: str,
    slope_pct: Optional[float] = None,
) -> RunoffInputs:
    """
    Convert RUFAS field state into RunoffInputs.

    Parameters
    ----------
    rufas_state
        A SimulationEngine instance (must have .field_manager.fields).
    field_name
        Name of the RUFAS field (matches field.field_data.name).
    slope_pct
        Slope in percent (0-100). Must be provided externally
        because Jérémie's slope API is being fixed.

    Returns
    -------
    RunoffInputs
        Ready to pass to RunoffEvaluator.evaluate().

    Raises
    ------
    IncompleteRufasStateError
        If field_name is not found, if surface layer is missing,
        or if slope_pct is None.
    """
    missing = []

    if slope_pct is None:
        missing.append("slope_pct (waiting for Jérémie's API fix)")

    # Find field by name
    try:
        fields = rufas_state.field_manager.fields
    except AttributeError as e:
        missing.append(f"rufas_state.field_manager.fields ({e})")
        if missing:
            raise IncompleteRufasStateError(
                missing_fields=missing,
                field_id=field_name,
            )

    field = next(
        (f for f in fields if f.field_data.name == field_name),
        None,
    )

    if field is None:
        missing.append(f"field with name '{field_name}' not found in field_manager")
        raise IncompleteRufasStateError(
            missing_fields=missing,
            field_id=field_name,
        )

    # Extract surface layer saturation
    try:
        surface_layer = field.soil.data.soil_layers[0]
        soil_saturation = surface_layer.water_filled_pore_space
    except (AttributeError, IndexError) as e:
        missing.append(f"surface_layer.water_filled_pore_space ({e})")
        raise IncompleteRufasStateError(
            missing_fields=missing,
            field_id=field_name,
        )

    if soil_saturation is None:
        missing.append("water_filled_pore_space is None")
        raise IncompleteRufasStateError(
            missing_fields=missing,
            field_id=field_name,
        )

    if missing:
        raise IncompleteRufasStateError(
            missing_fields=missing,
            field_id=field_name,
        )

    return RunoffInputs(
        slope_pct=slope_pct,
        soil_saturation=soil_saturation,
    )
