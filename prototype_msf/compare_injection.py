"""
Compare RUFAS prototype runs:
  Run 1  (BROADCAST):  application_depths=[0.0],  surface_remainder_fractions=[1.0]
  Run 3  (INJECTION):  application_depths=[30.0], surface_remainder_fractions=[0.2]

Both apply on sim day 0 (calendar 202, 2013-07-21).
Both share the same weather and field/soil/crop configuration.
Only manure application METHOD differs.
"""

import glob
import re

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


def find_col(df, must_contain, must_also_contain=("field_1",)):
    for c in df.columns:
        lc = c.lower()
        if all(needle.lower() in lc for needle in must_contain) and all(m.lower() in lc for m in must_also_contain):
            return c
    return None


def layer_col(df, kind, layer):
    for c in df.columns:
        if kind in c.lower() and "field_1" in c.lower() and f"layer='{layer}'" in c:
            return c
    raise KeyError(f"{kind} layer={layer} column not found")


print("=== Loading CSVs ===")
df_broad = load("msf_prototype")
df_inject = load("msf_prototype_injection")

print()
print("=== Discovery: volatilization / gas-loss columns ===")
vol_patterns = ["volatiliz", "nh3_gas", "ammonia_gas", "ammonia_loss", "n2o", "denitrif"]
vol_cols = []
for pat in vol_patterns:
    for c in df_broad.columns:
        if pat in c.lower() and "field_1" in c.lower():
            vol_cols.append((pat, c))
if vol_cols:
    print(f"  Found {len(vol_cols)} gas-loss columns:")
    for pat, c in vol_cols:
        print(f"    [{pat}] {c}")
else:
    print("  No columns matching {volatiliz, nh3_gas, ammonia_gas, ammonia_loss, n2o, denitrif}")
    print("  Volatilization may be reported at soil-cycle module (soil-layer scope), not field scope.")
    # Try broader search
    print()
    print("  Broader grep for 'gas' or 'emitted' columns (may not exist):")
    for c in df_broad.columns:
        lc = c.lower()
        if ("gas" in lc or "emit" in lc) and "field_1" in lc:
            print(f"    {c}")

print()
print("=== 1) Total nitrate runoff over 35-day window ===")
runoff_col = find_col(df_broad, ("nitrate_runoff",))
r_broad = df_broad[runoff_col].fillna(0).sum()
r_inject = df_inject[runoff_col].fillna(0).sum()
print(f"  Broadcast:   {r_broad:.4f} kg over 10 ha = {r_broad/10:.5f} kg/ha")
print(f"  Injection:   {r_inject:.4f} kg over 10 ha = {r_inject/10:.5f} kg/ha")
delta = r_inject - r_broad
pct = (delta / r_broad * 100) if r_broad > 0 else float("nan")
print(f"  Delta:       {delta:+.4f} kg  ({pct:+.1f}% change)")

print()
print("=== 2) Runoff by day — showing only rows with non-zero runoff ===")
r1 = df_broad[runoff_col].fillna(0)
r2 = df_inject[runoff_col].fillna(0)
cmp = pd.DataFrame({
    "sim_row": range(len(r1)),
    "broadcast_kg": r1.round(4).values,
    "injection_kg": r2.round(4).values,
})
cmp["delta"] = (cmp["injection_kg"] - cmp["broadcast_kg"]).round(4)
non_zero = cmp[(cmp["broadcast_kg"] != 0) | (cmp["injection_kg"] != 0)]
print(non_zero.to_string(index=False))

print()
print("=== 3) N available at day 30 post-application (both apply on row 0) ===")
row_30 = 30
print(f"  {'Layer':<8} {'brd_nit':>10} {'inj_nit':>10} {'brd_amm':>10} {'inj_amm':>10} {'brd_tot':>10} {'inj_tot':>10}")
sum_b = 0.0
sum_i = 0.0
for i in range(4):
    n_b = df_broad[layer_col(df_broad, "nitrate_content", i)].iloc[row_30]
    n_i = df_inject[layer_col(df_inject, "nitrate_content", i)].iloc[row_30]
    a_b = df_broad[layer_col(df_broad, "ammonium_content", i)].iloc[row_30]
    a_i = df_inject[layer_col(df_inject, "ammonium_content", i)].iloc[row_30]
    t_b = n_b + a_b
    t_i = n_i + a_i
    sum_b += t_b
    sum_i += t_i
    print(f"  {i:<8} {n_b:>10.3f} {n_i:>10.3f} {a_b:>10.3f} {a_i:>10.3f} {t_b:>10.3f} {t_i:>10.3f}")
print(f"  {'TOTAL':<8} {'':>10} {'':>10} {'':>10} {'':>10} {sum_b:>10.3f} {sum_i:>10.3f}")
delta_avail = sum_i - sum_b
pct_avail = (delta_avail / sum_b * 100) if sum_b > 0 else float("nan")
print(f"  Delta available N: {delta_avail:+.3f} kg ({pct_avail:+.1f}%)")

print()
print("=== 4) Ammonium on days 0-4 — 'hot window' surface concentration ===")
print(f"  {'Sim row':<10} {'brd_L0_NH4':>12} {'inj_L0_NH4':>12} {'brd_L1_NH4':>12} {'inj_L1_NH4':>12}")
for row in range(5):
    a0_b = df_broad[layer_col(df_broad, "ammonium_content", 0)].iloc[row]
    a0_i = df_inject[layer_col(df_inject, "ammonium_content", 0)].iloc[row]
    a1_b = df_broad[layer_col(df_broad, "ammonium_content", 1)].iloc[row]
    a1_i = df_inject[layer_col(df_inject, "ammonium_content", 1)].iloc[row]
    print(f"  {row:<10} {a0_b:>12.3f} {a0_i:>12.3f} {a1_b:>12.3f} {a1_i:>12.3f}")

print()
if vol_cols:
    print("=== 5) Volatilization / gas-loss totals over 35 days ===")
    for pat, c in vol_cols:
        v_b = df_broad[c].fillna(0).sum()
        v_i = df_inject[c].fillna(0).sum()
        d = v_i - v_b
        p = (d / v_b * 100) if v_b > 0 else float("nan")
        print(f"  [{pat}] {c.split('.')[-1] if '.' in c else c}")
        print(f"    Broadcast: {v_b:>10.4f}  Injection: {v_i:>10.4f}  Delta: {d:+.4f} ({p:+.1f}%)")

print()
print("=== DECISION SIGNAL ===")
runoff_change = (1 - r_inject/r_broad) * 100 if r_broad > 0 else 0
avail_change = pct_avail
if r_inject < r_broad * 0.5 and abs(avail_change) < 15:
    print(f"  INJECTION STRONGLY WINS: runoff cut by {runoff_change:.1f}%, day-30 available N essentially unchanged ({avail_change:+.1f}%)")
elif r_inject < r_broad and avail_change >= 0:
    print(f"  INJECTION WINS: runoff cut by {runoff_change:.1f}%, day-30 available N {avail_change:+.1f}%")
elif r_inject < r_broad:
    print(f"  INJECTION reduces runoff by {runoff_change:.1f}% but at cost of {-avail_change:.1f}% less day-30 available N")
else:
    print(f"  Runoff change {runoff_change:+.1f}%, available N change {avail_change:+.1f}% — unexpected result")
