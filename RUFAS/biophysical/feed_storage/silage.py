import math
from dataclasses import replace
from typing import Any

from RUFAS.general_constants import GeneralConstants
from RUFAS.data_structures.crop_soil_to_feed_storage_connection import HarvestedCrop
from RUFAS.output_manager import OutputManager
from RUFAS.rufas_time import RufasTime
from RUFAS.units import MeasurementUnits
from RUFAS.weather import Weather

from .storage import Storage
from .silage_constants import (
    PRESEAL_K,
    PRESEAL_KM,
    PRESEAL_FC,
    PRESEAL_ATMOSPHERIC_OXYGEN_FRACTION,
    PRESEAL_INITIAL_PH,
    PRESEAL_EXPOSURE_CAP_DAYS,
    PRESEAL_FALLBACK_EXPOSURE_DAYS,
    PRESEAL_WATER_RETENTION_FRACTION,
    PRESEAL_ALFALFA_MAX_RESPIRATION_RATE,
    PRESEAL_NON_ALFALFA_MAX_RESPIRATION_RATE,
    PRESEAL_MIN_THICKNESS_CM,
    PRESEAL_DEPTH_M_TO_CM,
    PRESEAL_DIFFUSION_COEFFICIENT_FACTOR,
    PRESEAL_DIFFUSION_TEMPERATURE_OFFSET_C,
    PRESEAL_TORTUOSITY,
    PRESEAL_MAX_RELATIVE_DENSITY_NUMERATOR,
    PRESEAL_RELATIVE_DENSITY_CAP_FRACTION,
    PRESEAL_DENSITY_KG_PER_M3_TO_G_PER_CM3,
    PRESEAL_HIGH_DRY_MATTER_THRESHOLD,
    PRESEAL_HIGH_DRY_MATTER_RESPIRATION_FACTOR,
    PRESEAL_LOW_DRY_MATTER_THRESHOLD,
    PRESEAL_RESPIRATION_FACTOR_INTERCEPT,
    PRESEAL_RESPIRATION_FACTOR_LINEAR_COEFFICIENT,
    PRESEAL_RESPIRATION_FACTOR_QUADRATIC_COEFFICIENT,
    PRESEAL_TEMPERATURE_FACTOR_SATURATION_C,
    PRESEAL_TEMPERATURE_FACTOR_COEFFICIENT,
    PRESEAL_TEMPERATURE_FACTOR_RATE,
    PRESEAL_PH_FACTOR_OFFSET,
    PRESEAL_PH_FACTOR_SCALE,
    PRESEAL_LOSS_PER_DAY_COEFFICIENT,
    PRESEAL_TEMPERATURE_RISE_ENERGY_COEFFICIENT,
    PRESEAL_TEMPERATURE_RISE_HEAT_RETENTION_FRACTION,
    PRESEAL_TEMPERATURE_RISE_DENOMINATOR_COEFFICIENT_A,
    PRESEAL_TEMPERATURE_RISE_DENOMINATOR_COEFFICIENT_B,
)

"""Fraction of effluent that is dry matter by mass."""
DRY_MATTER_FRACTION_OF_EFFLUENT = 0.1035
"""Number of days that loss of effluent occurs over after a crop is ensiled."""
EFFLUENT_CONSTRAINER = 10


def _clamp_preseal_fraction(fraction: float) -> float:
    """
    Clamps a Preseal dry-matter-loss fraction to [0.0, 1.0] (spec §6's floor/ceiling requirement for
    new Preseal/Infiltration code). Extracted as its own pure function so the boundary is directly
    unit-testable, since no realistic physical input drives the day-stepping loop in
    `calculate_preseal_loss` anywhere near this range on its own.

    Parameters
    ----------
    fraction : float
        The unclamped fraction.

    Returns
    -------
    float
        `fraction` clamped to [0.0, 1.0].

    """
    return max(0.0, min(fraction, 1.0))


