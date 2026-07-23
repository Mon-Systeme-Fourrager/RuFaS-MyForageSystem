import glob

import pandas as pd

csv_files = glob.glob(r"C:\Proyectos\RuFaS-MyForageSystem\output\CSVs\*.csv")
df = pd.read_csv(sorted(csv_files)[-1])

# Find N-related columns
n_cols = [
    c
    for c in df.columns
    if any(x in c.lower() for x in ["nitrogen", "nitrate", "ammonium", "uptake", "manure_n"])
]

print("=== SANITY CHECK — N Availability after manure application ===")
print(f"Total days: {len(df)}")
print(f"N columns found: {len(n_cols)}")
print()
print("First 5 N columns over 35 days:")
print(df[n_cols[:5]].round(2).to_string())
print()
print("=== KEY STATS ===")
for c in n_cols[:5]:
    print(f"{c}: min={df[c].min():.2f}, max={df[c].max():.2f}, day1={df[c].iloc[0]:.2f}, day35={df[c].iloc[-1]:.2f}")
