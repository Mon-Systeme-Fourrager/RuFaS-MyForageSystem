"""Beef cow-calf reproduction — natural-service seasonal breeding (NRC 2016 Ch.13)."""


def calculate_seasonal_conception_probability(
    body_condition_score: float,
    bull_to_cow_ratio: int,
    days_since_calving: int,
) -> float:
    """
    NRC 2016 Ch.13-informed daily conception probability for natural-service seasonal breeding.

    Parameters
    ----------
    body_condition_score : float
        Body condition on 1-9 scale. Cows below 5 have reduced conception.
    bull_to_cow_ratio : int
        Cows per bull. Above 30 reduces probability.
    days_since_calving : int
        Days postpartum. Below 45 = postpartum anestrus (probability = 0.0).

    Returns
    -------
    float
        Daily conception probability in [0.0, 1.0].

    Notes
    -----
    Simplified single-draw-per-day model; a full 21-day estrus-cycle model is
    out of scope for PR-B (documented limitation, Step 9). Calibrated so that
    aggregate seasonal pregnancy rate across a 63-day breeding season at BCS=5
    and 25:1 bull ratio approaches the USDA 91.5% calved-per-cow-exposed reference
    (excluding stillbirth/preweaning mortality applied separately).

    The BCS factor has a floor of 0.5 at BCS=1, meaning even severely thin cows
    retain 50% of base daily conception probability. This is a pragmatic model
    floor to avoid zero-probability traps in simulation; it is NOT derived from a
    specific NRC 2016 equation (the NRC gives qualitative guidance, not a precise
    mathematical adjustment function).
    """
    if days_since_calving < 45:
        return 0.0

    bcs_factor = min(1.0, max(0.5, (body_condition_score - 1) / 4.0))
    bull_factor = min(1.0, 30.0 / max(bull_to_cow_ratio, 1))
    base_daily_prob = 0.0404

    return base_daily_prob * bcs_factor * bull_factor