def calculate_preseal_loss(
    crop: HarvestedCrop, exposure_days: float, exposed_area_m2: float, dry_matter_density_kg_per_m3: float
) -> dict[str, float]:
    """
    Calculates the dry matter lost to aerobic respiration before a silage plot is sealed, and the
    resulting temperature rise, by stepping through the exposure duration one day at a time.

    Parameters
    ----------
    crop : HarvestedCrop
        The crop being exposed prior to sealing. Not mutated by this function.
    exposure_days : float
        Total time this crop is exposed before being covered (days), already capped/floored by the
        caller per ``PRESEAL_EXPOSURE_CAP_DAYS``.
    exposed_area_m2 : float
        Surface area of this crop exposed to air (m2).
    dry_matter_density_kg_per_m3 : float
        Packed dry-matter density of the storage (kg DM / m3).

    Returns
    -------
    dict[str, float]
        ``dry_matter_loss_fraction`` (fraction of dry matter lost to respiration) and
        ``final_temperature`` (degrees C, after any self-heating during exposure).

    Notes
    -----
    Translated from ``Silostg.for:634-714`` (``PRESEAL``). The day-stepping loop is preserved
    deliberately — temperature rises each day from respiration heat, feeding into the next day's
    respiration rate (positive feedback). Collapsing this into one evaluation over the full exposure
    window would lose that self-heating effect (design spec §5.1). ``[FS.SIL.13]``.

    """
    total_dry_matter_mass_kg = crop.dry_matter_mass
    dry_matter_fraction = crop.dry_matter_percentage * GeneralConstants.PERCENTAGE_TO_FRACTION
    temperature = crop.temperature
    max_respiration_rate = (
        PRESEAL_ALFALFA_MAX_RESPIRATION_RATE if crop.is_alfalfa else PRESEAL_NON_ALFALFA_MAX_RESPIRATION_RATE
    ) * dry_matter_fraction

    thickness_cm = max(
        PRESEAL_MIN_THICKNESS_CM,
        PRESEAL_DEPTH_M_TO_CM * total_dry_matter_mass_kg / (exposed_area_m2 * dry_matter_density_kg_per_m3),
    )
    diffusion_coefficient = (
        PRESEAL_DIFFUSION_COEFFICIENT_FACTOR * (PRESEAL_DIFFUSION_TEMPERATURE_OFFSET_C + temperature) ** 2
    )
    tortuosity = PRESEAL_TORTUOSITY
    max_relative_density = PRESEAL_MAX_RELATIVE_DENSITY_NUMERATOR / (
        PRESEAL_MAX_RELATIVE_DENSITY_NUMERATOR - dry_matter_fraction
    )
    relative_density = min(
        PRESEAL_RELATIVE_DENSITY_CAP_FRACTION * max_relative_density,
        PRESEAL_DENSITY_KG_PER_M3_TO_G_PER_CM3 * dry_matter_density_kg_per_m3 / dry_matter_fraction,
    )
    porosity = 1.0 - relative_density / max_relative_density
    if dry_matter_fraction > PRESEAL_HIGH_DRY_MATTER_THRESHOLD:
        dry_matter_respiration_factor = PRESEAL_HIGH_DRY_MATTER_RESPIRATION_FACTOR
    elif dry_matter_fraction > PRESEAL_LOW_DRY_MATTER_THRESHOLD:
        dry_matter_respiration_factor = (
            PRESEAL_RESPIRATION_FACTOR_INTERCEPT
            - PRESEAL_RESPIRATION_FACTOR_LINEAR_COEFFICIENT * dry_matter_fraction
            + PRESEAL_RESPIRATION_FACTOR_QUADRATIC_COEFFICIENT * dry_matter_fraction**2
        )
    else:
        dry_matter_respiration_factor = 1.0

    remaining_exposure_days = exposure_days
    dry_matter_loss_fraction = 0.0
    while remaining_exposure_days > 0.0:
        temperature_factor = (
            1.0
            if temperature >= PRESEAL_TEMPERATURE_FACTOR_SATURATION_C
            else PRESEAL_TEMPERATURE_FACTOR_COEFFICIENT * math.exp(PRESEAL_TEMPERATURE_FACTOR_RATE * temperature)
        )
        ph_factor = (PRESEAL_INITIAL_PH - PRESEAL_PH_FACTOR_OFFSET) / PRESEAL_PH_FACTOR_SCALE
        respiration_rate = max_respiration_rate * dry_matter_respiration_factor * temperature_factor * ph_factor
        gamma = (
            relative_density
            * respiration_rate
            * (PRESEAL_KM + PRESEAL_ATMOSPHERIC_OXYGEN_FRACTION)
            * PRESEAL_FC
            / (diffusion_coefficient * porosity * tortuosity * PRESEAL_ATMOSPHERIC_OXYGEN_FRACTION)
        )
        c = math.sqrt(PRESEAL_K * gamma)
        average_respiration_rate = (
            -respiration_rate
            * PRESEAL_FC
            * (PRESEAL_KM + PRESEAL_ATMOSPHERIC_OXYGEN_FRACTION)
            * (
                math.log(PRESEAL_KM + PRESEAL_ATMOSPHERIC_OXYGEN_FRACTION * math.exp(-c * thickness_cm))
                - math.log(PRESEAL_KM + PRESEAL_ATMOSPHERIC_OXYGEN_FRACTION)
            )
            / (PRESEAL_ATMOSPHERIC_OXYGEN_FRACTION * c * thickness_cm)
        )
        loss_per_day = PRESEAL_LOSS_PER_DAY_COEFFICIENT * average_respiration_rate / dry_matter_fraction

        day_step = min(1.0, remaining_exposure_days)
        loss_today = day_step * loss_per_day
        dry_matter_loss_fraction += loss_today
        remaining_exposure_days -= day_step

        temperature_rise = (
            PRESEAL_TEMPERATURE_RISE_ENERGY_COEFFICIENT
            * loss_today
            * PRESEAL_TEMPERATURE_RISE_HEAT_RETENTION_FRACTION
            / (
                PRESEAL_TEMPERATURE_RISE_DENOMINATOR_COEFFICIENT_A / dry_matter_fraction
                - PRESEAL_TEMPERATURE_RISE_DENOMINATOR_COEFFICIENT_B
            )
        )
        temperature += temperature_rise

    dry_matter_loss_fraction = _clamp_preseal_fraction(dry_matter_loss_fraction)

    return {"dry_matter_loss_fraction": dry_matter_loss_fraction, "final_temperature": temperature}


"""
Effective oxygen permeability by storage class (cm/h), used by the Infiltration phase
(Silostg.for TOWER/BUNKER). Only storage classes with a confirmed citation appear here — an
unsourced class must fail loudly at lookup time, not receive an invented default.

Bunker and Pile: Buckmaster, Rotz & Muck (1989), Trans. ASAE 32(4):1143-1152, as compiled in the
MSF `hf_silo_types` reference table (RT-19). Bunker uses cover permeability only (its
`infiltration_geometry` is "Top only"); Pile uses structure-wall permeability (its geometry is
"Top + sides", matching the source's general silo-wall class of value).
Bag: IFSM Reference Manual (Rotz et al. 2023, v4.7), p.76-77 — "sealed plastic (1.0 cm/h)".

"""
SILAGE_PERMEABILITY_CONSTANTS: dict[str, float] = {
    "Bunker": 1.0,
    "Pile": 4.0,
    "Bag": 1.0,
}


def get_permeability_constants(storage_class_name: str) -> float:
    """
    Looks up the sourced effective oxygen permeability for a silage storage class.

    Parameters
    ----------
    storage_class_name : str
        Name of the `Silage` subclass (e.g. ``"Bunker"``, ``"Pile"``, ``"Bag"``).

    Returns
    -------
    float
        Effective permeability (cm/h).

    Raises
    ------
    ValueError
        If no sourced permeability value exists for the given storage class.

    """
    try:
        return SILAGE_PERMEABILITY_CONSTANTS[storage_class_name]
    except KeyError:
        OutputManager().add_error(
            "Unsourced permeability error",
            f"No sourced permeability reference exists for storage type: {storage_class_name}.",
            info_map={"class": __name__, "function": get_permeability_constants.__name__},
        )
        raise ValueError(f"No sourced permeability reference for storage type: {storage_class_name}.")


def calculate_respirable_substrate_fraction(crop: HarvestedCrop) -> float:
    """
    Calculates the fraction of a crop's dry matter that is still respirable substrate — the ceiling
    that Infiltration's dry-matter loss can never exceed.

    Parameters
    ----------
    crop : HarvestedCrop
        The crop to compute respirable substrate for, using its current composition.

    Returns
    -------
    float
        Respirable substrate as a fraction of dry matter, floored at 0.0.

    Notes
    -----
    ``RS = 1 - NDF - CP - ASH`` (``Silostg.for:810,939``). As infiltration consumes respirable
    substrate, NDF concentration rises via dilution (design spec §2.2's "sponge" analogy) — computed
    fresh from the crop's current composition each call, no new state needed. Crude protein is
    excluded from dilution here: ``Silostg.for:871-872,978-979`` explicitly comment out CP dilution for
    `TOWER`/`BUNKER` ("CRUDE PROTEIN LOSS = DM LOSS", a 1994 model change), unlike `PRESEAL`
    (`Silostg.for:710`) where it is active. ``[FS.SIL.15]``.

    """
    ndf_fraction = crop.ndf * GeneralConstants.PERCENTAGE_TO_FRACTION
    crude_protein_fraction = crop.crude_protein_percent * GeneralConstants.PERCENTAGE_TO_FRACTION
    ash_fraction = crop.ash * GeneralConstants.PERCENTAGE_TO_FRACTION
    return max(0.0, 1.0 - ndf_fraction - crude_protein_fraction - ash_fraction)


