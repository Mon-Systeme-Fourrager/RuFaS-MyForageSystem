"""
compaction.py — Spatializer v0.2 evaluators, MSFourrager

Factor 1 of 4: compaction risk, evaluated through the Terranimo REST API.

Scaling — discrete, deliberately
--------------------------------
The score is the Terranimo categorical verdict mapped to 0.0 / 0.5 / 1.0.
This is **not** the continuous 7-point ratio scale drafted in Décision 5 on
2026-09-09. That scale needs trustworthy absolute ``soilStress`` and
``soilStrength`` values, and those depend on a unit convention that is still
unresolved with Stefan Gfeller. The categorical verdict, by contrast, is
internally consistent whichever pressure unit the API means, because it comes
from comparing stress against strength on the same scale.

References:
    MSF-Notes/Terranimo/00-Terranimo-Status-Consolidated-2026-09-10.md
        "Working assumption for MSF integration (until unit re-validation)"
    MSF-Notes/Spatializer/2026-09-03-Spatializer-v0.2-placeholders-proposal.md
        Décision 5, Factor 1 — carries the SUPERSEDED note pointing here.

Do not surface ``soil_stress_bar`` / ``soil_strength_bar`` to producers. They
are carried on the result for debugging and for the eventual upgrade to the
continuous scale, not for display.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Final, Optional

from terranimo_client import TerranimoClient
from terranimo_client.models import PrecompressionResult, TyreCompactionResult

from .base import EvaluationResult

logger = logging.getLogger(__name__)


#: Verdict to score mapping (discrete, per Terranimo Status Consolidated
#: 2026-09-10). Keys are the ``EResult`` enum members declared in the OpenAPI
#: spec. Favourable-high, matching the Spatializer polarity convention.
VERDICT_TO_SCORE: Final[Dict[str, float]] = {
    "good": 1.0,
    "ok": 0.5,
    "bad": 0.0,
}


@dataclass
class SoilInputs:
    """
    Soil properties needed for compaction evaluation.

    Bulk density values must be provided by the caller.
    The evaluator does not hardcode defaults because:
    - Values vary by field location (Quebec has diverse soils)
    - Perreault et al. 2022 means (1.33 A / 1.50 B) apply only to
      Montérégie region and are not representative of other regions
    - Production values will come from IRDA pedological database
      via a Supabase reference table (RT-XX ref_soil_pedology,
      proposed architecture)

    For testing, callers may pass literature values with explicit
    source citation.

    Attributes
    ----------
    clay_pct
        Clay content ``[%]``.
    silt_pct
        Silt content ``[%]``.
    organic_matter_pct
        Organic matter content ``[%]``.
    bulk_density_g_per_cm3
        Bulk density ``[g/cm3]`` of the A horizon (topsoil). Required.
    bulk_density_subsoil_g_per_cm3
        Bulk density ``[g/cm3]`` of the B horizon (subsoil). Required.
        Drives the second precompression call, whose result becomes
        ``preCompressionOfSoil`` (layer 4) on the tyre endpoint — and, as
        observed live on 2026-09-10, the returned ``soilStrength``.
    water_content_pct
        Water content ``[%]``, from the RUFAS daily state. Applied to both
        layers, as in the August chain.
    matric_potential
        Matric potential in **bar** — confirmed by Stefan Gfeller (BFH) on
        2026-09-15, matching the spec's ``[bar]`` declaration and the
        2026-09-10 numerical check. Passed to the API verbatim, unconverted.
        (Field name kept unsuffixed so existing callers do not break.)
    top_soil
        Topsoil flag sent to the API, on **both** precompression calls.
        Retained for fidelity to the request schema; bulk density is the
        dominant discriminator between layers.
    """

    clay_pct: float
    silt_pct: float
    organic_matter_pct: float
    bulk_density_g_per_cm3: float              # A horizon (topsoil)
    bulk_density_subsoil_g_per_cm3: float      # B horizon (subsoil) — NEW, required
    water_content_pct: float
    matric_potential: float
    top_soil: bool = True


@dataclass
class TractorInputs:
    """
    Tractor / tyre properties from producer input.

    Attributes
    ----------
    tyre_uid
        Terranimo tyre UID from the catalog. The catalog supplies width,
        diameter and static loaded radius internally, which is what reduced
        the machinery blocker to a small number of producer-supplied values.
    tyre_load_kg
        Wheel load ``[kg]``.
    tyre_pressure_bar
        Actual inflation pressure ``[bar]``.
    tyre_pressure_recommended_bar
        Recommended inflation pressure ``[bar]``. Ideally obtained from
        ``calculate_recommended_tyre_pressure``, which this client does not
        yet wrap; until then the caller supplies it.
    recent_tillage
        Whether the field was recently tilled.
    """

    tyre_uid: str
    tyre_load_kg: int
    tyre_pressure_bar: float
    tyre_pressure_recommended_bar: float
    recent_tillage: bool = False


@dataclass
class CompactionResult(EvaluationResult):
    """
    Compaction evaluation result with API context.

    Inherits ``score``, ``verdict`` and ``context`` from
    :class:`~.base.EvaluationResult`.

    Attributes
    ----------
    precompression_topsoil_bar
        ``preCompressionOfSoil`` from the topsoil precompression call, sent
        on to the tyre endpoint as ``preCompressionOfSoilTopLayer``.
    precompression_subsoil_bar
        ``preCompressionOfSoil`` from the subsoil precompression call, sent
        on to the tyre endpoint as ``preCompressionOfSoil`` (layer 4).
    soil_stress_bar
        ``soilStress`` from endpoint 2. **Not for producer display.**
    soil_strength_bar
        ``soilStrength`` from endpoint 2. **Not for producer display.**
        Observed live on 2026-09-10 to equal the precompression value passed
        in for layer 4, to full float precision.
    api_verdict
        Raw ``EResult`` value returned by Terranimo, before mapping.
    """

    precompression_topsoil_bar: Optional[float] = None    # NEW (was precompression_bar)
    precompression_subsoil_bar: Optional[float] = None    # NEW
    soil_stress_bar: Optional[float] = None
    soil_strength_bar: Optional[float] = None
    api_verdict: Optional[str] = None


class CompactionEvaluator:
    """
    Evaluates compaction risk for a soil + tractor combination on a specific
    day using the Terranimo API.

    Reference:
    - MSF-Notes/Terranimo/00-Terranimo-Status-Consolidated-2026-09-10.md
    - Décision 5, Factor 1 (compaction) in the placeholders proposal

    Current implementation uses discrete verdict mapping
    (good/ok/bad -> 1.0/0.5/0.0) while unit ambiguity with Terranimo is
    pending resolution. The continuous ratio-based scale is documented as a
    future upgrade.

    Each :meth:`evaluate` call issues **three** HTTP requests: two
    ``calculate_precompression_of_soil`` (A horizon and B horizon bulk
    density) plus one ``calculate_tyre_for_compaction_risc_decision``.
    Terranimo has no batch endpoint, so a per-zone, per-day sweep multiplies
    accordingly.

    The two precompression calls differ **only** in bulk density. Bulk
    density is the dominant discriminator between layers; the ``topSoil``
    flag has minimal effect — testing on 2026-08-26 returned identical
    values for ``True`` and ``False`` across three input pairs. This matches
    the chain Stefan described and the approach used in the August
    2026-08-26 session.

    Bulk densities are **not** defaulted anywhere in this module. The caller
    supplies both, explicitly. In production they are expected to come from
    the IRDA Quebec pedological database via a Supabase reference table
    (RT-XX ``ref_soil_pedology``, proposed architecture); in tests they come
    from literature values with an explicit source citation. See
    :class:`SoilInputs`.
    """

    def __init__(self, terranimo_client: TerranimoClient) -> None:
        """
        Initialize with a configured Terranimo client.

        Parameters
        ----------
        terranimo_client
            An authenticated :class:`~terranimo_client.TerranimoClient`. The
            evaluator does not construct one itself, so credentials and
            timeout stay the caller's concern and the evaluator stays
            testable against a stub.
        """
        self.client: TerranimoClient = terranimo_client

    def evaluate(
        self,
        soil: SoilInputs,
        tractor: TractorInputs,
    ) -> CompactionResult:
        """
        Compute the compaction score for one day.

        Executes the full Terranimo chain:

        1. ``calculate_precompression_of_soil``
        2. ``calculate_tyre_for_compaction_risc_decision``

        Parameters
        ----------
        soil
            Soil state for the zone on the day being evaluated.
        tractor
            Machine configuration for the planned operation.

        Returns
        -------
        CompactionResult
            ``score`` in {0.0, 0.5, 1.0}, plus the raw verdict and the
            absolute values for debugging.

        Raises
        ------
        TerranimoError
            Or a subclass, if either API call fails.
        ValueError
            If the API returns a verdict outside the known ``EResult`` set.
            This fails loudly on purpose: silently scoring an unrecognised
            verdict would put an unvalidated number into the geometric mean.
        """
        # Step 1a: precompression for topsoil layer (A horizon)
        precomp_top: PrecompressionResult = self.client.precompression(
            water_content_pct=soil.water_content_pct,
            matric_potential_bar=soil.matric_potential,  # bar, confirmed by Stefan 2026-09-15
            clay_pct=soil.clay_pct,
            silt_pct=soil.silt_pct,
            organic_matter_pct=soil.organic_matter_pct,
            bulk_density_g_per_cm3=soil.bulk_density_g_per_cm3,
            top_soil=soil.top_soil,
        )

        # Step 1b: precompression for subsoil layer (B horizon)
        # Note: top_soil flag kept per input — Terranimo documentation observation
        # is that this flag has minimal effect vs bulk_density which is the
        # dominant discriminator between layers.
        # Consistent with August 2026-08-26 chain approach.
        precomp_sub: PrecompressionResult = self.client.precompression(
            water_content_pct=soil.water_content_pct,
            matric_potential_bar=soil.matric_potential,  # bar, confirmed by Stefan 2026-09-15
            clay_pct=soil.clay_pct,
            silt_pct=soil.silt_pct,
            organic_matter_pct=soil.organic_matter_pct,
            bulk_density_g_per_cm3=soil.bulk_density_subsoil_g_per_cm3,  # SUBSOIL BD
            top_soil=soil.top_soil,
        )

        # Step 2: tyre compaction decision with DISTINCT layer values
        tyre_result: TyreCompactionResult = self.client.tyre_for_compaction(
            tyre_uid=tractor.tyre_uid,
            tyre_load_kg=tractor.tyre_load_kg,
            tyre_pressure_bar=tractor.tyre_pressure_bar,
            tyre_pressure_recommended_bar=tractor.tyre_pressure_recommended_bar,
            recent_tillage=tractor.recent_tillage,
            precompression_top_layer_bar=precomp_top.precompression_bar,   # topsoil
            precompression_bar=precomp_sub.precompression_bar,             # subsoil
            matric_potential_bar=soil.matric_potential,  # bar, confirmed by Stefan 2026-09-15
        )

        # Map verdict to discrete score
        api_verdict = tyre_result.verdict
        if api_verdict not in VERDICT_TO_SCORE:
            raise ValueError(
                f"Unknown verdict from Terranimo API: {api_verdict!r}. "
                f"Expected one of {list(VERDICT_TO_SCORE.keys())}"
            )

        score = VERDICT_TO_SCORE[api_verdict]
        logger.info(
            "Compaction evaluated: verdict=%s -> score=%.1f (stress=%s, strength=%s)",
            api_verdict,
            score,
            tyre_result.soil_stress_bar,
            tyre_result.soil_strength_bar,
        )

        return CompactionResult(
            score=score,
            verdict=api_verdict,  # exposed as high-level verdict
            api_verdict=api_verdict,
            precompression_topsoil_bar=precomp_top.precompression_bar,
            precompression_subsoil_bar=precomp_sub.precompression_bar,
            soil_stress_bar=tyre_result.soil_stress_bar,
            soil_strength_bar=tyre_result.soil_strength_bar,
            context={
                "raw_precompression_topsoil_response": precomp_top.raw_response,
                "raw_precompression_subsoil_response": precomp_sub.raw_response,
                "raw_tyre_response": tyre_result.raw_response,
            },
        )
