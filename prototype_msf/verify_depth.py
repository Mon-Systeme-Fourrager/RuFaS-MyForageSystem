"""
Verify RUFAS actually recorded application_depth = 30 mm for the injection run.
If application_depth in the injection CSV is 0.0 (same as broadcast), the model
silently ignored our input and the runoff result is meaningless.
If it's 30.0, RUFAS accepted the value and the model's runoff behavior is a real
model limitation (not a config error).
"""

import glob

import pandas as pd

CSV_DIR = r"C:\Proyectos\RuFaS-MyForageSystem\output\CSVs"


def latest(prefix: str) -> str:
    return sorted(glob.glob(f"{CSV_DIR}\\{prefix}_saved_variables_*.csv"))[-1]


df_broad = pd.read_csv(latest("msf_prototype"))
df_inject = pd.read_csv(latest("msf_prototype_injection"))


def find_col(df, must_contain):
    for c in df.columns:
        lc = c.lower()
        if all(m.lower() in lc for m in must_contain) and "field_1" in lc:
            return c
    return None


print("=== Verifying RUFAS respected the injection parameters ===")
print()
print("On application day (sim row 0):")
print()

# What RUFAS RECORDED as actually applied
for label, event in [("APPLIED (RUFAS recorded)", "manure_application"), ("REQUESTED (from our schedule)", "manure_request")]:
    print(f"--- {label} ---")
    for parm in ["application_depth", "surface_remainder_fraction", "nitrogen"]:
        col_b = find_col(df_broad, (event, parm))
        col_i = find_col(df_inject, (event, parm))
        if col_b is None or col_i is None:
            print(f"  {parm}: column not found")
            continue
        v_b = df_broad[col_b].iloc[0]
        v_i = df_inject[col_i].iloc[0]
        print(f"  {parm:35s}  broadcast={v_b!s:>10}  injection={v_i!s:>10}")
    print()

print("=== VERDICT ===")
depth_col_b = find_col(df_broad, ("manure_application", "application_depth"))
depth_col_i = find_col(df_inject, ("manure_application", "application_depth"))
surf_col_b = find_col(df_broad, ("manure_application", "surface_remainder_fraction"))
surf_col_i = find_col(df_inject, ("manure_application", "surface_remainder_fraction"))
d_b = df_broad[depth_col_b].iloc[0]
d_i = df_inject[depth_col_i].iloc[0]
s_b = df_broad[surf_col_b].iloc[0]
s_i = df_inject[surf_col_i].iloc[0]

if d_i == 30.0 and s_i == 0.2 and d_b == 0.0 and s_b == 1.0:
    print("  CONFIRMED: RUFAS recorded application_depth=30.0 and surface_remainder=0.2 for injection.")
    print("  The +52% runoff result reflects a MODEL LIMITATION, not a config error.")
elif d_i == 0.0:
    print("  BUG: RUFAS ignored our application_depth input (still 0.0). The comparison is invalid.")
else:
    print(f"  UNEXPECTED VALUES: broadcast depth={d_b} surface={s_b}, injection depth={d_i} surface={s_i}")