def _get_or_initialize_infiltration_ceiling_kg(crop: HarvestedCrop) -> float:
    """
    Fixes the absolute-kg respirable-substrate ceiling the first time Infiltration runs for a crop,
    and returns that fixed value on every later call.

    Parameters
    ----------
    crop : HarvestedCrop
        The crop to fix (or retrieve) the ceiling for. ``infiltration_max_loss_kg`` is set in place
        on first call.

    Returns
    -------
    float
        The crop's fixed Infiltration loss ceiling (kg).

    Notes
    -----
    Added after the 2026-09-10 `/challenge-plan` review: recomputing ``dry_matter_mass *
    calculate_respirable_substrate_fraction(crop)`` on every call let unrelated Effluent/Fermentation
    mass loss move the ceiling between calls, since neither process touches
    ``infiltration_cumulative_loss_kg``. Fixing it once, in absolute kg, at the moment Infiltration
    first processes the crop matches `Silostg.for`'s own invariant — its per-call reference mass
    (``PLOT(NPL,11)``) is held fixed for the whole `TOWER`/`BUNKER` call, never re-derived mid-call.
    ``[FS.SIL.15]``.

    """
    if crop.infiltration_max_loss_kg is None:
        crop.infiltration_max_loss_kg = crop.dry_matter_mass * calculate_respirable_substrate_fraction(crop)
    return crop.infiltration_max_loss_kg


"""Series-diffusion parameter shared by TOWER and BUNKER infiltration math (Silostg.for:813,941)."""
INFILTRATION_DTAU = 492.0
"""Lower bound on porosity so infiltration never fully stops even at maximum packing (Silostg.for:818)."""
INFILTRATION_MIN_POROSITY = 0.02
"""Per-day dry-matter loss coefficient — the daily-step form of Eq. 30's 10-day coefficient 0.628
(Silostg.for:949, Open Decision 1)."""
INFILTRATION_DAILY_LOSS_COEFFICIENT = 0.0628


def _calculate_infiltration_porosity(dry_matter_fraction: float, dry_matter_density_kg_per_m3: float) -> float:
    """
    Calculates packed-material porosity for the Infiltration phase, shared by `Bag` and `Bunker`/`Pile`
    — the calculation doesn't differ by storage geometry.

    Parameters
    ----------
    dry_matter_fraction : float
        Crop dry-matter content as a fraction (0-1).
    dry_matter_density_kg_per_m3 : float
        Packed dry-matter density of the storage (kg DM / m3).

    Returns
    -------
    float
        Porosity, floored at `INFILTRATION_MIN_POROSITY` (Silostg.for:818).

    Notes
    -----
    Translated from ``Silostg.for:372-380``'s relative-density term, using the flat
    ``dry_matter_density_kg_per_m3`` config value rather than the source's packing-profile
    computation (Open Decision 2). ``[FS.SIL.11]``.

    """
    max_relative_density = 3.0 / (3.0 - dry_matter_fraction)
    return max(INFILTRATION_MIN_POROSITY, 1.0 - dry_matter_density_kg_per_m3 / (1000.0 * max_relative_density))


def calculate_bag_infiltration_loss(
    crop: HarvestedCrop, elapsed_days: float, diameter_m: float, dry_matter_density_kg_per_m3: float
) -> float:
    """
    Calculates the dry-matter loss to oxygen infiltration for a `Bag` over an elapsed period,
    advancing the radial oxygen front inward from the bag wall.

    Parameters
    ----------
    crop : HarvestedCrop
        The stored crop being degraded. ``infiltration_cumulative_loss_kg`` is updated in place.
    elapsed_days : float
        Number of days since infiltration was last processed for this crop.
    diameter_m : float
        Bag diameter (m).
    dry_matter_density_kg_per_m3 : float
        Packed dry-matter density of the storage (kg DM / m3).

    Returns
    -------
    float
        Dry-matter loss for this step (kg), already clipped at the RS ceiling.

    Notes
    -----
    Translated from ``Silostg.for:794-835`` (``TOWER``, radial-diffusion portion only — the
    downward-diffusion-into-the-top-plot branch at lines 836-863 does not apply to a `Bag`, which
    has no distinguishable top plot; see design spec §5.2). Re-cadenced from the source's fixed
    10-day step to an arbitrary ``elapsed_days`` step (Open Decision 1) — the per-day coefficient
    ``0.0628`` is ``BUNKER``'s own explicit per-day form (line 949) of the same equation. ``[FS.SIL.11]``.

    """
    if elapsed_days <= 0.0:
        return 0.0

    radius_m = diameter_m / 2.0
    max_loss_kg = _get_or_initialize_infiltration_ceiling_kg(crop)
    if max_loss_kg <= 0.0 or crop.infiltration_cumulative_loss_kg >= max_loss_kg:
        return 0.0

    dry_matter_fraction = crop.dry_matter_percentage * GeneralConstants.PERCENTAGE_TO_FRACTION
    if dry_matter_fraction <= 0.0:
        return 0.0
    porosity = _calculate_infiltration_porosity(dry_matter_fraction, dry_matter_density_kg_per_m3)

    fraction_of_ceiling_consumed = crop.infiltration_cumulative_loss_kg / max_loss_kg
    front_radius_m = radius_m * math.sqrt(max(0.0, 1.0 - fraction_of_ceiling_consumed))
    silo_permeability = get_permeability_constants("Bag")
    if front_radius_m >= radius_m:
        effective_permeability = silo_permeability
    else:
        material_permeability = (
            INFILTRATION_DTAU * porosity / (100.0 * front_radius_m * math.log(radius_m / front_radius_m))
        )
        effective_permeability = 1.0 / (1.0 / material_permeability + 1.0 / silo_permeability)

    depth_m = crop.dry_matter_mass / dry_matter_fraction / dry_matter_density_kg_per_m3 / (math.pi * radius_m**2)
    front_area_m2 = 2.0 * math.pi * front_radius_m * depth_m
    loss_this_step_kg = INFILTRATION_DAILY_LOSS_COEFFICIENT * effective_permeability * front_area_m2 * elapsed_days

    total_loss_kg = min(max_loss_kg, crop.infiltration_cumulative_loss_kg + loss_this_step_kg)
    loss_this_step_kg = total_loss_kg - crop.infiltration_cumulative_loss_kg
    crop.infiltration_cumulative_loss_kg = total_loss_kg
    return loss_this_step_kg


