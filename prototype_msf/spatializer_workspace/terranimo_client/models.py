"""
models.py — Terranimo API client, MSFourrager

Typed return values for the calculation endpoints.

Every field name carries its unit as a suffix, and every value is stored
exactly as the API returned it. This module performs **no unit conversion**:
the Terranimo unit convention is still being clarified with Stefan Gfeller
(see MSF-Notes/Terranimo/00-Terranimo-Status-Consolidated-2026-09-10.md), and
converting on an unconfirmed assumption would fabricate information.

Where a suffix reflects only what the OpenAPI spec *declares* rather than what
has been confirmed, the docstring says so. ``raw_response`` always carries the
full decoded body, so nothing is lost to the typed view.

Schema references are to the OpenAPI 3.0.4 spec:
    https://services.terranimo.world/swagger/v1/swagger.json
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Final, Tuple

logger = logging.getLogger(__name__)

#: Values of the ``EResult`` enum, used by the compaction-risk endpoint.
#: Note the spec also defines ``ESoilStrengthSoilStressEvaluationResult`` with
#: capitalised members ("Good"/"Ok"/"Bad") — a different enum on a different
#: endpoint, and a known spec inconsistency.
VERDICT_VALUES: Final[Tuple[str, ...]] = ("good", "ok", "bad")


def _check_number(value: Any, name: str, owner: str) -> None:
    """
    Raise ``TypeError`` unless ``value`` is a real number.

    ``bool`` is rejected explicitly: it is a subclass of ``int`` in Python, so
    a stray ``True`` would otherwise pass silently as ``1``.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(
            f"{owner}.{name} must be a number, got {type(value).__name__}: {value!r}"
        )


def _check_mapping(value: Any, name: str, owner: str) -> None:
    """Raise ``TypeError`` unless ``value`` is a dict."""
    if not isinstance(value, dict):
        raise TypeError(
            f"{owner}.{name} must be a dict, got {type(value).__name__}: {value!r}"
        )


@dataclass
class VanGenuchtenWaterContentResult:
    """
    Water content computed from matric potential.

    Endpoint: ``/calculations/calculate_mualem_van_genuchten_for_water_content``
    Response schema: ``MualemVanGenuchtenForWaterContentCalculationResponse``

    Attributes
    ----------
    water_content_pct
        The schema's ``result`` field. The request schema declares
        ``waterContent`` as ``[%]``, and the response's ``result`` carries the
        description "Result of the calculation" with **no unit stated**.
        Stefan Gfeller confirmed on 2026-09-15 that it is a volumetric
        fraction in **m³/m³**, not a percentage — so the ``_pct`` suffix is a
        misnomer. Kept for backward compatibility; not renamed.
    raw_response
        Full decoded response body.
    """

    water_content_pct: float
    raw_response: Dict[str, Any] = field(repr=False)

    def __post_init__(self) -> None:
        _check_number(self.water_content_pct, "water_content_pct", type(self).__name__)
        _check_mapping(self.raw_response, "raw_response", type(self).__name__)


@dataclass
class VanGenuchtenMatricPotentialResult:
    """
    Matric potential computed from water content.

    Endpoint: ``/calculations/calculate_mualem_van_genuchten_for_matric_potential``
    Response schema: ``MualemVanGenuchtenForMatricPotentialCalculationResponse``

    Used as a coherence oracle: it tells you which matric potential actually
    corresponds to a given water content for a given soil, so a caller can
    check that the two are not physically contradictory before feeding both
    into the precompression endpoint.

    Attributes
    ----------
    matric_potential
        The schema's ``result`` field. **Deliberately carries no unit
        suffix.** The spec gives the response ``result`` no unit. Stefan
        Gfeller confirmed on 2026-09-15 that matric-potential *inputs* are in
        bar on every calculate endpoint; it is not established that this
        covers this output, and read as bar the values measured on
        2026-09-10 (81-1902 for 25 % water content) would be implausible.
        Until confirmed, naming this field for a unit would assert something
        unverified.
    raw_response
        Full decoded response body.
    """

    matric_potential: float
    raw_response: Dict[str, Any] = field(repr=False)

    def __post_init__(self) -> None:
        _check_number(self.matric_potential, "matric_potential", type(self).__name__)
        _check_mapping(self.raw_response, "raw_response", type(self).__name__)


