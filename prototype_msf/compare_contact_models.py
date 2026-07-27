"""
Cross-check of two published tyre-soil contact models.

MODEL A - Grecenko (1989/1995), as implemented in compaction_model.py
  Closed form from catalogue geometry:
    A_geo = C1 * sqrt((dk - 2*rs) * bk * rs)
    A_exp = rs * bk * (W / (p * rs * bk))
  Inputs: overall diameter, static loaded radius, section width, load,
          inflation pressure.

MODEL B - Keller (2005), SoilFlex, as implemented in soilphysics v5.0
  R/stressTraffic.R lines 8-14. SHA-256
    601C0CC9FA5A21A37E5D7FFA03B211E8CB1D50DB5D06B1F324136C4356A9232A
  Reimplemented here in Python from that source:
    stress_max  = 34.4 + 1.13*p + 0.72*W - 33.4*ln(p / p_rec)
    area_length = 0.47 + 0.11*d^2 - 0.16*ln(p / p_rec)
  Then a superellipse shape integrated numerically.
  Inputs: inflation pressure, recommended pressure, wheel load, diameter,
          width.

The two use different inputs and different mathematics, so exact agreement
is not expected. The purpose is an order-of-magnitude check: if they differ
by more than roughly a factor of two, at least one implementation or one
transcription is wrong.

NOTE ON UNITS in Keller 2005 as implemented in soilphysics:
  inflation.pressure and recommended.pressure in kPa
  wheel.load converted internally from kg to kN: (kg * 9.81)/1000
  tyre.diameter and tyre.width in m
  stress_max output in kPa
"""

import math

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from compaction_model import (
    contact_area_geometric,
    contact_area_experimental,
    applied_stress,
)


def keller_stress_max_kPa(inflation_pressure_kPa: float,
                          wheel_load_kN: float,
                          recommended_pressure_kPa: float) -> float:
    """
    Maximum contact stress, Keller (2005).
    soilphysics R/stressTraffic.R line 8:
      stressmax <- 34.4 + (1.13 * inflation.pressure) + (0.72 * wheel.load)
                   - 33.4 * log(inflation.pressure/recommended.pressure)
    R's log() is natural log.
    """
    return (34.4
            + 1.13 * inflation_pressure_kPa
            + 0.72 * wheel_load_kN
            - 33.4 * math.log(inflation_pressure_kPa / recommended_pressure_kPa))


def keller_area_length_m(tyre_diameter_m: float,
                         inflation_pressure_kPa: float,
                         recommended_pressure_kPa: float) -> float:
    """
    Contact area length, Keller (2005).
    soilphysics R/stressTraffic.R line 9-10:
      area.length <- 0.47 + 0.11*(tyre.diameter^2)
                     - 0.16*log(inflation.pressure/recommended.pressure)
    """
    return (0.47
            + 0.11 * (tyre_diameter_m ** 2)
            - 0.16 * math.log(inflation_pressure_kPa / recommended_pressure_kPa))


def main():
    # Illustrative inputs only - NOT verified machinery parameters.
    # Chosen to span a plausible range for a small utility tractor rear tyre.
    scenarios = [
        # label,              dk,   rs,   bk,   p,     p_rec, wheel_load_kN
        ("small, low press",  1.20, 0.52, 0.34, 80.0,  80.0,  10.0),
        ("small, high press", 1.20, 0.52, 0.34, 160.0, 80.0,  10.0),
        ("large, low press",  1.60, 0.70, 0.50, 80.0,  80.0,  20.0),
        ("large, high press", 1.60, 0.70, 0.50, 160.0, 80.0,  20.0),
    ]

    print("Cross-check: Grecenko (ours) vs Keller 2005 (soilphysics)")
    print("Inputs are ILLUSTRATIVE - no verified machinery parameters available")
    print("=" * 92)
    print(f"{'scenario':<20}{'A_geo':>9}{'A_exp':>9}{'sig_geo':>10}"
          f"{'sig_exp':>10}{'K_len':>9}{'K_smax':>10}{'ratio':>10}")
    print(f"{'':<20}{'m2':>9}{'m2':>9}{'kPa':>10}{'kPa':>10}{'m':>9}{'kPa':>10}"
          f"{'ours/K':>10}")
    print("-" * 92)

    for label, dk, rs, bk, p, p_rec, load_kN in scenarios:
        a_geo = contact_area_geometric(dk, rs, bk)
        a_exp = contact_area_experimental(rs, bk, load_kN, p)

        # applied_stress takes axle load; pass 2*wheel load with 2 wheels
        sig_geo = applied_stress(load_kN * 2, a_geo, n_wheels_per_axle=2)
        sig_exp = applied_stress(load_kN * 2, a_exp, n_wheels_per_axle=2)

        k_len = keller_area_length_m(dk, p, p_rec)
        k_smax = keller_stress_max_kPa(p, load_kN, p_rec)

        ratio = sig_geo / k_smax

        print(f"{label:<20}{a_geo:>9.3f}{a_exp:>9.3f}{sig_geo:>10.1f}"
              f"{sig_exp:>10.1f}{k_len:>9.3f}{k_smax:>10.1f}{ratio:>10.2f}")

    print("-" * 92)
    print()
    print("How to read this:")
    print("  sig_geo / sig_exp  our mean contact stress, two area formulas")
    print("  K_smax             Keller MAXIMUM contact stress, not the mean")
    print()
    print("Keller reports a maximum and ours is a mean, so ours should be")
    print("LOWER. A ratio around 0.4-0.8 is consistent. A ratio above 1, or")
    print("below 0.2, points at a problem in one of the implementations.")
    print()
    print("This is a sanity check between two published models, not a")
    print("validation of either against measurements.")


if __name__ == "__main__":
    main()
