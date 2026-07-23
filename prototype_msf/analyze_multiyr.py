"""
Multi-year sweep analysis:
  1. Compute rain profile per year from the weather CSV (before RUFAS extracts).
  2. Read the 30 output CSVs, extract runoff / available-N / root-zone-N per run.
  3. Build the per-year summary table.
  4. Save summary CSV + full 30-row CSV.
  5. Generate the runoff-vs-delay plot (one line per year, colored by precip band).

Runs headless — matplotlib Agg backend to avoid interactive-window hang.
"""

from __future__ import annotations

import glob

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

CSV_DIR = r"C:\Proyectos\RuFaS-MyForageSystem\output\CSVs"
WEATHER = r"C:\Proyectos\RuFaS-MyForageSystem\input\data\weather\example_temperate_weather.csv"
OUT_CSV = r"C:\Proyectos\RuFaS-MyForageSystem\prototype_msf\multiyr_sweep_results.csv"
OUT_FULL_CSV = r"C:\Proyectos\RuFaS-MyForageSystem\prototype_msf\multiyr_sweep_results_full.csv"
OUT_PLOT = r"C:\Proyectos\RuFaS-MyForageSystem\prototype_msf\multiyr_sweep_plot.png"

YEARS = [2020, 2003, 2002, 2010, 2007, 2013]
DELAYS = [0, 1, 2, 3, 4]


# --- 1. Rain profile ---
weather = pd.read_csv(WEATHER)
weather.columns = weather.columns.str.strip()
window = weather[(weather["jday"] >= 202) & (weather["jday"] <= 237)]


def rain_profile(y: int) -> dict:
    yw = window[window["year"] == y]
    rain_days = yw[yw["precip"] > 0]
    if not len(rain_days):
        return {
            "year": y,
            "total_precip_mm": 0.0,
            "first_rain_day": None,
            "biggest_rain_day": None,
            "biggest_rain_mm": 0.0,
            "n_rain_days": 0,
        }
    biggest_idx = rain_days["precip"].idxmax()
    return {
        "year": y,
        "total_precip_mm": float(yw["precip"].sum()),
        "first_rain_day": int(rain_days["jday"].min()),
        "biggest_rain_day": int(rain_days.loc[biggest_idx, "jday"]),
        "biggest_rain_mm": float(rain_days["precip"].max()),
        "n_rain_days": int(len(rain_days)),
    }


profiles = {y: rain_profile(y) for y in YEARS}

print("=== Rain profile per year ===")
for y in YEARS:
    p = profiles[y]
    print(
        f"  {y}: {p['total_precip_mm']:>6.1f} mm total, "
        f"first rain day {p['first_rain_day']}, "
        f"biggest rain day {p['biggest_rain_day']} ({p['biggest_rain_mm']:.1f} mm), "
        f"{p['n_rain_days']} rain days"
    )
print()


# --- 2. Read output CSVs ---
def latest(prefix: str) -> str | None:
    matches = sorted(glob.glob(f"{CSV_DIR}\\{prefix}_saved_variables_*.csv"))
    return matches[-1] if matches else None


def find_col(df, must_contain, must_also_contain=("field_1",)) -> str | None:
    for c in df.columns:
        lc = c.lower()
        if all(m.lower() in lc for m in must_contain) and all(m.lower() in lc for m in must_also_contain):
            return c
    return None


def layer_col(df, kind: str, layer: int) -> str | None:
    for c in df.columns:
        if kind in c.lower() and "field_1" in c.lower() and f"layer='{layer}'" in c:
            return c
    return None


results = []
for year in YEARS:
    for delay in DELAYS:
        day = 202 + delay
        prefix = f"msf_multiyr_y{year}_d{day}"
        path = latest(prefix)
        if not path:
            print(f"MISSING: {prefix} — skipped")
            continue
        df = pd.read_csv(path)
        runoff_c = find_col(df, ("nitrate_runoff",))
        total_runoff = df[runoff_c].fillna(0).sum() if runoff_c else float("nan")

        row_post30 = delay + 30
        total_avail = 0.0
        rz = 0.0
        for i in range(4):
            nc = layer_col(df, "nitrate_content", i)
            ac = layer_col(df, "ammonium_content", i)
            if nc:
                total_avail += df[nc].iloc[row_post30]
                if i == 1:
                    rz += df[nc].iloc[row_post30]
            if ac:
                total_avail += df[ac].iloc[row_post30]
                if i == 1:
                    rz += df[ac].iloc[row_post30]

        results.append(
            {
                "year": year,
                "delay": delay,
                "apply_day": day,
                "total_runoff_kg": total_runoff,
                "n_available_day30_kg": total_avail,
                "root_zone_layer1_kg": rz,
            }
        )

