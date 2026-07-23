import glob

import pandas as pd

csv_files = glob.glob(r"C:\Proyectos\RuFaS-MyForageSystem\output\CSVs\*.csv")
df = pd.read_csv(sorted(csv_files)[-1])

# Find soil layer N columns for field_1 only
layer_cols = [c for c in df.columns if "soil_layer" in c.lower() and "field_1" in c.lower()]
avail_n = [
    c
    for c in layer_cols
    if "available_nitrogen" in c.lower() or "nitrate_content" in c.lower() or "ammonium" in c.lower()
]

print("Soil N columns found:")
for c in avail_n:
    print(f"  {c}")
print()
print("Daily soil N availability (35 days):")
print(df[avail_n].round(3).to_string())
print()
print("=== KEY: N available at day 30 ===")
print(df[avail_n].iloc[30].round(3))
