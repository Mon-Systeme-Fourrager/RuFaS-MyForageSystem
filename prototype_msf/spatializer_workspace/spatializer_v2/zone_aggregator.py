"""
zone_aggregator.py — Spatializer v0.2, MSFourrager

Combines normalized factor scores into one composite index, applies a
decision threshold, and renders a producer-facing message.

Combination method
------------------
**Geometric mean of normalized factor scores**, following Adamchuk et al.
2011 (Geoderma 163:63-73). This replaces the earlier weighted arithmetic
mean, which used subjective equal weights (25% x 4) and was judged not
defensible for publication (weekly of 2026-09-08).

Multiplication penalizes critical single-factor failures: a single factor at
exactly 0.0 forces the entire index to 0.0. That is intended, not a bug, and
the result is deliberately **not** clamped to a minimum.

No weights are assigned. Factor importance emerges from how each factor is
scaled to 0-1, which is now the critical calibration work — see the
Spatializer placeholders proposal note, Décision 5.

Polarity convention
-------------------
**High index = favourable.** A score of 1.0 means fully favourable for
working the field; 0.0 means unfavourable. ``apply_threshold`` passes when
the index is at or *above* the threshold.

Producer-facing language
------------------------
Producer messages are written in **French** — MSF's end users are Quebec
producers. Identifiers, docstrings, comments and error messages stay in
English; only strings a producer can see are translated.

The internal subdivision of a field is deliberately invisible to the
producer: messages describe the field as a whole and never expose the words
"zone", "cluster", "percentage"/"pourcentage", and carry no digits.
"""

from math import prod
from typing import Dict

# ============================================================
# Thresholds — PLACEHOLDERS
# Pending team validation. No value below is derived from data or literature.
# ============================================================

# High index = favourable. Apply when index >= THRESHOLD_APPLY.
THRESHOLD_APPLY = 0.7  # PLACEHOLDER — at or above this, the day is workable
THRESHOLD_MARGINAL = 0.5  # PLACEHOLDER — between MARGINAL and APPLY the day is borderline

# Backwards-compatible alias: the default used by apply_threshold().
DEFAULT_THRESHOLD = THRESHOLD_APPLY  # PLACEHOLDER

MASS_BALANCE_TOLERANCE = 1e-9

# Words that must never reach the producer.
# French equivalents included: producer messages are French (see module docstring).
FORBIDDEN_PRODUCER_TERMS = ("zone", "cluster", "percentage", "pourcentage", "%")

# Plain-language names for factors, used in producer messages.
# Deliberately polarity-neutral: they name the subject without implying whether
# a high score is a risk or a benefit, which keeps them consistent with the
# favourable-high convention.
# PLACEHOLDER — wording to be reviewed with the agronomy side.
#
# NOTE: keys are the internal factor names as used in each factor-score dict —
# "compaction", not "compaction_score".
_FACTOR_PLAIN_NAMES: Dict[str, str] = {
    "compaction": "les conditions du sol",
    "weather": "la météo",
    "runoff": "le ruissellement",
    "manure": "la disponibilité du fumier",
}


def aggregate_scores(factor_scores: Dict[str, float]) -> float:
    """
    Geometric mean of normalized factor scores.

    Reference: Adamchuk et al. 2011 (Geoderma 163:63-73).
    Multiplication penalizes critical single-factor failures.
    A single factor at exactly 0.0 forces the entire index to 0.0.

    Parameters
    ----------
    factor_scores
        Factor name to score in [0, 1], favourable-high. No weights are
        applied; every factor contributes equally through the product.

    Returns
    -------
    float
        Composite index in [0, 1]. The result is **not** clamped to a
        minimum — a zero factor yields a zero index, by design.

    Raises
    ------
    ValueError
        If ``factor_scores`` is empty, or any score is outside [0, 1].
        The range check also guards the arithmetic: a negative value raised
        to a fractional power is not real.
    """
    if not factor_scores:
        raise ValueError("factor_scores must not be empty")

    for factor, score in factor_scores.items():
        if not 0.0 <= score <= 1.0:
            raise ValueError(f"score for '{factor}' must be in [0, 1], got {score}")

    values = list(factor_scores.values())
    n = len(values)
    return prod(values) ** (1 / n)


def apply_threshold(index: float, threshold: float = DEFAULT_THRESHOLD) -> bool:
    """
    Decide whether the composite index clears the decision threshold.

    Returns
    -------
    bool
        ``True`` when the day is judged workable, i.e. the composite index is
        at or *above* the threshold. Higher index means more favourable.

    Raises
    ------
    ValueError
        If ``index`` or ``threshold`` is outside [0, 1].
    """
    if not 0.0 <= index <= 1.0:
        raise ValueError(f"index must be in [0, 1], got {index}")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"threshold must be in [0, 1], got {threshold}")
    return index >= threshold


def generate_producer_message(
    index: float,
    verdict: bool,
    factor_scores: Dict[str, float],
) -> str:
    """
    Render a plain-language message for the producer.

    The message never mentions internal subdivision, and carries no digits:
    the producer sees a judgement and the reason behind it, not an index.

    Parameters
    ----------
    index
        Composite index in [0, 1], favourable-high. Used only to choose
        wording strength.
    verdict
        Result of ``apply_threshold``.
    factor_scores
        Factor name to score in [0, 1], favourable-high. The **lowest**-scoring
        factor is named as the limiting one, since under this convention low
        means least favourable. May be empty, in which case no reason is given.

    Returns
    -------
    str
        A message safe to show a producer.

    Raises
    ------
    ValueError
        If ``index`` is outside [0, 1], or any factor score is outside [0, 1].
    """
    if not 0.0 <= index <= 1.0:
        raise ValueError(f"index must be in [0, 1], got {index}")
    for factor, score in factor_scores.items():
        if not 0.0 <= score <= 1.0:
            raise ValueError(f"factor score for '{factor}' must be in [0, 1], got {score}")

    if verdict:
        if index >= THRESHOLD_APPLY:
            headline = "Les conditions sont bonnes pour intervenir dans ce champ aujourd'hui."
        else:
            headline = "Les conditions sont acceptables pour intervenir dans ce champ aujourd'hui."
    else:
        if index < THRESHOLD_MARGINAL:
            headline = "Évitez d'intervenir dans ce champ aujourd'hui."
        else:
            headline = "Il n'est pas conseillé d'intervenir dans ce champ aujourd'hui."

    reason = ""
    if factor_scores:
        # Favourable-high: the limiting factor is the LOWEST-scoring one.
        limiting_factor = min(factor_scores, key=lambda name: factor_scores[name])
        plain_name = _FACTOR_PLAIN_NAMES.get(limiting_factor, limiting_factor.replace("_", " "))
        # Colon form avoids French gender/number agreement with the factor name:
        # the plain names vary (les conditions / la météo / le ruissellement).
        if verdict:
            reason = f" À surveiller principalement : {plain_name}."
        else:
            reason = f" Principale préoccupation : {plain_name}."

    message = headline + reason
    _assert_producer_safe(message)
    return message


def _assert_producer_safe(message: str) -> None:
    """
    Guard: raise if a producer-facing message leaks internal vocabulary.

    Raises
    ------
    AssertionError
        If any forbidden term appears in the message.
    """
    lowered = message.lower()
    for term in FORBIDDEN_PRODUCER_TERMS:
        assert term not in lowered, f"Producer message contains forbidden term '{term}': {message!r}"
