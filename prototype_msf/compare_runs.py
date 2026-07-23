"""
Compare RUFAS prototype runs:
  Run 1: apply on sim day 0 (calendar 202, 2013-07-21) — day-1 rain hits manure
  Run 2: apply on sim day 3 (calendar 205, 2013-07-24) — day-1 rain is 2 days pre-application

Both runs share the same 35-day weather window (2013:202 -> 2013:237), so rain events
fall on the SAME simulation day indexes (rows 1, 22, 33 based on run 1 observations).
"""

import glob

import pandas as pd

CSV_DIR = r"C:\Proyectos\RuFaS-MyForageSystem\output\CSVs"


def latest(prefix: str) -> str:
    matches = sorted(glob.glob(f"{CSV_DIR}\\{prefix}_saved_variables_*.csv"))
    if not matches:
        raise FileNotFoundError(f"No CSV found for prefix {prefix}")
    return matches[-1]


def load(prefix: str) -> pd.DataFrame:
    path = latest(prefix)
    print(f"  Loading: {path.split(chr(92))[-1]}")
    return pd.read_csv(path)


def runoff_col(df):
    for c in df.columns:
        if "nitrate_runoff" in c.lower() and "field_1" in c.lower():
            return c
    raise KeyError("nitrate_runoff.field_1 column not found")


def layer_nitrate_cols(df):
    return {
        i: next(
            c for c in df.columns
            if "nitrate_content" in c.lower()
            and "field_1" in c.lower()
            and f"layer='{i}'" in c
        )
        for i in range(4)
    }


def layer_ammonium_cols(df):
    return {
        i: next(
            c for c in df.columns
            if "ammonium_content" in c.lower()
            and "field_1" in c.lower()
            and f"layer='{i}'" in c
        )
        for i in range(4)
    }


def application_day(df):
    for c in df.columns:
        if "manure_application" in c.lower() and "field_1" in c.lower() and c.endswith(".day"):
            return int(df[c].dropna().iloc[0])
    return None


print("=== Loading CSVs ===")
df1 = load("msf_prototype")
df2 = load("msf_prototype_delayed")

print()
print("=== Application days ===")
app_day_1 = application_day(df1)
app_day_2 = application_day(df2)
print(f"  Run 1 applied on calendar day: {app_day_1}")
print(f"  Run 2 applied on calendar day: {app_day_2}")

# Simulation start = day 202 -> row 0. Sim day = row index.
sim_day_apply_1 = app_day_1 - 202
sim_day_apply_2 = app_day_2 - 202
print(f"  Run 1 application on sim row: {sim_day_apply_1}")
print(f"  Run 2 application on sim row: {sim_day_apply_2}")

print()
print("=== 1) Total nitrate runoff over 35-day window ===")
r1 = df1[runoff_col(df1)].fillna(0).sum()
r2 = df2[runoff_col(df2)].fillna(0).sum()
print(f"  Run 1 (apply row 0):  {r1:.3f} kg over 10 ha = {r1/10:.4f} kg/ha")
print(f"  Run 2 (apply row 3):  {r2:.3f} kg over 10 ha = {r2/10:.4f} kg/ha")
delta = r2 - r1
pct = (delta / r1 * 100) if r1 > 0 else float("nan")
print(f"  Delta:                {delta:+.3f} kg  ({pct:+.1f}% change)")

print()
print("=== 2) Nitrate runoff by day (kg) — where the difference comes from ===")
runoff_series_1 = df1[runoff_col(df1)].fillna(0)
runoff_series_2 = df2[runoff_col(df2)].fillna(0)
runoff_cmp = pd.DataFrame({
    "sim_row": range(len(runoff_series_1)),
    "run1_runoff_kg": runoff_series_1.round(3).values,
    "run2_runoff_kg": runoff_series_2.round(3).values,
})
runoff_cmp["delta"] = (runoff_cmp["run2_runoff_kg"] - runoff_cmp["run1_runoff_kg"]).round(3)
# Only show rows where either run had non-zero runoff
non_zero = runoff_cmp[(runoff_cmp["run1_runoff_kg"] != 0) | (runoff_cmp["run2_runoff_kg"] != 0)]
print(non_zero.to_string(index=False))

print()
print("=== 3) N available 30 days POST-APPLICATION ===")
# Run 1: applied row 0 -> +30 days = row 30
# Run 2: applied row 3 -> +30 days = row 33
row_30_days_1 = sim_day_apply_1 + 30
row_30_days_2 = sim_day_apply_2 + 30
nitrate_1 = layer_nitrate_cols(df1)
nitrate_2 = layer_nitrate_cols(df2)
ammonium_1 = layer_ammonium_cols(df1)
ammonium_2 = layer_ammonium_cols(df2)

print(f"  Comparison at row {row_30_days_1} (run 1) vs row {row_30_days_2} (run 2)")
print()
print(f"  {'Layer':<8} {'run1_nit':>10} {'run2_nit':>10} {'run1_amm':>10} {'run2_amm':>10} {'run1_tot':>10} {'run2_tot':>10}")
sum_1 = 0.0
sum_2 = 0.0
for i in range(4):
    n1 = df1[nitrate_1[i]].iloc[row_30_days_1]
    n2 = df2[nitrate_2[i]].iloc[row_30_days_2]
    a1 = df1[ammonium_1[i]].iloc[row_30_days_1]
    a2 = df2[ammonium_2[i]].iloc[row_30_days_2]
    t1 = n1 + a1
    t2 = n2 + a2
    sum_1 += t1
    sum_2 += t2
    print(f"  {i:<8} {n1:>10.3f} {n2:>10.3f} {a1:>10.3f} {a2:>10.3f} {t1:>10.3f} {t2:>10.3f}")
print(f"  {'TOTAL':<8} {'':>10} {'':>10} {'':>10} {'':>10} {sum_1:>10.3f} {sum_2:>10.3f}")
print(f"  Delta available N at day+30: {sum_2 - sum_1:+.3f} kg ({(sum_2 - sum_1)/sum_1*100:+.1f}%)")

print()
print("=== 4) Layer 0 total N on rain days (sim rows 1, 22, 33) ===")
print(f"  {'Sim row':<10} {'run1_L0_N':>12} {'run2_L0_N':>12} {'delta':>10}")
for row in [1, 22, 33]:
    n1 = df1[nitrate_1[0]].iloc[row] + df1[ammonium_1[0]].iloc[row]
    n2 = df2[nitrate_2[0]].iloc[row] + df2[ammonium_2[0]].iloc[row]
    print(f"  {row:<10} {n1:>12.3f} {n2:>12.3f} {n2 - n1:>+10.3f}")

print()
print("=== DECISION SIGNAL ===")
if r2 < r1 and sum_2 >= sum_1 * 0.9:
    print(f"  DELAY WINS: runoff cut by {r1 - r2:.2f} kg ({(1 - r2/r1)*100:.1f}%) with only {(sum_1 - sum_2)/sum_1*100 if sum_1 > 0 else 0:.1f}% loss in day-30 available N")
elif r2 < r1:
    print(f"  DELAY REDUCES RUNOFF ({(1 - r2/r1)*100:.1f}%) but at cost of {(sum_1 - sum_2)/sum_1*100:.1f}% less day-30 available N")
elif r2 > r1:
    print(f"  DELAY INCREASES RUNOFF by {(r2/r1 - 1)*100:.1f}% — hypothesis rejected for this weather scenario")
else:
    print(f"  Runoff unchanged; day-30 available N delta {(sum_2 - sum_1)/sum_1*100:+.1f}%")