def calculate_bunker_infiltration_loss(
    crop: HarvestedCrop,
    elapsed_days: float,
    storage_class_name: str,
    width_m: float,
    height_m: float,
    dry_matter_density_kg_per_m3: float,
) -> float:
    """
    Calculates the dry-matter loss to oxygen infiltration for a `Bunker` or `Pile` over an elapsed
    period, advancing the vertical oxygen front downward from the open top.

    Parameters
    ----------
    crop : HarvestedCrop
        The stored crop being degraded. ``infiltration_cumulative_loss_kg`` is updated in place.
    elapsed_days : float
        Number of days since infiltration was last processed for this crop.
    storage_class_name : str
        ``"Bunker"`` or ``"Pile"`` — selects the sourced permeability value.
    width_m : float
        Storage width (m).
    height_m : float
        Storage wall height (m).
    dry_matter_density_kg_per_m3 : float
        Packed dry-matter density of the storage (kg DM / m3).

    Returns
    -------
    float
        Dry-matter loss for this step (kg), already clipped at the RS ceiling.

    Notes
    -----
    Translated from ``Silostg.for:879-984`` (``BUNKER``), specifically its per-day "before starting
    to empty this silo" loop (lines 947-958), which already uses the daily-step form of the same
    equation `Bag`'s per-10-day loop needed re-deriving (Open Decision 1). Applied per-crop, not
    per-vertical-section (Open Decision 3 — a documented scope reduction, not a hidden one). Top
    surface area uses ``width_m * height_m`` (the storage's static footprint) rather than the
    source's ``A`` (``Silostg.for:938``, ``10*FDRTE/(DRHO*HEIGHT)``) — the source's term is tied to
    the feed-out rate, which does not exist as a concept in RuFaS yet (Open Decision 4). The
    ``crop.infiltration_cumulative_loss_kg >= max_loss_kg`` early return matches `Bag`'s own guard
    (Task 3) for symmetry — Bunker/Pile's ``front_depth_cm`` grows toward, rather than shrinks toward,
    zero as the ceiling is approached, so it was never at zero-division risk here, but a capped crop
    would otherwise still re-run the full per-day formula every call only to be clipped back to a
    ``0.0`` delta (2026-09-11 `/challenge-plan` re-review). ``[FS.SIL.12]``.

    """
    if elapsed_days <= 0.0:
        return 0.0

    max_loss_kg = _get_or_initialize_infiltration_ceiling_kg(crop)
    if max_loss_kg <= 0.0 or crop.infiltration_cumulative_loss_kg >= max_loss_kg:
        return 0.0

    dry_matter_fraction = crop.dry_matter_percentage * GeneralConstants.PERCENTAGE_TO_FRACTION
    porosity = _calculate_infiltration_porosity(dry_matter_fraction, dry_matter_density_kg_per_m3)

    fraction_of_ceiling_consumed = crop.infiltration_cumulative_loss_kg / max_loss_kg
    front_depth_cm = fraction_of_ceiling_consumed * height_m * 100.0
    silo_permeability = get_permeability_constants(storage_class_name)
    if front_depth_cm <= 0.0:
        effective_permeability = silo_permeability
    else:
        material_permeability = INFILTRATION_DTAU * porosity / front_depth_cm
        effective_permeability = 1.0 / (1.0 / material_permeability + 1.0 / silo_permeability)

    top_area_m2 = width_m * height_m
    loss_this_step_kg = INFILTRATION_DAILY_LOSS_COEFFICIENT * effective_permeability * top_area_m2 * elapsed_days

    total_loss_kg = min(max_loss_kg, crop.infiltration_cumulative_loss_kg + loss_this_step_kg)
    loss_this_step_kg = total_loss_kg - crop.infiltration_cumulative_loss_kg
    crop.infiltration_cumulative_loss_kg = total_loss_kg
    return loss_this_step_kg