@dataclass
class PrecompressionResult:
    """
    Precompression stress of a soil — endpoint 1 of the compaction chain.

    Endpoint: ``/calculations/calculate_precompression_of_soil``
    Response schema: ``SoilPrecompressionResponse``

    Attributes
    ----------
    precompression_bar
        The schema's ``preCompressionOfSoil`` field, described as
        "Pre compression of soil [bar]". The suffix records what the spec
        declares; the actual output unit is still unconfirmed (see the
        2026-09-16 replay of the August payloads).
    raw_response
        Full decoded response body.

    Notes
    -----
    The compaction chain needs this value **twice** — once for the top layer
    and once for the subsoil — obtained by calling the endpoint with each
    layer's bulk density. The ``topSoil`` flag does not discriminate them:
    testing on 2026-08-26 showed identical output for ``True`` and ``False``,
    with only ``bulkDensity`` changing the result.
    """

    precompression_bar: float
    raw_response: Dict[str, Any] = field(repr=False)

    def __post_init__(self) -> None:
        _check_number(self.precompression_bar, "precompression_bar", type(self).__name__)
        _check_mapping(self.raw_response, "raw_response", type(self).__name__)


@dataclass
class TyreCompactionResult:
    """
    Compaction-risk decision for a wheeled machine — endpoint 2 of the chain.

    Endpoint: ``/calculations/calculate_tyre_for_compaction_risc_decision``
    Response schema: ``CalculateWheelForCompactionRiscDecisionResponse``

    Attributes
    ----------
    soil_stress_bar
        The schema's ``soilStress`` field, described as "Soil stress [bar]".
    soil_strength_bar
        The schema's ``soilStrength`` field, described as "Soil strength [bar]".
    verdict
        The schema's ``result`` field, an ``EResult`` enum member:
        ``"good"``, ``"ok"`` or ``"bad"``.
    raw_response
        Full decoded response body.

    Notes
    -----
    **Use the verdict, not the absolute values.** The stress/strength
    comparison is internally consistent regardless of which pressure unit the
    API actually means, so the categorical result is trustworthy while the
    absolute numbers are not. Per the consolidated status note, absolute
    stress and strength must not be surfaced to producers.

    An unrecognised verdict is logged as a warning and kept as-is rather than
    rejected: a live API returning a new enum member should not crash a
    pipeline that only needs the raw value.
    """

    soil_stress_bar: float
    soil_strength_bar: float
    verdict: str
    raw_response: Dict[str, Any] = field(repr=False)

    def __post_init__(self) -> None:
        owner = type(self).__name__
        _check_number(self.soil_stress_bar, "soil_stress_bar", owner)
        _check_number(self.soil_strength_bar, "soil_strength_bar", owner)
        _check_mapping(self.raw_response, "raw_response", owner)

        if not isinstance(self.verdict, str):
            raise TypeError(
                f"{owner}.verdict must be a str, "
                f"got {type(self.verdict).__name__}: {self.verdict!r}"
            )
        if self.verdict not in VERDICT_VALUES:
            logger.warning(
                "Unrecognised verdict %r; expected one of %s. Value kept as-is.",
                self.verdict,
                VERDICT_VALUES,
            )

    @property
    def is_workable(self) -> bool:
        """
        ``True`` when the verdict is ``"good"`` or ``"ok"``.

        Convenience for the common gate. Anything unrecognised is treated as
        not workable, which fails safe.
        """
        return self.verdict in ("good", "ok")
