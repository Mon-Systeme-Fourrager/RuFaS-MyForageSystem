"""Beef NRC 2016 nutrition requirements calculator.

References: NRC (2016) Nutrient Requirements of Beef Cattle, 8th ed.
  Ch. 10 (Feed Intake), Ch. 11 (Maintenance), Ch. 12 (Growth), Ch. 6 (Protein),
  Ch. 7 (Minerals), Ch. 19 (Model Equations).
"""

from __future__ import annotations

from RUFAS.biophysical.animal.animal_module_constants import AnimalModuleConstants
from RUFAS.biophysical.animal.data_types.animal_types import AnimalType
from RUFAS.biophysical.animal.data_types.nutrition_data_structures import NutritionRequirements
from RUFAS.biophysical.animal.nutrients.nutrition_requirements_calculator import (
    NutritionRequirementsCalculator,
)
from RUFAS.biophysical.animal.ration.amino_acid import EssentialAminoAcidRequirements


class BeefNRCRequirementsCalculator(NutritionRequirementsCalculator):
    """Nutrition requirements calculator for feedlot cattle — NRC 2016 (Beef)."""

    @classmethod
    def calculate_requirements(
        cls,
        body_weight: float,
        mature_body_weight: float,
        animal_type: AnimalType,
        breed: str,
        sex: str,
        days_on_feed: int,
        target_adg: float,
        implant_adg_factor: float,
        housing: str,
        mud_condition: str,
        temperature_c: float,
        ne_diet_concentration: float,
        process_based_phosphorus_requirement: float,
    ) -> NutritionRequirements:
        """
        Calculate all nutritional requirements for a feedlot finishing animal.

        Parameters
        ----------
        body_weight : float
            Live body weight (kg).
        mature_body_weight : float
            Frame-based mature body weight (kg); used to derive MSBW and EQSBW.
        animal_type : AnimalType
            Must be FEEDLOT_STEER or FEEDLOT_HEIFER.
        breed : str
            Breed string (e.g. 'Angus') for NRC 2016 Table 19-1 BE lookup.
        sex : str
            'steer', 'female', or 'male' for SEX multiplier.
        days_on_feed : int
            Days since pen placement; drives receiving-period DMI adjustment.
        target_adg : float
            Target average daily gain (kg/d live weight).
        implant_adg_factor : float
            ADG multiplier from growth implant (1.0 = no implant).
        housing : str
            'Barn' or 'Open_Lot' (reserved for future activity adjustments).
        mud_condition : str
            'none', 'mild', or 'severe'; drives NRC 2016 mud multiplier.
        temperature_c : float
            Ambient temperature for cold-stress a2 term (°C).
        ne_diet_concentration : float
            NEm concentration of the current ration (Mcal/kg DM).
        process_based_phosphorus_requirement : float
            Phosphorus requirement from the process-based submodule (g/d).

        Returns
        -------
        NutritionRequirements
            All nutritional requirements; pregnancy/lactation/activity fields = 0.

        """
        if animal_type.is_beef_cow_calf:
            raise NotImplementedError(
                f"BeefNRCRequirementsCalculator is feedlot-only. "
                f"Use BeefCowCalfRequirementsCalculator for {animal_type.value}."
            )
        if not animal_type.is_feedlot:
            raise ValueError(
                f"BeefNRCRequirementsCalculator only handles feedlot animal types, " f"got {animal_type.value}."
            )

        sbw = cls._calculate_sbw(body_weight)
        msbw = mature_body_weight * 0.96
        eqsbw = cls._calculate_eqsbw(sbw, msbw)
        eqebw = cls._calculate_eqebw(eqsbw)

        effective_adg = target_adg * implant_adg_factor
        ebg = effective_adg * 0.956  # EBG = 0.956 × ADG (NRC 2016 Ch. 12)

        ne_maintenance = cls._calculate_maintenance_energy(sbw, breed, sex, housing, mud_condition, temperature_c)
        ne_growth = cls._calculate_growth_energy(eqebw, ebg)

        np_growth = cls._calculate_np_growth(effective_adg, ne_growth)
        mp = cls._calculate_metabolizable_protein(body_weight, np_growth, eqsbw)

        calcium = cls._calculate_calcium(sbw, np_growth)
        phosphorus = cls._calculate_phosphorus(sbw, np_growth)

        dmi = cls._calculate_dmi(body_weight, ne_diet_concentration, days_on_feed)

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
            process_based_phosphorus=process_based_phosphorus_requirement,
            dry_matter=dmi,
            activity_energy=0.0,
            essential_amino_acids=empty_aa,
        )

    @staticmethod
    def _calculate_sbw(body_weight: float) -> float:
        """
        Shrunk body weight — removes gut fill.

        Parameters
        ----------
        body_weight : float
            Live body weight (kg).

        Returns
        -------
        float
            SBW = 0.96 × BW (kg). NRC 2016 Ch. 11.

        """
        return body_weight * 0.96

    @staticmethod
    def _calculate_ebw(sbw: float) -> float:
        """
        Empty body weight from shrunk body weight.

        Parameters
        ----------
        sbw : float
            Shrunk body weight (kg).

        Returns
        -------
        float
            EBW = 0.891 × SBW (kg). NRC 2016 Ch. 12.

        """
        return sbw * 0.891

    @staticmethod
    def _calculate_eqsbw(sbw: float, msbw: float, srw: float = 478.0) -> float:
        """
        Equivalent shrunk body weight — normalises across frame sizes.

        Parameters
        ----------
        sbw : float
            Shrunk body weight (kg).
        msbw : float
            Mature SBW = 0.96 × mature_BW (kg).
        srw : float, optional
            Standard reference weight for Choice-grade steer (kg).
            NRC 2016 Table 12-2 default is 478 kg.

        Returns
        -------
        float
            EQSBW = SBW × (SRW / MSBW) (kg). NRC 2016 Ch. 12.

        """
        return sbw * (srw / msbw)

    @staticmethod
    def _calculate_eqebw(eqsbw: float) -> float:
        """
        Equivalent empty body weight.

        Parameters
        ----------
        eqsbw : float
            Equivalent shrunk body weight (kg).

        Returns
        -------
        float
            EQEBW = 0.891 × EQSBW (kg). Used as weight basis in NEg equation.

        """
        return eqsbw * 0.891

    @classmethod
    def _calculate_maintenance_energy(
        cls,
        sbw: float,
        breed: str,
        sex: str,
        housing: str,
        mud_condition: str,
        temperature_c: float,
    ) -> float:
        """
        Net energy for maintenance (Mcal/d).

        Parameters
        ----------
        sbw : float
            Shrunk body weight (kg).
        breed : str
            Breed string for NRC 2016 Table 19-1 BE multiplier.
        sex : str
            Sex string for NRC 2016 Table 19-1 SEX multiplier.
        housing : str
            Housing type (reserved; not used in current implementation).
        mud_condition : str
            Pen mud depth: 'none', 'mild', or 'severe'.
        temperature_c : float
            Ambient temperature for cold-stress a2 addition (°C).

        Returns
        -------
        float
            NEm (Mcal/d). Base formula NRC 2016 Eq. 11-1.
            Cold-stress a2 term added when temperature < 20 °C (Eq. 11-2).

        """
        be: float = AnimalModuleConstants.BREED_NEm_MULTIPLIER.get(breed, 1.0)
        sex_mult: float = AnimalModuleConstants.SEX_NEm_MULTIPLIER.get(sex, 1.00)
        sbw075: float = sbw**0.75

        # a2 cold-stress addition; zero at thermoneutral (Tp >= 20 °C)
        a2 = max(0.0, 0.0007 * (20.0 - temperature_c))
        ne_m = sbw075 * (0.077 * be * sex_mult + a2)

        mud_multiplier_map = {
            "none": AnimalModuleConstants.MUD_NEm_MULTIPLIER_NONE,
            "mild": AnimalModuleConstants.MUD_NEm_MULTIPLIER_MILD,
            "severe": AnimalModuleConstants.MUD_NEm_MULTIPLIER_SEVERE,
        }
        ne_m *= mud_multiplier_map.get(mud_condition, 1.00)

        return ne_m

    @staticmethod
    def _calculate_growth_energy(eqebw: float, ebg: float) -> float:
        """
        Net energy for growth — retained energy (Mcal/d).

        Parameters
        ----------
        eqebw : float
            Equivalent empty body weight (kg). Use EQEBW = 0.891 × EQSBW.
        ebg : float
            Empty body gain (kg/d). Use EBG = 0.956 × ADG.

        Returns
        -------
        float
            RE = NEg (Mcal/d). NRC 2016 Ch. 12 Eq. 12-3.

        """
        if ebg <= 0.0:
            return 0.0
        eqebw_075: float = eqebw**0.75
        ebg_1097: float = ebg**1.097
        return 0.0635 * eqebw_075 * ebg_1097

    @staticmethod
    def _calculate_np_growth(adg: float, ne_growth: float) -> float:
        """
        Net protein deposited in gain (g/d).

        Parameters
        ----------
        adg : float
            Effective average daily gain — live weight basis (kg/d).
        ne_growth : float
            NEg / retained energy (Mcal/d).

        Returns
        -------
        float
            NPg (g/d) = ADG × (268 - 29.4 × RE/ADG). NRC 2016 Ch. 6.

        """
        if adg <= 0.0 or ne_growth <= 0.0:
            return 0.0
        return max(0.0, adg * (268.0 - 29.4 * ne_growth / adg))

    @staticmethod
    def _calculate_metabolizable_protein(
        body_weight: float,
        np_growth: float,
        eqsbw: float,
    ) -> float:
        """
        Metabolizable protein requirement (g/d).

        Parameters
        ----------
        body_weight : float
            Live body weight (kg). MPm uses live BW^0.75, not SBW.
        np_growth : float
            Net protein in gain (g/d) from _calculate_np_growth.
        eqsbw : float
            Equivalent shrunk body weight (kg). Drives MP efficiency for gain.

        Returns
        -------
        float
            MP (g/d) = MPm + MPg. NRC 2016 Ch. 6 / Box 12-1.

        """
        bw075: float = body_weight**0.75
        mp_maintenance: float = 3.8 * bw075  # live BW per Box 12-1
        if np_growth > 0.0:
            eff_g = max(0.492, 0.834 - 0.00114 * eqsbw)
            mp_growth = np_growth / eff_g
        else:
            mp_growth = 0.0
        return mp_maintenance + mp_growth

    @staticmethod
    def _calculate_calcium(sbw: float, np_growth: float) -> float:
        """
        Dietary calcium requirement (g/d).

        Parameters
        ----------
        sbw : float
            Shrunk body weight (kg).
        np_growth : float
            Net protein deposited in gain (g/d).

        Returns
        -------
        float
            Ca (g/d) = net_Ca / 0.50 absorption efficiency.
            NRC 2016 Table 19-3: net_Ca = 0.0308×SBW + NPg×0.142.

        """
        net_ca = 0.0308 * sbw + np_growth * 0.142
        return net_ca / 0.50

    @staticmethod
    def _calculate_phosphorus(sbw: float, np_growth: float) -> float:
        """
        Dietary phosphorus requirement (g/d).

        Parameters
        ----------
        sbw : float
            Shrunk body weight (kg).
        np_growth : float
            Net protein deposited in gain (g/d).

        Returns
        -------
        float
            P (g/d) = net_P / 0.68 absorption efficiency.
            NRC 2016 Table 19-3: net_P = 0.02353×SBW + NPg×0.05735.

        """
        net_p = 0.02353 * sbw + np_growth * 0.05735
        return net_p / 0.68

    @classmethod
    def _calculate_dmi(
        cls,
        body_weight: float,
        ne_diet_concentration: float,
        days_on_feed: int,
    ) -> float:
        """
        Predicted dry matter intake for yearling feedlot cattle (kg/d).

        Parameters
        ----------
        body_weight : float
            Live body weight (kg).
        ne_diet_concentration : float
            NEm concentration of the ration (Mcal/kg DM).
        days_on_feed : int
            Days since pen placement; drives receiving-period adjustment.

        Returns
        -------
        float
            Predicted DMI (kg/d). NRC 2016 Eq. 10-1.

        """
        ne_c: float = max(ne_diet_concentration, 0.95)
        bw075: float = body_weight**0.75
        ne_m_intake: float = bw075 * (0.2435 * ne_c - 0.0466 * ne_c**2 - 0.0869)
        dmi = ne_m_intake / ne_c if ne_m_intake > 0.0 else 0.0

        if days_on_feed <= AnimalModuleConstants.RECEIVING_PERIOD_DAYS:
            dmi *= AnimalModuleConstants.RECEIVING_DMI_FRACTION

        return max(dmi, AnimalModuleConstants.FEEDLOT_MIN_DMI_RATIO * body_weight)
