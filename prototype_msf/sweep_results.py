"""
Sweep results — compares 5 RUFAS simulations that vary manure application day.

Metrics per run:
  * Total nitrate runoff over the 35-day window
  * Plant-available N (nitrate + ammonium across 4 soil layers) 30 days POST-application
  * Layer 1 (root zone) N 30 days POST-application

Post-application indexing is used so all 5 runs are compared 30 days after THEIR
respective application day, not on the same absolute calendar day.
"""

from __future__ import annotations

import glob

import pandas as pd

CSV_DIR = r"C:\Proyectos\RuFaS-MyForageSystem\output\CSVs"
DAYS = [202, 203, 204, 205, 206]
SIM_START = 202  # first day of simulation window (row 0)


def latest(prefix: str) -> str:
    matches = sorted(glob.glob(f"{CSV_DIR}\\{prefix}_saved_variables_*.csv"))
    if not matches:
        raise FileNotFoundError(f"No CSV found for prefix {prefix}")
    return matches[-1]


def find_col(df, must_contain, must_also_contain=("field_1",)):
    for c in df.columns:
        lc = c.lower()
        if all(m.lower() in lc for m in must_contain) and all(m.lower() in lc for m in must_also_contain):
            return c
    return None


def layer_col(df, kind, layer):
    for c in df.columns:
        if kind in c.lower() and "field_1" in c.lower() and f"layer='{layer}'" in c:
            return c
    raise KeyError(f"{kind} layer={layer} column not found")


rows = []
for day in DAYS:
    prefix = f"msf_prototype_day{day}"
    df = pd.read_csv(latest(prefix))

    # Sanity: verify RUFAS recorded the correct application day
    app_day_col = find_col(df, ("manure_application",), ("field_1",))  # any manure_app col
    # More specific: pull application_depth to sanity-check the manure event fired
    apply_day_series = df[find_col(df, ("manure_application", "day"))].dropna()
    recorded_day = int(apply_day_series.iloc[0]) if len(apply_day_series) else -1

    # Row index for "30 days POST-application"
    row_apply = day - SIM_START
    row_post30 = row_apply + 30

    # 1. Total nitrate runoff
    runoff_c = find_col(df, ("nitrate_runoff",))
    total_runoff = df[runoff_c].fillna(0).sum()

    # 2. N available at day+30 (nitrate + ammonium across 4 layers)
    total_avail = 0.0
    for i in range(4):
        total_avail += df[layer_col(df, "nitrate_content", i)].iloc[row_post30]
        total_avail += df[layer_col(df, "ammonium_content", i)].iloc[row_post30]

    # 3. Layer 1 (root zone) N at day+30
    layer1_n = (
        df[layer_col(df, "nitrate_content", 1)].iloc[row_post30]
        + df[layer_col(df, "ammonium_content", 1)].iloc[row_post30]
    )

    rows.append(
        {
            "day_applied": day,
            "recorded_day": recorded_day,
            "delay": day - DAYS[0],
            "total_runoff_kg": round(total_runoff, 4),
            "n_available_day30_kg": round(total_avail, 3),
            "root_zone_layer1_kg": round(layer1_n, 3),
        }
    )

# Sanity-check: recorded days should match requested days
mismatch = [r for r in rows if r["recorded_day"] != r["day_applied"]]
if mismatch:
    print("!! WARNING: recorded_day != requested_day for some runs:")
    for r in mismatch:
        print(f"     requested={r['day_applied']}  recorded={r['recorded_day']}")
    print()

print("=== Sweep results — days-of-delay vs runoff/availability curve ===")
print()
print(f"{'Day applied':>11} | {'Delay':>5} | {'Total runoff (kg)':>17} | {'N available day 30 (kg)':>23} | {'Root zone N (kg)':>16}")
print(f"{'-'*11:>11}-+-{'-'*5:>5}-+-{'-'*17:>17}-+-{'-'*23:>23}-+-{'-'*16:>16}")
for r in rows:
    print(
        f"{r['day_applied']:>11} | {r['delay']:>5} | {r['total_runoff_kg']:>17.4f} | {r['n_available_day30_kg']:>23.3f} | {r['root_zone_layer1_kg']:>16.3f}"
    )

print()
print("=== Decision curve — day-over-day deltas ===")
baseline = rows[0]
for r in rows:
    d_runoff = r["total_runoff_kg"] - baseline["total_runoff_kg"]
    pct_runoff = (d_runoff / baseline["total_runoff_kg"] * 100) if baseline["total_runoff_kg"] > 0 else float("nan")
    d_avail = r["n_available_day30_kg"] - baseline["n_available_day30_kg"]
    pct_avail = (d_avail / baseline["n_available_day30_kg"] * 100) if baseline["n_available_day30_kg"] > 0 else float("nan")
    marker = "  " if r["delay"] > 0 else "* "  # mark the baseline row
    print(
        f"  {marker}delay {r['delay']}d: runoff {d_runoff:+.4f} kg ({pct_runoff:+.1f}%), day-30 available N {d_avail:+.3f} kg ({pct_avail:+.1f}%)"
    )

print()
print("=== Optimum ===")
best_runoff = min(rows, key=lambda r: r["total_runoff_kg"])
best_avail = max(rows, key=lambda r: r["n_available_day30_kg"])
print(f"  Lowest runoff:        day {best_runoff['day_applied']} (delay {best_runoff['delay']}d) — {best_runoff['total_runoff_kg']:.4f} kg")
print(f"  Highest day-30 N:     day {best_avail['day_applied']} (delay {best_avail['delay']}d) — {best_avail['n_available_day30_kg']:.3f} kg")
