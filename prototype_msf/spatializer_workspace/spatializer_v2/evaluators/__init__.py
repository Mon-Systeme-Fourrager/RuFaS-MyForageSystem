"""
evaluators — Spatializer v0.2 factor evaluators, MSFourrager

One evaluator per factor of the composite index. Each returns a normalized
score in [0, 1], favourable-high, which ``zone_aggregator.aggregate_scores``
combines as a geometric mean (Adamchuk et al. 2011, Geoderma 163:63-73).

Implemented:
    compaction — via the Terranimo REST API (Factor 1)
    weather    — via Open-Meteo, umbrales de Brassard et al. 2026 (Factor 2)
    runoff     — slope + soil saturation, linear placeholder scoring (Factor 3)

Not yet implemented:
    manure availability (Factor 4)

Reference:
    MSF-Notes/Spatializer/2026-09-03-Spatializer-v0.2-placeholders-proposal.md
"""

from .base import EvaluationResult, Evaluator
from .compaction import (
    VERDICT_TO_SCORE,
    CompactionEvaluator,
    CompactionResult,
    SoilInputs,
    TractorInputs,
)
from .runoff import (
    RunoffEvaluator,
    RunoffInputs,
    RunoffResult,
)
from .weather import (
    WeatherEvaluator,
    WeatherInputs,
    WeatherResult,
    get_recommended_timing,
    get_verdict,
    score_precipitation,
    score_temperature,
    score_wind,
)

__all__ = [
    "EvaluationResult",
    "Evaluator",
    "CompactionEvaluator",
    "CompactionResult",
    "SoilInputs",
    "TractorInputs",
    "VERDICT_TO_SCORE",
    "RunoffEvaluator",
    "RunoffInputs",
    "RunoffResult",
    "WeatherEvaluator",
    "WeatherInputs",
    "WeatherResult",
    "score_temperature",
    "score_wind",
    "score_precipitation",
    "get_verdict",
    "get_recommended_timing",
]
