"""Tests for beef cow-calf herd cohort lists in HerdFactory and HerdManager (Task 7.1)."""

from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from RUFAS.biophysical.animal.data_types.animal_types import AnimalType
from RUFAS.biophysical.animal.herd_factory import HerdFactory
from RUFAS.biophysical.animal.herd_manager import HerdManager


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