class Silage(Storage):
    """
    Represents Silage storage, a subclass of ``Storage``.

    Parameters
    ----------
    config : dict[str, str | float | list[str]]
        Configuration dictionary for the silage storage.

    Attributes
    ----------
    om : OutputManager
        The singleton output manager used for model outputs.

    """

    def __init__(self, config: dict[str, str | float | list[str]]) -> None:
        super().__init__(config)
        self.om = OutputManager()

    def receive_crop(self, crop: HarvestedCrop, simulation_day: int) -> None:
        """
        Receives a harvested crop, then finalizes the Preseal loss of the previously-received crop
        in this storage (if any and not already finalized), since its exposure time is now known.

        Parameters
        ----------
        crop : HarvestedCrop
            The harvested crop being added to the storage.
        simulation_day : int
            The day of the simulation when the crop is being added.

        Notes
        -----
        See design spec §2.1/§4: a crop's Preseal loss cannot be computed the instant it arrives,
        because RuFaS does not yet know how long it will sit exposed. It is finalized here, the
        first moment that becomes knowable — when the next crop arrives in the same storage.

        """
        predecessor = self.stored[-1] if self.stored else None
        super().receive_crop(crop, simulation_day)

        if predecessor is not None and not predecessor.preseal_finalized:
            exposure_days = min(
                PRESEAL_EXPOSURE_CAP_DAYS, max(0.0, (crop.storage_time - predecessor.storage_time).days)
            )
            self._finalize_preseal_loss(predecessor, exposure_days)

    def _finalize_preseal_loss(self, crop: HarvestedCrop, exposure_days: float) -> None:
        """
        Computes and permanently applies this crop's Preseal dry-matter loss.

        Parameters
        ----------
        crop : HarvestedCrop
            The crop whose Preseal loss is being finalized. Mutated in place.
        exposure_days : float
            The resolved exposure duration to use (already capped/floored by the caller).

        Notes
        -----
        Applied exactly once per crop (matches ``Silostg.for``'s one-shot-per-plot semantics) — the
        caller is responsible for only invoking this on crops with ``preseal_finalized is False``.
        If this storage has no configured geometry/density (`_preseal_exposed_area_m2`/
        `_preseal_dry_matter_density_kg_per_m3` returning ``None``), this is a no-op beyond marking
        the crop finalized — existing storages that predate these optional fields are unaffected.
        Likewise a no-op for a crop with no dry matter left (e.g. fed out via ``remove_dry_matter_mass``
        the same day, before `Storage.remove_empty_crops` has swept it out of `self.stored`):
        `calculate_preseal_loss` divides by ``dry_matter_fraction`` in several places, so calling it
        on an empty crop raises `ZeroDivisionError`. ``[FS.SIL.14]``.

        """
        if crop.dry_matter_mass <= 0.0:
            crop.preseal_finalized = True
            return

        exposed_area_m2 = self._preseal_exposed_area_m2()
        dry_matter_density_kg_per_m3 = self._preseal_dry_matter_density_kg_per_m3()
        if exposed_area_m2 is None or dry_matter_density_kg_per_m3 is None:
            crop.preseal_finalized = True
            return

        preseal_result = calculate_preseal_loss(crop, exposure_days, exposed_area_m2, dry_matter_density_kg_per_m3)
        dry_matter_loss_kg = crop.dry_matter_mass * preseal_result["dry_matter_loss_fraction"]

        crop.ndf = self.recalculate_nutrient_percentage(crop.ndf, 0.0, dry_matter_loss_kg, crop.dry_matter_mass)
        crop.crude_protein_percent = self.recalculate_nutrient_percentage(
            crop.crude_protein_percent, 0.0, dry_matter_loss_kg, crop.dry_matter_mass
        )
        # Silostg.for:707-708: only the gas-lost fraction of DM leaves the crop as fresh mass; the
        # water-retained fraction stays behind, so moisture_loss_kg is negative here (a moisture
        # gain that offsets most of dry_matter_loss_kg).
        moisture_loss_kg = -dry_matter_loss_kg * PRESEAL_WATER_RETENTION_FRACTION
        mass_values = self._calculate_mass_attributes_after_loss(crop, dry_matter_loss_kg, moisture_loss_kg)
        crop.dry_matter_mass = mass_values["dry_matter_mass"]
        crop.dry_matter_percentage = mass_values["dry_matter_percentage"]
        crop.temperature = preseal_result["final_temperature"]
        crop.preseal_finalized = True

    def _preseal_exposed_area_m2(self) -> float | None:
        """
        Returns the exposed surface area used by the Preseal calculation for this storage class.

        Returns
        -------
        float | None
            Exposed area (m2). A concrete subclass may return ``None`` when this storage instance
            lacks the config needed for the calculation — Preseal is then skipped for it, not
            substituted with a fallback.

        Raises
        ------
        NotImplementedError
            If called on a `Silage` subclass that has not overridden this method at all (a
            programmer error — `Bunker`/`Pile`/`Bag` always override it).

        """
        self.om.add_error(
            "Missing Preseal geometry error",
            f"{self.__class__.__name__} has no _preseal_exposed_area_m2 implementation.",
            info_map={"class": self.__class__.__name__, "function": self._preseal_exposed_area_m2.__name__},
        )
        raise NotImplementedError(f"{self.__class__.__name__} must implement _preseal_exposed_area_m2.")

    def _preseal_dry_matter_density_kg_per_m3(self) -> float | None:
        """
        Returns the packed dry-matter density used by the Preseal calculation for this storage class.

        Returns
        -------
        float | None
            Packed dry-matter density (kg DM / m3). A concrete subclass may return ``None`` when
            this storage instance lacks the config needed for the calculation — Preseal is then
            skipped for it, not substituted with a fallback.

        Raises
        ------
        NotImplementedError
            If called on a `Silage` subclass that has not overridden this method at all (a
            programmer error — `Bunker`/`Pile`/`Bag` always override it).

        """
        self.om.add_error(
            "Missing Preseal density error",
            f"{self.__class__.__name__} has no _preseal_dry_matter_density_kg_per_m3 implementation.",
            info_map={
                "class": self.__class__.__name__,
                "function": self._preseal_dry_matter_density_kg_per_m3.__name__,
            },
        )
        raise NotImplementedError(f"{self.__class__.__name__} must implement _preseal_dry_matter_density_kg_per_m3.")

    def _process_infiltration(self, crop: HarvestedCrop, elapsed_days: float) -> float:
        """
        Calculates and applies this crop's Infiltration dry-matter loss for the elapsed period.

        Parameters
        ----------
        crop : HarvestedCrop
            The crop to process infiltration for.
        elapsed_days : float
            Days since infiltration was last processed for this crop.

        Returns
        -------
        float
            Dry-matter loss applied this step (kg).

        Raises
        ------
        NotImplementedError
            If called on a `Silage` subclass that has not defined its own infiltration geometry.

        """
        self.om.add_error(
            "Missing Infiltration geometry error",
            f"{self.__class__.__name__} has no _process_infiltration implementation.",
            info_map={"class": self.__class__.__name__, "function": self._process_infiltration.__name__},
        )
        raise NotImplementedError(f"{self.__class__.__name__} must implement _process_infiltration.")

    def _apply_infiltration_loss(self, crop: HarvestedCrop, dry_matter_loss_kg: float) -> None:
        """
        Applies a computed Infiltration dry-matter loss to a crop's mass and composition.

        Parameters
        ----------
        crop : HarvestedCrop
            The crop to update in place.
        dry_matter_loss_kg : float
            Dry-matter loss to apply (kg).

        Notes
        -----
        Crude protein is deliberately left unchanged here — ``Silostg.for:871-872,978-979`` comment out CP
        dilution specifically for `TOWER`/`BUNKER` ("CRUDE PROTEIN LOSS = DM LOSS"), so CP mass
        tracks dry-matter loss 1:1 instead of concentrating like NDF does. Ash is likewise untouched:
        it is a call-level scalar in the source, never a per-plot diluted field. ``moisture_loss=0.0``
        below is likewise deliberate, not a placeholder: ``Silostg.for:794-984`` models Infiltration as
        gaseous respirable-substrate loss with no moisture-retention term analogous to Preseal's
        ``PRESEAL_WATER_RETENTION_FRACTION`` (Open Decision 8).

        """
        if dry_matter_loss_kg <= 0.0:
            return
        crop.ndf = self.recalculate_nutrient_percentage(crop.ndf, 0.0, dry_matter_loss_kg, crop.dry_matter_mass)
        mass_values = self._calculate_mass_attributes_after_loss(crop, dry_matter_loss_kg, moisture_loss=0.0)
        crop.dry_matter_mass = mass_values["dry_matter_mass"]
        crop.dry_matter_percentage = mass_values["dry_matter_percentage"]

    def process_degradations(self, weather: Weather, time: RufasTime) -> None:
        """
        Processes the ensiled crops' three degradation stages in order — Effluent, then Fermentation
        (the parent ``process_degradations`` implementation), then Infiltration.

        Any crop that has not yet had its Preseal loss finalized (i.e. has not yet been superseded by a
        newer crop via ``receive_crop``) is finalized here first, using the fallback exposure time
        (``PRESEAL_FALLBACK_EXPOSURE_DAYS``) — this covers the newest crop in storage, whose real
        exposure time cannot yet be known.

        Parameters
        ----------
        weather : Weather
            Weather instance containing all weather information for the simulation.
        time : RufasTime
            RufasTime instance tracking the current time of the simulation.

        Notes
        -----
        Infiltration's ``elapsed_days`` (days since Infiltration was last processed for each crop) is
        computed from ``crop.last_time_degraded`` in a dedicated pass *before* ``super()`` runs, not
        inline in a loop after it. ``Storage.process_degradations``/``_calculate_degradation_values``
        (``storage.py``) both reads the OLD ``crop.last_time_degraded`` (to derive weather conditions)
        and, as a side effect, overwrites it to ``time.current_date.date()`` for every crop by the time
        it returns. Computing ``elapsed_days`` after that call would see the just-updated value and
        always measure a zero-day gap, silently freezing Infiltration's accumulated loss. Capturing the
        list here, indexed by ``self.stored``'s iteration order, is safe because neither this method's
        own Effluent loop nor Fermentation adds/removes crops from ``self.stored`` — only
        ``remove_empty_crops`` does that, and it is never called from here.

        """
        info_map = {
            "class": self.__class__.__name__,
            "function": self.process_degradations.__name__,
            "units": MeasurementUnits.KILOGRAMS,
            "simulation_day": time.simulation_day,
            "prefix": self._prefix,
        }
        total_effluent_dry_matter_loss = 0.0
        total_effluent_moisture_loss = 0.0
        for crop in self.stored:
            if not crop.preseal_finalized:
                self._finalize_preseal_loss(crop, PRESEAL_FALLBACK_EXPOSURE_DAYS)
            effluent_loss_values = self._calculate_effluent_loss(crop, time)
            total_effluent_dry_matter_loss += effluent_loss_values["dry_matter_loss"]
            total_effluent_moisture_loss += effluent_loss_values["moisture_loss"]
            crop.non_protein_nitrogen = effluent_loss_values["non_protein_nitrogen"]
            crop.crude_protein_percent = effluent_loss_values["crude_protein_percent"]
            crop.dry_matter_mass = effluent_loss_values["dry_matter_mass"]
            crop.dry_matter_percentage = effluent_loss_values["dry_matter_percentage"]

        self.om.add_variable("total_effluent_dry_matter_loss", total_effluent_dry_matter_loss, info_map)
        self.om.add_variable("total_effluent_moisture_loss", total_effluent_moisture_loss, info_map)

        # Captured before super() runs — see Notes above on why this cannot be computed afterward.
        infiltration_elapsed_days = [
            float((time.current_date.date() - crop.last_time_degraded).days) for crop in self.stored
        ]

        super().process_degradations(weather, time)

        for crop, elapsed_days in zip(self.stored, infiltration_elapsed_days):
            infiltration_loss_kg = self._process_infiltration(crop, elapsed_days)
            self._apply_infiltration_loss(crop, infiltration_loss_kg)

    def project_degradations(
        self, crops: list[HarvestedCrop], weather: Weather, time: RufasTime
    ) -> list[HarvestedCrop]:
        """
        Projects the state of crops currently stored at a given future date.

        Parameters
        ----------
        crops : list[HarvestedCrop]
            List of ``HarvestedCrop`` objects to project degradations for.
        weather : Weather
            Weather instance containing all weather information for the simulation.
        time : RufasTime
            RufasTime instance containing the date at which the state of the stored crops should be projected.

        Returns
        -------
        list[HarvestedCrop]
            Crops in the state they are projected to be in at the given date.

        Notes
        -----
        ``temperature``, ``preseal_finalized``, ``infiltration_cumulative_loss_kg``, and
        ``infiltration_max_loss_kg`` are all ``init=False`` fields on `HarvestedCrop`, so
        `dataclasses.replace` reruns `HarvestedCrop.__post_init__`, which unconditionally resets all
        four to their as-newly-stored defaults. Copied back from the pre-``replace`` crop here, same
        pattern `Storage.project_degradations` already uses for `last_time_degraded`.

        """
        crops_projected_with_effluent_loss: list[HarvestedCrop] = []
        for crop in crops:
            effluent_loss_values: dict[str, Any] = self._calculate_effluent_loss(crop, time)
            del effluent_loss_values["dry_matter_loss"]
            del effluent_loss_values["moisture_loss"]
            projected_crop = replace(crop, **effluent_loss_values)
            projected_crop.temperature = crop.temperature
            projected_crop.preseal_finalized = crop.preseal_finalized
            projected_crop.infiltration_cumulative_loss_kg = crop.infiltration_cumulative_loss_kg
            projected_crop.infiltration_max_loss_kg = crop.infiltration_max_loss_kg
            crops_projected_with_effluent_loss.append(projected_crop)

        return super().project_degradations(crops_projected_with_effluent_loss, weather, time)

    def _calculate_effluent_loss(self, crop: HarvestedCrop, time: RufasTime) -> dict[str, float]:
        """
        Calculates the attributes of a crop after effluent loss.

        Parameters
        ----------
        crop : HarvestedCrop
            ``HarvestedCrop`` to calculate effluent losses from.
        time : RufasTime
            RufasTime instance tracking the current time of the simulation.

        Returns
        -------
        dict[str, float]
            Mapping of the crop's attributes to their values after effluent loss.

        """
        post_loss_values = {
            "dry_matter_mass": crop.dry_matter_mass,
            "dry_matter_percentage": crop.dry_matter_percentage,
            "non_protein_nitrogen": crop.non_protein_nitrogen,
            "crude_protein_percent": crop.crude_protein_percent,
            "dry_matter_loss": 0.0,
            "moisture_loss": 0.0,
        }
        days_of_effluent_to_process = self.calculate_days_of_effluent_loss_to_process(crop, time)
        if days_of_effluent_to_process == 0:
            return post_loss_values

        crop.estimated_maximum_effluent = crop.estimate_maximum_effluent()
        dry_matter_loss = self.calculate_dry_matter_loss_to_effluent(
            crop.estimated_maximum_effluent, days_of_effluent_to_process
        )
        moisture_loss = self.calculate_moisture_loss_to_effluent(
            crop.estimated_maximum_effluent, days_of_effluent_to_process
        )

        dry_matter_loss_frac = dry_matter_loss / crop.dry_matter_mass
        post_loss_values["non_protein_nitrogen"] = self.calculate_non_protein_nitrogen_after_effluent_loss(
            crop.non_protein_nitrogen, crop.crude_protein_percent, dry_matter_loss_frac
        )

        post_loss_values["crude_protein_percent"] = self.calculate_crude_protein_after_effluent_loss(
            crop.crude_protein_percent, dry_matter_loss_frac
        )

        mass_attributes = self._calculate_mass_attributes_after_loss(crop, dry_matter_loss, moisture_loss)
        post_loss_values.update(mass_attributes | {"dry_matter_loss": dry_matter_loss, "moisture_loss": moisture_loss})
        return post_loss_values

    def calculate_days_of_effluent_loss_to_process(self, crop: HarvestedCrop, time: RufasTime) -> int:
        """
        Calculates the number of days of effluent loss to process for an ensiled crop.

        Parameters
        ----------
        crop : HarvestedCrop
            Ensiled crop that is being degraded.
        time : RufasTime
            RufasTime instance containing the current time of the simulation.

        Returns
        -------
        int
            Number of days to calculate effluent loss for.

        Notes
        -----
        Effluent loss is fixed at 10 days if the crop is still within the first 10 days of storage. After that period,
        it is calculated as the number of days since the last degradation.

        """
        days_since_storage = (time.current_date.date() - crop.storage_time).days

        if days_since_storage <= 10:
            return max(0, min(10, (time.current_date.date() - crop.last_time_degraded).days))
        else:
            return (time.current_date.date() - crop.last_time_degraded).days

    def calculate_dry_matter_loss_to_effluent(self, estimated_maximum_effluent: float, days_of_loss: int) -> float:
        """
        Calculates the dry matter loss to effluent.

        Parameters
        ----------
        estimated_maximum_effluent : float
            The estimated maximum effluent.
        days_of_loss : int
            The number of days effluent loss will be calculated for.

        Returns
        -------
        float
            The amount of dry matter lost to effluent (kg).

        References
        ----------
        Feed Storage Scientific Documentation, equations FS.SIL.4, FS.SIL.6, and FS.SIL.7.

        """
        return estimated_maximum_effluent * days_of_loss * DRY_MATTER_FRACTION_OF_EFFLUENT / EFFLUENT_CONSTRAINER

    def calculate_moisture_loss_to_effluent(self, estimated_maximum_effluent: float, days_of_loss: int) -> float:
        """
        Calculates the moisture loss to effluent.

        Parameters
        ----------
        estimated_maximum_effluent : float
            The estimated maximum effluent.
        days_of_loss : int
            The number of days effluent loss will be calculated for.

        Returns
        -------
        float
            The amount of moisture lost to effluent (kg).

        References
        ----------
        Feed Storage Scientific Documentation, equation FS.SIL.5.

        """
        return estimated_maximum_effluent * days_of_loss * (1 - DRY_MATTER_FRACTION_OF_EFFLUENT) / EFFLUENT_CONSTRAINER

    def calculate_non_protein_nitrogen_after_effluent_loss(
        self, initial_non_protein_nitrogen: float, initial_crude_protein: float, loss_fraction: float
    ) -> float:
        """
        Calculates the percentage of non-protein nitrogen in a stored crop after losing dry matter to effluent.

        Parameters
        ----------
        initial_non_protein_nitrogen : float
            Percentage of non-protein nitrogen in the crop before dry matter loss occurred.
        initial_crude_protein : float
            Percentage of crude protein in the crop before dry matter loss occurred.
        loss_fraction : float
            Fraction of dry matter that was lost to effluent.

        Returns
        -------
        float
            Percentage of non-protein nitrogen remaining in the stored crop.

        References
        ----------
        Feed Storage Scientific Documentation, equation FS.NUT.1.

        """
        if loss_fraction == 0.0:
            return initial_non_protein_nitrogen

        npn_fraction = initial_non_protein_nitrogen * GeneralConstants.PERCENTAGE_TO_FRACTION
        cp_fraction = initial_crude_protein * GeneralConstants.PERCENTAGE_TO_FRACTION

        numerator = npn_fraction * cp_fraction - 0.3 * loss_fraction
        denominator = cp_fraction - 0.3 * loss_fraction

        new_npn_fraction = numerator / denominator
        new_npn_percentage = new_npn_fraction * GeneralConstants.FRACTION_TO_PERCENTAGE
        return max(0.0, new_npn_percentage)

    def calculate_crude_protein_after_effluent_loss(self, initial_crude_protein: float, loss_fraction: float) -> float:
        """
        Calculates the percentage of crude protein in a stored crop after losing dry matter to effluent.

        Parameters
        ----------
        initial_crude_protein : float
            Percentage of crude protein in the crop before dry matter loss occurred.
        loss_fraction : float
            Fraction of dry matter that was lost to effluent.

        Returns
        -------
        float
            Percentage of crude protein remaining in the stored crop.

        References
        ----------
        Feed Storage Scientific Documentation, equation FS.NUT.1.

        """
        if loss_fraction == 0.0:
            return initial_crude_protein

        new_fraction = (initial_crude_protein * GeneralConstants.PERCENTAGE_TO_FRACTION - 0.3 * loss_fraction) / (
            1 - loss_fraction
        )
        new_percentage = new_fraction * GeneralConstants.FRACTION_TO_PERCENTAGE
        return max(0.0, new_percentage)


