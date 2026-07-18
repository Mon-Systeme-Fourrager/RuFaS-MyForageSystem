"""Beef NRC 2016 nutrition requirements calculator for stocker/backgrounding cattle.

References: NRC (2016) Nutrient Requirements of Beef Cattle, 8th ed.
  Ch. 10 (Feed Intake, Eq.10-5 for forage-based growing cattle),
  Ch. 11 (Maintenance), Ch. 12 (Growth), Ch. 6 (Protein), Ch. 7 (Minerals).

DMI uses Eq.10-5 (forage-based growing cattle), NOT Eq.10-1 (feedlot finishing).
Growth (NEg, NPg, MP) and mineral equations are reused from BeefNRCRequirementsCalculator
via composition. No lactation, pregnancy, or compensatory-gain terms.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from RUFAS.biophysical.animal.animal_module_constants import AnimalModuleConstants
from RUFAS.biophysical.animal.data_types.animal_enums import Sex
from RUFAS.biophysical.animal.data_types.animal_types import AnimalType
from RUFAS.biophysical.animal.data_types.nutrition_data_structures import NutritionRequirements
from RUFAS.biophysical.animal.nutrients.beef_nrc_requirements_calculator import BeefNRCRequirementsCalculator
from RUFAS.biophysical.animal.nutrients.nutrition_requirements_calculator import (
    NutritionRequirementsCalculator,
)
from RUFAS.biophysical.animal.ration.amino_acid import EssentialAminoAcidRequirements


@dataclass
class StockerRequirementsInputs:
    """
    Inputs for BeefStockerRequirementsCalculator.calculate_requirements().

    Attributes
    ----------
    animal_type : AnimalType
        Must be BEEF_STOCKER_STEER or BEEF_STOCKER_HEIFER.
    sex : Sex
        Sex enum member; drives SEX multiplier in NEm.
    body_weight : float
        Live body weight (kg). Must be > 0 and math.isfinite.
    mature_body_weight : float
        Frame-based mature body weight (kg). Use AnimalConfig.beef_mature_cow_weight_kg
        (~520 kg), NOT stocker exit weight. Must be > 0 and math.isfinite.
    breed : str
        Breed string for NRC 2016 Table 19-1 BE lookup.
    target_adg : float
        Target average daily gain (kg/d live weight).
    temperature_c : float
        Ambient temperature (°C) for cold-stress a2 term.
    ne_diet_concentration : float
        NEm concentration of the current ration (Mcal/kg DM). Drives Eq.10-5 DMI.
    mud_condition : str
        'none', 'mild', or 'severe'; drives NRC 2016 mud multiplier. Defaults to 'none'.

    """

    animal_type: AnimalType
    sex: Sex
    body_weight: float
    mature_body_weight: float
    breed: str
    target_adg: float
    temperature_c: float
    ne_diet_concentration: float
    mud_condition: str = field(default=AnimalModuleConstants.BEEF_MUD_CONDITION_NONE)


class BeefStockerRequirementsCalculator(NutritionRequirementsCalculator):
    """Nutrition requirements calculator for stocker/backgrounding cattle — NRC 2016 (Beef)."""

    @classmethod
    def calculate_requirements(cls, inputs: StockerRequirementsInputs) -> NutritionRequirements:
        """
        Calculate all nutritional requirements for a beef stocker/backgrounding animal.

        Parameters
        ----------
        inputs : StockerRequirementsInputs
            Fully populated input dataclass.

        Returns
        -------
        NutritionRequirements
            Nutrition requirements; pregnancy, lactation, and activity fields = 0.

        Raises
        ------
        ValueError
            If animal_type is not a beef stocker type; if body_weight or
            mature_body_weight are not positive and finite; or if sex is not a
            recognised value in SEX_NEm_MULTIPLIER.

        """
        cls._validate_inputs(inputs)

        sbw: float = BeefNRCRequirementsCalculator._calculate_sbw(inputs.body_weight)
        msbw: float = inputs.mature_body_weight * 0.96
        eqsbw: float = BeefNRCRequirementsCalculator._calculate_eqsbw(sbw, msbw)
        eqebw: float = BeefNRCRequirementsCalculator._calculate_eqebw(eqsbw)
        ebg: float = inputs.target_adg * 0.956

        ne_maintenance: float = BeefNRCRequirementsCalculator._calculate_maintenance_energy(
            sbw, inputs.breed, inputs.sex, "Open_Lot", inputs.mud_condition, inputs.temperature_c
        )
        ne_growth: float = BeefNRCRequirementsCalculator._calculate_growth_energy(eqebw, ebg)
        np_growth: float = BeefNRCRequirementsCalculator._calculate_np_growth(inputs.target_adg, ne_growth)
        mp: float = BeefNRCRequirementsCalculator._calculate_metabolizable_protein(inputs.body_weight, np_growth, eqsbw)

        calcium: float = BeefNRCRequirementsCalculator._calculate_calcium(sbw, np_growth)
        phosphorus: float = BeefNRCRequirementsCalculator._calculate_phosphorus(sbw, np_growth)

        dmi: float = cls._calculate_dmi(inputs.body_weight, inputs.ne_diet_concentration)

        empty_aa = EssentialAminoAcidRequirements(
            histidine=0.0,
            isoleucine=0.0,
            leucine=0.0,
            lysine=0.0,
            methionine=0.0,
            phenylalanine=0.0,
            threonine=0.0,
            thryptophan=0.0,
            valine=0.0,
        )

        return NutritionRequirements(
            maintenance_energy=ne_maintenance,
            growth_energy=ne_growth,
            pregnancy_energy=0.0,
            lactation_energy=0.0,
            metabolizable_protein=mp,
            calcium=calcium,
            phosphorus=phosphorus,
            process_based_phosphorus=0.0,
            dry_matter=dmi,
            activity_energy=0.0,
            essential_amino_acids=empty_aa,
        )

    @staticmethod
    def _validate_inputs(inputs: StockerRequirementsInputs) -> None:
        """
        Validate StockerRequirementsInputs and raise ValueError on any violation.

        Parameters
        ----------
        inputs : StockerRequirementsInputs
            Fully populated input dataclass.

        Raises
        ------
        ValueError
            If animal_type is not a beef stocker type; if body_weight or
            mature_body_weight are not positive and finite; or if sex is not a
            recognised value in SEX_NEm_MULTIPLIER.

        """
        if not inputs.animal_type.is_beef_stocker:
            raise ValueError(
                f"BeefStockerRequirementsCalculator only handles stocker types; got {inputs.animal_type.value}."
            )
        if not math.isfinite(inputs.body_weight) or inputs.body_weight <= 0.0:
            raise ValueError(f"body_weight must be positive and finite, got {inputs.body_weight}")
        if not math.isfinite(inputs.mature_body_weight) or inputs.mature_body_weight <= 0.0:
            raise ValueError(f"mature_body_weight must be positive and finite, got {inputs.mature_body_weight}")
        if inputs.sex not in AnimalModuleConstants.SEX_NEm_MULTIPLIER:
            valid_sexes = ", ".join(str(s) for s in AnimalModuleConstants.SEX_NEm_MULTIPLIER)
            raise ValueError(f"sex must be one of {valid_sexes}; got {inputs.sex}.")

    @classmethod
    def _calculate_dmi(cls, body_weight: float, ne_diet_concentration: float) -> float:
        """
        Predicted dry matter intake for forage-based stocker cattle (kg/d).

        Parameters
        ----------
        body_weight : float
            Live body weight (kg).
        ne_diet_concentration : float
            NEm concentration of the ration (Mcal/kg DM).

        Returns
        -------
        float
            Predicted DMI (kg/d). NRC 2016 Eq.10-5 (forage-based growing cattle).
            No pregnancy intercept and no lactation term — stocker animals
            neither gestate nor lactate.

        """
        ne_c: float = max(ne_diet_concentration, 0.95)
        bw075: float = body_weight**0.75
        ne_m_intake: float = bw075 * (
            AnimalModuleConstants.BEEF_DMI_COW_NE_QUAD * ne_c**2 + AnimalModuleConstants.BEEF_DMI_COW_NE_LINEAR * ne_c
        )
        return ne_m_intake / ne_c if ne_m_intake > 0.0 else 0.0
