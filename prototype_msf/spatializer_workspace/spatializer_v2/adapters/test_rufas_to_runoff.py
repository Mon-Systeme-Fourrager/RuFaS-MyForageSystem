"""
Tests for rufas_to_runoff.py.

The mocks are minimal dataclasses mirroring the real RUFAS attribute path
``SimulationEngine.field_manager.fields[i].field_data.name`` and
``Field.soil.data.soil_layers[0].water_filled_pore_space``, so a wrong path
fails here instead of silently passing as it would with a free MagicMock.
RUFAS itself is not imported.
"""

from dataclasses import dataclass
from typing import List, Optional

import pytest

from spatializer_v2.adapters.exceptions import IncompleteRufasStateError
from spatializer_v2.adapters.rufas_to_runoff import rufas_state_to_runoff_inputs
from spatializer_v2.evaluators.runoff import RunoffInputs


@dataclass
class MockLayerData:
    water_filled_pore_space: Optional[float]


@dataclass
class MockSoilData:
    soil_layers: List[MockLayerData]


@dataclass
class MockSoil:
    data: MockSoilData


@dataclass
class MockFieldData:
    name: str


@dataclass
class MockField:
    field_data: MockFieldData
    soil: MockSoil


@dataclass
class MockFieldManager:
    fields: List[MockField]


@dataclass
class MockSimulationEngine:
    field_manager: MockFieldManager


@dataclass
class EmptyState:
    """State object with no ``field_manager`` attribute."""


def make_field(name: str, surface_saturation: Optional[float] = 0.65) -> MockField:
    return MockField(
        field_data=MockFieldData(name=name),
        soil=MockSoil(data=MockSoilData(soil_layers=[MockLayerData(surface_saturation)])),
    )


def make_engine(*fields: MockField) -> MockSimulationEngine:
    return MockSimulationEngine(field_manager=MockFieldManager(fields=list(fields)))


def test_1_complete_state_returns_inputs() -> None:
    engine = make_engine(make_field("field_36-1", 0.65))
    result = rufas_state_to_runoff_inputs(engine, "field_36-1", slope_pct=2.3)
    assert result == RunoffInputs(slope_pct=2.3, soil_saturation=0.65)


def test_2_missing_slope_raises() -> None:
    engine = make_engine(make_field("field_36-1", 0.65))
    with pytest.raises(IncompleteRufasStateError) as exc:
        rufas_state_to_runoff_inputs(engine, "field_36-1", slope_pct=None)
    assert any(m.startswith("slope_pct (") for m in exc.value.missing_fields)
    assert exc.value.field_id == "field_36-1"


def test_3_field_name_not_found_raises() -> None:
    engine = make_engine(make_field("otro_nombre", 0.65))
    with pytest.raises(IncompleteRufasStateError) as exc:
        rufas_state_to_runoff_inputs(engine, "field_36-1", slope_pct=2.3)
    assert any("not found" in m for m in exc.value.missing_fields)


def test_4_no_soil_layers_raises() -> None:
    field = MockField(
        field_data=MockFieldData(name="field_36-1"),
        soil=MockSoil(data=MockSoilData(soil_layers=[])),
    )
    with pytest.raises(IncompleteRufasStateError) as exc:
        rufas_state_to_runoff_inputs(make_engine(field), "field_36-1", slope_pct=2.3)
    assert any("water_filled_pore_space" in m for m in exc.value.missing_fields)


def test_5_surface_saturation_none_raises() -> None:
    engine = make_engine(make_field("field_36-1", None))
    with pytest.raises(IncompleteRufasStateError) as exc:
        rufas_state_to_runoff_inputs(engine, "field_36-1", slope_pct=2.3)
    assert "water_filled_pore_space is None" in exc.value.missing_fields


def test_6_state_without_field_manager_raises() -> None:
    with pytest.raises(IncompleteRufasStateError) as exc:
        rufas_state_to_runoff_inputs(EmptyState(), "field_36-1", slope_pct=2.3)
    assert any("field_manager" in m for m in exc.value.missing_fields)


def test_7_multiple_fields_picks_matching_one() -> None:
    engine = make_engine(
        make_field("field_A", 0.10),
        make_field("field_B", 0.90),
        make_field("field_36-1", 0.65),
    )
    result = rufas_state_to_runoff_inputs(engine, "field_36-1", slope_pct=2.3)
    assert result == RunoffInputs(slope_pct=2.3, soil_saturation=0.65)