def _read_optional_positive_config_float(
    config: dict[str, str | float | list[str]], key: str, class_name: str
) -> float | None:
    """
    Reads and validates an optional positive float from a storage config dict.

    Parameters
    ----------
    config : dict[str, str | float | list[str]]
        Configuration dictionary for the storage.
    key : str
        The config key to read.
    class_name : str
        Name of the calling storage class, for the error message.

    Returns
    -------
    float | None
        The validated, positive config value, or ``None`` if the key is absent. Existing farm
        configs that predate the Preseal geometry/density fields are unaffected: a storage
        missing one or more of them simply skips Preseal (see `Silage._finalize_preseal_loss`)
        rather than failing to construct.

    Raises
    ------
    ValueError
        If the key is present but its value is not a positive number.

    """
    value = config.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ValueError(f"{class_name} '{key}' must be a positive number when provided, got {value!r}.")
    return float(value)


class Bunker(Silage):
    """
    Represents the Bunker type of Silage storage.

    Attributes
    ----------
    width_m : float | None
        Bunker width (m). Optional — omitting it (or `height_m` or
        `dry_matter_density_kg_per_m3`) skips Preseal for this storage, no reference-table
        fallback is substituted.
    height_m : float | None
        Bunker wall height (m). Optional, same as `width_m`.
    dry_matter_density_kg_per_m3 : float | None
        Packed dry-matter density (kg DM / m3). Optional, same as `width_m`.

    """

    def __init__(self, config: dict[str, str | float | list[str]]) -> None:
        super().__init__(config)
        self.width_m = _read_optional_positive_config_float(config, "width_m", self.__class__.__name__)
        self.height_m = _read_optional_positive_config_float(config, "height_m", self.__class__.__name__)
        self.dry_matter_density_kg_per_m3 = _read_optional_positive_config_float(
            config, "dry_matter_density_kg_per_m3", self.__class__.__name__
        )

    def _preseal_exposed_area_m2(self) -> float | None:
        """
        Exposed surface area for the Preseal phase, accounting for a 50% filling grade.

        Returns
        -------
        float | None
            Exposed area (m2), or ``None`` if `width_m`/`height_m` isn't configured — Preseal is
            then skipped for this storage (see `Silage._finalize_preseal_loss`).

        Notes
        -----
        ``Silostg.for:329``: ``EXPAR = SQRT(5) * DIM1 * DIM2``. Buckmaster et al. (1989), p.1144:
        "Estimation of surface area is based on a 50% grade during filling."

        """
        if self.width_m is None or self.height_m is None:
            return None
        return math.sqrt(5.0) * self.width_m * self.height_m

    def _preseal_dry_matter_density_kg_per_m3(self) -> float | None:
        """
        Packed dry-matter density for the Preseal calculation.

        Returns
        -------
        float | None
            ``self.dry_matter_density_kg_per_m3``, set from config in ``__init__``, or ``None``
            if not configured.

        """
        return self.dry_matter_density_kg_per_m3

    def _process_infiltration(self, crop: HarvestedCrop, elapsed_days: float) -> float:
        """See `Silage._process_infiltration`. Dispatches to the vertical-front Bunker/Pile math, or
        skips (returns 0.0) if geometry/density isn't configured — mirrors `_preseal_exposed_area_m2`'s
        own None-skip pattern (Open Decision 7) rather than requiring the protected
        `example_feed_storage_configs.json` fixture's legacy `size`-only entries to be edited."""
        if self.width_m is None or self.height_m is None or self.dry_matter_density_kg_per_m3 is None:
            return 0.0
        return calculate_bunker_infiltration_loss(
            crop, elapsed_days, self.__class__.__name__, self.width_m, self.height_m, self.dry_matter_density_kg_per_m3
        )


