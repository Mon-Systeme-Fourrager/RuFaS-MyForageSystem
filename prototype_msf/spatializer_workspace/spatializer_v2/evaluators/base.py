"""
base.py — Spatializer v0.2 evaluators, MSFourrager

Shared types for the four factor evaluators (compaction, weather, runoff,
manure availability).

Each evaluator turns domain inputs into a **normalized score in [0, 1],
favourable-high**, which ``zone_aggregator.aggregate_scores`` then combines
as a geometric mean, following Adamchuk et al. 2011 (Geoderma 163:63-73).
Because the aggregation multiplies, a single factor at exactly 0.0 forces the
whole index to 0.0 — intended, and the reason the per-factor scaling is the
critical calibration work.

Reference:
    MSF-Notes/Spatializer/2026-09-03-Spatializer-v0.2-placeholders-proposal.md
    (Décision 5 — Scaling par facteur)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Protocol


@dataclass
class EvaluationResult:
    """
    Base result for any evaluator.

    Attributes
    ----------
    score
        Normalized factor score in [0, 1], **favourable-high**: 1.0 is fully
        favourable for working the field, 0.0 unfavourable. This is the only
        field ``aggregate_scores`` consumes.
    verdict
        Human-readable label for the outcome. Free-form per evaluator — this
        is a developer-facing label, **not** producer-facing text. Producer
        messages are generated in French by ``zone_aggregator``.
    context
        Debugging information: raw API responses, intermediate values,
        whatever made the score reproducible. Never consumed by scoring.
    """

    score: float
    verdict: str
    context: Dict[str, Any] = field(default_factory=dict)


class Evaluator(Protocol):
    """
    Protocol for all factor evaluators.

    Structural, not inherited: an evaluator satisfies this by shape. Each
    implementation takes whatever domain inputs it needs and returns an
    :class:`EvaluationResult` whose ``score`` is in [0, 1], favourable-high.
    """

    def evaluate(self, **inputs: Any) -> EvaluationResult:
        """Return a score 0-1 with contextual information."""
        ...