results_df = pd.DataFrame(results)


# --- 3. Per-year summary ---
summary = []
for year in YEARS:
    yr = results_df[results_df["year"] == year].sort_values("delay").reset_index(drop=True)
    if not len(yr):
        continue
    prof = profiles[year]
    opt_runoff_row = yr.loc[yr["total_runoff_kg"].idxmin()]
    opt_rz_row = yr.loc[yr["root_zone_layer1_kg"].idxmax()]
    baseline = yr[yr["delay"] == 0].iloc[0]
    summary.append(
        {
            "year": year,
            "precip_mm": round(prof["total_precip_mm"], 1),
            "first_rain_day": prof["first_rain_day"],
            "biggest_rain_day": prof["biggest_rain_day"],
            "biggest_rain_mm": round(prof["biggest_rain_mm"], 1),
            "n_rain_days": prof["n_rain_days"],
            "optimal_delay_runoff": int(opt_runoff_row["delay"]),
            "optimal_delay_root_zone_n": int(opt_rz_row["delay"]),
            "runoff_at_optimal_kg": round(float(opt_runoff_row["total_runoff_kg"]), 4),
            "runoff_at_delay0_kg": round(float(baseline["total_runoff_kg"]), 4),
        }
    )

summary_df = pd.DataFrame(summary).sort_values("precip_mm").reset_index(drop=True)


# --- 4. Save ---
summary_df.to_csv(OUT_CSV, index=False)
results_df.to_csv(OUT_FULL_CSV, index=False)


# --- 5. Plot ---
fig, ax = plt.subplots(figsize=(10, 6))


def color_for(precip_mm: float) -> str:
    if precip_mm < 60:
        return "#DC2626"  # dry — red
    if precip_mm < 200:
        return "#1E40AF"  # median — blue
    return "#166534"  # wet — green


band_labels = {"#DC2626": "Dry (<60 mm)", "#1E40AF": "Median (60-200 mm)", "#166534": "Wet (>200 mm)"}

for year in YEARS:
    yr = results_df[results_df["year"] == year].sort_values("delay")
    if not len(yr):
        continue
    p = profiles[year]["total_precip_mm"]
    color = color_for(p)
    ax.plot(
        yr["delay"],
        yr["total_runoff_kg"],
        "o-",
        color=color,
        linewidth=2,
        markersize=7,
        label=f"{year} ({p:.0f} mm)",
        alpha=0.85,
    )

ax.set_title(
    "Multi-year robustness — nitrate runoff vs manure application delay\n"
    "(30 t/ha broadcast dairy slurry, 6 years spanning 29.8-333 mm July-Aug precipitation)",
    fontweight="bold",
)
ax.set_xlabel("Days of delay (relative to July 21)")
ax.set_ylabel("Total 35-day nitrate runoff (kg N)")
ax.set_xticks(DELAYS)
ax.grid(True, alpha=0.3)
ax.legend(title="Year (window precip)", loc="best")

plt.tight_layout()
plt.savefig(OUT_PLOT, dpi=150, bbox_inches="tight")


# --- 6. Print final table per user's spec ---
print()
print("=== FINAL TABLE ===")
print()
print(
    f"{'Year':>4} | {'Precip (mm)':>11} | {'First rain':>10} | {'Biggest rain':>12} | "
    f"{'Opt delay runoff':>16} | {'Opt delay rootN':>15} | {'Runoff@opt':>10} | {'Runoff@d0':>9}"
)
print(
    f"{'-'*4} | {'-'*11} | {'-'*10} | {'-'*12} | {'-'*16} | {'-'*15} | {'-'*10} | {'-'*9}"
)
for _, r in summary_df.iterrows():
    print(
        f"{int(r['year']):>4} | {r['precip_mm']:>11.1f} | "
        f"{int(r['first_rain_day']):>10} | {int(r['biggest_rain_day']):>12} | "
        f"{int(r['optimal_delay_runoff']):>16} | {int(r['optimal_delay_root_zone_n']):>15} | "
        f"{r['runoff_at_optimal_kg']:>10.4f} | {r['runoff_at_delay0_kg']:>9.4f}"
    )

print()
print(f"Summary CSV: {OUT_CSV}")
print(f"Full 30-row CSV: {OUT_FULL_CSV}")
print(f"Plot: {OUT_PLOT}")