class Pile(Silage):
    """
    Represents the Pile type of Silage storage.

    Attributes
    ----------
    width_m : float | None
        Pile width (m). Optional — omitting it (or `height_m` or
        `dry_matter_density_kg_per_m3`) skips Preseal for this storage, no reference-table
        fallback is substituted.
    height_m : float | None
        Pile height (m). Optional, same as `width_m`.
    dry_matter_density_kg_per_m3 : float | None
        Packed dry-matter density (kg DM / m3). Optional, same as `width_m`.

    """

    def __init__(self, config: dict[str, str | float | list[str]]) -> None:
        super().__init__(config)
        self.width_m = _read_optional_positive_config_float(config, "width_m", self.__class__.__name__)
        self.height_m = _read_optional_positive_config_float(config, "height_m", self.__class__.__name__)
        self.dry_matter_density_kg_per_m3 = _read_optional_positive_config_float(
            config, "dry_matter_density_kg_per_m3", self.__class__.__name__
        )

    def _preseal_exposed_area_m2(self) -> float | None:
        """
        Exposed surface area for the Preseal phase, accounting for a 50% filling grade.

        Returns
        -------
        float | None
            Exposed area (m2), or ``None`` if `width_m`/`height_m` isn't configured — Preseal is
            then skipped for this storage (see `Silage._finalize_preseal_loss`).

        Notes
        -----
        ``Silostg.for:329``: ``EXPAR = SQRT(5) * DIM1 * DIM2``. Buckmaster et al. (1989), p.1144:
        "Estimation of surface area is based on a 50% grade during filling."

        """
        if self.width_m is None or self.height_m is None:
            return None
        return math.sqrt(5.0) * self.width_m * self.height_m

    def _preseal_dry_matter_density_kg_per_m3(self) -> float | None:
        """
        Packed dry-matter density for the Preseal calculation.

        Returns
        -------
        float | None
            ``self.dry_matter_density_kg_per_m3``, set from config in ``__init__``, or ``None``
            if not configured.

        """
        return self.dry_matter_density_kg_per_m3

    def _process_infiltration(self, crop: HarvestedCrop, elapsed_days: float) -> float:
        """See `Silage._process_infiltration`. Dispatches to the vertical-front Bunker/Pile math, or
        skips (returns 0.0) if geometry/density isn't configured — mirrors `_preseal_exposed_area_m2`'s
        own None-skip pattern (Open Decision 7) rather than requiring the protected
        `example_feed_storage_configs.json` fixture's legacy `size`-only entries to be edited."""
        if self.width_m is None or self.height_m is None or self.dry_matter_density_kg_per_m3 is None:
            return 0.0
        return calculate_bunker_infiltration_loss(
            crop, elapsed_days, self.__class__.__name__, self.width_m, self.height_m, self.dry_matter_density_kg_per_m3
        )


