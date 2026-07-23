"""
MSF Expert System — Integrated Decision Engine
Combines:
  1. RUFAS timing analysis (nitrate runoff, N availability)
  2. Soil compaction risk (Carranza-Díaz et al. + Stettler et al. 2014)

Output: complete recommendation for the producer
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from compaction_model import evaluate_compaction_risk
import pandas as pd
import glob


# ─────────────────────────────────────────────
# Machinery profile — typical Quebec dairy farm
# ─────────────────────────────────────────────
MACHINERY_PROFILE = {
    "name": "Massey Ferguson 243 + slurry tanker",
    "static_rear_weight_kN": 21.3,
    "static_front_weight_kN": 12.7,
    "traction_force_kN": 8.0,
    "hitch_height_m": 0.45,
    "wheelbase_m": 2.15,
    "total_diameter_m": 1.35,
    "static_load_radius_m": 0.58,
    "section_width_m": 0.38,
    "inflation_pressure_kPa": 120.0,
    "tire_load_kN": 17.2,
}

# ─────────────────────────────────────────────
# Soil profile — Quebec clay (G1 group)
# ─────────────────────────────────────────────
SOIL_PROFILE = {
    "clay_content_pct": 35.0,
    "name": "Quebec clay loam (G1)",
}


def estimate_matric_potential(precip_last_7days_mm: float) -> float:
    """
    Rough estimate of soil matric potential from recent precipitation.
    Wet soil = low absolute matric potential (near 0)
    Dry soil = high absolute matric potential

    This is a simplification — ideally comes from RUFAS soil water content.

    Args:
        precip_last_7days_mm: Total precipitation last 7 days (mm)

    Returns:
        Matric potential (kPa, absolute value)
    """
    if precip_last_7days_mm > 40:
        return 5.0      # very wet
    elif precip_last_7days_mm > 20:
        return 10.0     # wet
    elif precip_last_7days_mm > 10:
        return 30.0     # moist
    elif precip_last_7days_mm > 5:
        return 60.0     # drying
    else:
        return 100.0    # dry


def integrated_recommendation(
    delay_days: int,
    nitrate_runoff_kg: float,
    n_available_kg: float,
    root_zone_n_kg: float,
    precip_last_7days_mm: float,
) -> dict:
    """
    Combine RUFAS timing metrics with compaction risk for a given delay.
    """
    # Estimate soil moisture state
    matric_potential = estimate_matric_potential(precip_last_7days_mm)

    # Evaluate compaction risk
    # Filter machinery profile to arg names accepted by evaluate_compaction_risk
    machinery_args = {k: v for k, v in MACHINERY_PROFILE.items() if k != "name"}
    compaction = evaluate_compaction_risk(
        **machinery_args,
        clay_content_pct=SOIL_PROFILE["clay_content_pct"],
        matric_potential_kPa=matric_potential,
    )

    # Decision logic
    can_apply = compaction["can_enter_field"]

    if not can_apply:
        decision = "NO"
        reason = f"Compaction risk {compaction['color']} — {compaction['recommendation']}"
    else:
        decision = "YES"
        reason = f"Soil conditions OK (compaction {compaction['color']}). Expected runoff: {nitrate_runoff_kg:.3f} kg N"

    return {
        "delay_days": delay_days,
        "decision": decision,
        "reason": reason,
        "compaction_risk": compaction["color"],
        "compaction_ratio": compaction["ratio"],
        "sigma_act_kPa": compaction["sigma_act"],
        "sigma_pc_kPa": compaction["sigma_pc"],
        "nitrate_runoff_kg": nitrate_runoff_kg,
        "n_available_kg": n_available_kg,
        "root_zone_n_kg": root_zone_n_kg,
        "matric_potential_kPa": matric_potential,
    }


def main():
    print("=" * 70)
    print("MSF EXPERT SYSTEM — INTEGRATED DECISION ENGINE")
    print("=" * 70)
    print()
    print(f"Machinery: {MACHINERY_PROFILE['name']}")
    print(f"Soil:      {SOIL_PROFILE['name']} ({SOIL_PROFILE['clay_content_pct']}% clay)")
    print()

    # Load the 2013 sweep results (from sweep_results.py output)
    sweep_data = [
        # delay, runoff, n_avail, root_n, precip_7d_before_application
        (0, 0.5862, 60.249, 32.927, 45.0),   # wet — recent rain
        (1, 0.3266, 61.247, 33.800, 45.0),   # still wet
        (2, 0.3668, 61.407, 33.840, 12.0),   # drying
        (3, 0.4051, 60.457, 38.795, 8.0),    # drier
        (4, 0.3986, 60.460, 35.720, 3.0),    # dry
    ]

    results = []
    for delay, runoff, n_avail, root_n, precip in sweep_data:
        rec = integrated_recommendation(delay, runoff, n_avail, root_n, precip)
        results.append(rec)

    # Print decision table
    print("DECISION TABLE — 2013 weather scenario")
    print("-" * 70)
    print(f"{'Delay':<7} {'Decision':<10} {'Compaction':<12} {'Ratio':<8} {'Runoff (kg)':<13} {'Root N (kg)':<12}")
    print("-" * 70)

    for r in results:
        print(f"{r['delay_days']:<7} {r['decision']:<10} {r['compaction_risk']:<12} "
              f"{r['compaction_ratio']:<8.2f} {r['nitrate_runoff_kg']:<13.4f} {r['root_zone_n_kg']:<12.2f}")

    print("-" * 70)
    print()

    # Find the best recommendation
    viable = [r for r in results if r["decision"] == "YES"]

    if not viable:
        print("⚠️  RECOMMENDATION: DO NOT APPLY")
        print("   No day in the 0-4 day window has acceptable compaction risk.")
        print("   Wait for drier soil conditions.")
    else:
        # Among viable options, minimize runoff
        best = min(viable, key=lambda r: r["nitrate_runoff_kg"])
        print("✅ RECOMMENDATION")
        print(f"   Apply in {best['delay_days']} day(s)")
        print(f"   Compaction: {best['compaction_risk']} (σ_act={best['sigma_act_kPa']} kPa vs σ_pc={best['sigma_pc_kPa']} kPa)")
        print(f"   Expected nitrate runoff: {best['nitrate_runoff_kg']:.3f} kg N")
        print(f"   Root-zone N at day 30: {best['root_zone_n_kg']:.2f} kg")
        print()
        print("   Alternatives:")
        for r in sorted(viable, key=lambda x: x["nitrate_runoff_kg"])[1:3]:
            print(f"     Delay {r['delay_days']}d — runoff {r['nitrate_runoff_kg']:.3f} kg, "
                  f"root N {r['root_zone_n_kg']:.2f} kg, compaction {r['compaction_risk']}")

    print()
    print("=" * 70)

    # Save results
    df = pd.DataFrame(results)
    out_path = Path(__file__).parent / "integrated_decision_results.csv"
    df.to_csv(out_path, index=False)
    print(f"Results saved to {out_path.name}")


if __name__ == "__main__":
    main()
