"""
runoff.py — Spatializer v0.3 evaluators, MSFourrager

Factor 3 of 4: runoff risk, from two field-level inputs.

MVP scope (design decisions confirmed 2026-09-16)
-------------------------------------------------
- Two factors: slope ``[%]`` and soil saturation ``[fraction, 0-1]``.
- Final score is the geometric mean of the per-factor scores, the same
  aggregation the Spatializer uses across evaluators (Adamchuk et al. 2011,
  Geoderma 163:63-73; see ``base.py``).
- No REA input (skipped for now, per Maxime).
- No categorical stops.
- No precipitation input: rain is handled by the Weather evaluator, so it is
  deliberately absent here to avoid double-counting.
- Extension hook for future factors (hydrography, vegetation, ...): see
  :meth:`RunoffEvaluator._extra_factors`.
- Follows the ``base.py`` contract like Compaction and Weather: inputs are
  passed to :meth:`RunoffEvaluator.evaluate` as a :class:`RunoffInputs`, and
  the result is a :class:`RunoffResult`, an ``EvaluationResult`` subclass.

Placeholder scoring — read before using the numbers
---------------------------------------------------
Both per-factor scoring functions are **linear placeholders**. None of their
breakpoints come from the literature. In particular, the 25 % slope at which
the slope score reaches 0.0 is an MVP placeholder chosen to make the pipeline
runnable, **not** a literature threshold. Replace both functions with
literature-backed ones (e.g. SCS Curve Number, MUSLE) before any score from
this module is shown to producers.

The verdict cut-offs (0.3 and 0.7, placed around the default workability
threshold of 0.5) are likewise design choices, not literature values.

Inputs are plain floats. This module does not import RUFAS.
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Final, List, Optional

from .base import EvaluationResult

__version__ = "0.1.0-alpha"

#: Slope ``[%]`` at which the placeholder slope score reaches 0.0.
#: PLACEHOLDER MVP — not a literature value. See module docstring.
SLOPE_ZERO_SCORE_PCT: Final[float] = 25.0


@dataclass
class RunoffInputs:
    """
    Inputs for the Runoff Evaluator.

    Parameters
    ----------
    slope_pct
        Slope in percent (0-100).
    soil_saturation
        Soil water saturation as fraction (0-1).
    """

    slope_pct: float
    soil_saturation: float


@dataclass
class RunoffResult(EvaluationResult):
    """
    Result of the Runoff Evaluator.

    Extends EvaluationResult with per-factor breakdown.

    Attributes
    ----------
    score
        Geometric mean of all factor scores (from EvaluationResult).
    verdict
        One of "favourable" (>=0.7), "marginal" (0.3-0.7),
        "unfavourable" (<0.3) (from EvaluationResult).
    context
        Debugging info: inputs received, per-factor scores,
        version, is_workable flag (from EvaluationResult).
    slope_score
        Individual score for the slope factor (0-1).
    saturation_score
        Individual score for the soil saturation factor (0-1).
    is_workable
        True if score >= is_workable_threshold (default 0.5).
    extra_factor_scores
        Dict of {name: score} for any extra factors from _extra_factors() hook.
    """

    slope_score: Optional[float] = None
    saturation_score: Optional[float] = None
    is_workable: Optional[bool] = None
    extra_factor_scores: Dict[str, float] = field(default_factory=dict)


class RunoffEvaluator:
    """
    Evaluator for runoff risk based on slope and soil saturation.

    Stateless apart from the workability threshold: one instance can
    evaluate any number of :class:`RunoffInputs`.

    Parameters
    ----------
    is_workable_threshold
        Minimum final score for ``is_workable`` to be ``True``, in [0, 1].
        Default 0.5.

    Raises
    ------
    TypeError
        If ``is_workable_threshold`` is not a real number.
    ValueError
        If ``is_workable_threshold`` is non-finite or outside [0, 1].

    Examples
    --------
    >>> RunoffEvaluator().evaluate(RunoffInputs(slope_pct=5.0, soil_saturation=0.4)).score
    0.6928203230275509
    """

    def __init__(self, is_workable_threshold: float = 0.5) -> None:
        self.is_workable_threshold: float = self._validate_range(
            "is_workable_threshold", is_workable_threshold, 0.0, 1.0
        )

    # ------------------------------------------------------------------ public

    def evaluate(self, inputs: RunoffInputs) -> RunoffResult:
        """
        Score one field.

        Parameters
        ----------
        inputs
            Slope and soil saturation for the field.

        Returns
        -------
        RunoffResult
            Final geometric-mean score, verdict, per-factor scores,
            workability flag and context.

        Raises
        ------
        TypeError
            If an input, or an extra factor score, is not a real number.
        ValueError
            If an input, or an extra factor score, is non-finite or outside
            its range (slope [0, 100], saturation [0, 1], extra factors
            [0, 1]).
        """
        slope_pct = self._validate_range("slope_pct", inputs.slope_pct, 0.0, 100.0)
        soil_saturation = self._validate_range(
            "soil_saturation", inputs.soil_saturation, 0.0, 1.0
        )

        slope_score = self._score_slope(slope_pct)
        saturation_score = self._score_saturation(soil_saturation)
        extra_scores = self._extra_factors()
        for name, value in extra_scores.items():
            self._validate_range(f"extra factor {name!r}", value, 0.0, 1.0)

        all_scores = [slope_score, saturation_score] + list(extra_scores.values())
        score = self._geometric_mean(all_scores)
        is_workable = score >= self.is_workable_threshold

        # Independent copies: the result field and the context entry must not
        # alias each other (or the dict returned by the hook).
        extra_scores_snapshot = dict(extra_scores)

        context = {
            "inputs": {
                "slope_pct": inputs.slope_pct,
                "soil_saturation": inputs.soil_saturation,
            },
            "version": __version__,
            "slope_score": slope_score,
            "saturation_score": saturation_score,
            "extra_factor_scores": dict(extra_scores_snapshot),
            "is_workable": is_workable,
            "is_workable_threshold": self.is_workable_threshold,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return RunoffResult(
            score=score,
            verdict=self._determine_verdict(score),
            context=context,
            slope_score=slope_score,
            saturation_score=saturation_score,
            is_workable=is_workable,
            extra_factor_scores=dict(extra_scores_snapshot),
        )

    # ------------------------------------------------------------------ extension hook

    def _extra_factors(self) -> Dict[str, float]:
        """
        Hook for additional runoff factors. Returns ``{}`` by default.

        To add a factor (e.g. hydrography, vegetation), subclass
        ``RunoffEvaluator`` and override this method to return
        ``{factor_name: score}``. Each score must be in [0, 1],
        favourable-high; ``evaluate`` validates the range, folds every value
        into the geometric mean, and records them in ``extra_factor_scores``
        and ``context["extra_factor_scores"]``.

        Returns
        -------
        dict of str to float
            Extra factor scores keyed by factor name.
        """
        return {}

    # ------------------------------------------------------------------ scoring

    def _determine_verdict(self, score: float) -> str:
        """
        Determine categorical verdict from score.

        Cortes:
        - score >= 0.7 → "favourable"
        - 0.3 <= score < 0.7 → "marginal"
        - score < 0.3 → "unfavourable"

        Note: Comparisons use strict >=. Due to floating-point
        arithmetic, scores that "should" be exactly 0.3 or 0.7
        may fall on either side by ~1e-16. Example: slope=0,
        saturation=0.91 produces score=0.29999999999999993, which
        is classified as "unfavourable" rather than "marginal".

        Design choice — thresholds 0.3/0.7 are project-level
        decisions, not from literature. See module header.

        Parameters
        ----------
        score
            Final score in [0, 1].

        Returns
        -------
        str
            ``"favourable"`` if ``score >= 0.7``, ``"marginal"`` if
            ``0.3 <= score < 0.7``, ``"unfavourable"`` otherwise.
        """
        if score >= 0.7:
            return "favourable"
        elif score >= 0.3:
            return "marginal"
        else:
            return "unfavourable"

    def _score_slope(self, slope_pct: float) -> float:
        """
        Score slope, favourable-high.

        PLACEHOLDER MVP — linear mapping. TODO: replace with
        literature-backed function (e.g. SCS Curve Number, MUSLE)

        Linear from 0 % → 1.0 to 25 % → 0.0; slopes above 25 % clamp to 0.0.
        The 25 % breakpoint (``SLOPE_ZERO_SCORE_PCT``) is a placeholder, not
        a literature threshold.

        Parameters
        ----------
        slope_pct
            Field slope ``[%]``, in [0, 100].

        Returns
        -------
        float
            Slope score in [0, 1].
        """
        return max(0.0, 1.0 - slope_pct / SLOPE_ZERO_SCORE_PCT)

    def _score_saturation(self, saturation: float) -> float:
        """
        Score soil saturation, favourable-high.

        PLACEHOLDER MVP — linear mapping. TODO: replace with
        literature-backed function (e.g. SCS Curve Number, MUSLE)

        Inverted linear: 0.0 → 1.0, 1.0 → 0.0.

        Parameters
        ----------
        saturation
            Soil saturation as a fraction, in [0, 1].

        Returns
        -------
        float
            Saturation score in [0, 1].
        """
        return 1.0 - saturation

    @staticmethod
    def _geometric_mean(scores: List[float]) -> float:
        """
        Geometric mean ``prod(scores) ** (1 / len(scores))``.

        If any score is 0, the result is 0.0 (a single fully unfavourable
        factor forces the whole score to 0, as in ``base.py``).

        Parameters
        ----------
        scores
            Factor scores, each in [0, 1]. Must be non-empty.

        Returns
        -------
        float
            Geometric mean in [0, 1].

        Raises
        ------
        ValueError
            If ``scores`` is empty.
        """
        if not scores:
            raise ValueError("geometric mean of an empty list is undefined")
        if any(s == 0 for s in scores):
            return 0.0
        return math.prod(scores) ** (1.0 / len(scores))

    # ------------------------------------------------------------------ validation

    @staticmethod
    def _validate_range(name: str, value: float, low: float, high: float) -> float:
        """
        Check that ``value`` is a finite real number in ``[low, high]``.

        Parameters
        ----------
        name
            Input name, for the error message.
        value
            Value to check.
        low, high
            Inclusive bounds.

        Returns
        -------
        float
            ``value`` as a float.

        Raises
        ------
        TypeError
            If ``value`` is not an int or float (``bool`` is rejected).
        ValueError
            If ``value`` is non-finite or outside ``[low, high]``.
        """
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be a number, got {type(value).__name__}")
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite, got {value}")
        if not low <= value <= high:
            raise ValueError(f"{name} must be in [{low}, {high}], got {value}")
        return float(value)