class Bag(Silage):
    """
    Represents the Bag type of Silage storage.

    Attributes
    ----------
    diameter_m : float | None
        Bag diameter (m). Optional — omitting it (or `dry_matter_density_kg_per_m3`) skips
        Preseal for this storage, no reference-table fallback is substituted.
    dry_matter_density_kg_per_m3 : float | None
        Packed dry-matter density (kg DM / m3). Optional, same as `diameter_m`.

    """

    def __init__(self, config: dict[str, str | float | list[str]]) -> None:
        super().__init__(config)
        self.diameter_m = _read_optional_positive_config_float(config, "diameter_m", self.__class__.__name__)
        self.dry_matter_density_kg_per_m3 = _read_optional_positive_config_float(
            config, "dry_matter_density_kg_per_m3", self.__class__.__name__
        )

    def _preseal_exposed_area_m2(self) -> float | None:
        """
        Exposed surface area for the Preseal phase — the bag's circular cross-section.

        Returns
        -------
        float | None
            Exposed area (m2), or ``None`` if `diameter_m` isn't configured — Preseal is then
            skipped for this storage (see `Silage._finalize_preseal_loss`).

        Notes
        -----
        Bags reuse tower relationships per the IFSM Reference Manual (p.76-77); ``Silostg.for:310-313``'s
        tower branch sets ``EXPAR = CSA = pi * RAD**2``.

        """
        if self.diameter_m is None:
            return None
        radius_m = self.diameter_m / 2.0
        return math.pi * radius_m**2

    def _preseal_dry_matter_density_kg_per_m3(self) -> float | None:
        """
        Packed dry-matter density for the Preseal calculation.

        Returns
        -------
        float | None
            ``self.dry_matter_density_kg_per_m3``, set from config in ``__init__``, or ``None``
            if not configured.

        """
        return self.dry_matter_density_kg_per_m3

    def _process_infiltration(self, crop: HarvestedCrop, elapsed_days: float) -> float:
        """See `Silage._process_infiltration`. Dispatches to the radial-front Bag math, or skips
        (returns 0.0) if geometry/density isn't configured — same None-skip pattern as Bunker/Pile
        (Open Decision 7)."""
        if self.diameter_m is None or self.dry_matter_density_kg_per_m3 is None:
            return 0.0
        return calculate_bag_infiltration_loss(crop, elapsed_days, self.diameter_m, self.dry_matter_density_kg_per_m3)
