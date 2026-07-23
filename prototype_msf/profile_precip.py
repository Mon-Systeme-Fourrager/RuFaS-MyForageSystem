"""
Profile July 21 - August 25 precipitation across all years in the weather CSV.
Used to select representative years (wet / median / dry) for the multi-year
robustness sweep.
"""

import pandas as pd

df = pd.read_csv(r"C:\Proyectos\RuFaS-MyForageSystem\input\data\weather\example_temperate_weather.csv")
df.columns = df.columns.str.strip()

# Filter July-August window (days 202-237) for each year
window = df[(df["jday"] >= 202) & (df["jday"] <= 237)]
precip_by_year = window.groupby("year")["precip"].sum().reset_index()
precip_by_year.columns = ["year", "total_precip_mm"]
precip_by_year = precip_by_year.sort_values("total_precip_mm")

print("Precipitation July 21 - Aug 25 by year (sorted):")
print(precip_by_year.to_string(index=False))
print()
print(f"Mean: {precip_by_year.total_precip_mm.mean():.1f} mm")
print(f"Std:  {precip_by_year.total_precip_mm.std():.1f} mm")
print(f"Min:  {precip_by_year.total_precip_mm.min():.1f} mm ({precip_by_year.iloc[0].year:.0f})")
print(f"Max:  {precip_by_year.total_precip_mm.max():.1f} mm ({precip_by_year.iloc[-1].year:.0f})")
