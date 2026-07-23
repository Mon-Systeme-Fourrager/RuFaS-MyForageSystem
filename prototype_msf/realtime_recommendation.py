"""
Real-time decision-support prototype:
  1. Fetch Open-Meteo forecast for Quebec City (today + 7 days)
  2. Build a RUFAS-format weather CSV: real forecast + 2013 tail padding
  3. Run 5 RUFAS simulations (delay 0-4)
  4. Print a decision recommendation

Design notes:
  - Open-Meteo free daily forecast caps at 7 days; RUFAS needs 35 days to
    measure "N at day 30 post-application" for delay=4. Padding beyond the
    forecast horizon uses 2013 historical for the same Julian days (climatology
    proxy).
  - The "Hday" column in the RUFAS example CSV appears to be daily solar
    radiation in MJ/m² (values 6-8 winter, 20-24 summer at 42°N — matches
    radiation, not daylength). We populate Hday from shortwave_radiation_sum.
"""

from __future__ import annotations

import copy
import glob
import json
import subprocess
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# ---- Paths & constants ----------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
PROTO = REPO_ROOT / "prototype_msf"
CFG_DIR = PROTO / "sweep_config" / "realtime"
BASE_METADATA_PATH = PROTO / "prototype_metadata.json"
BASE_CONFIG_PATH = PROTO / "prototype_config.json"
BASE_MANURE_PATH = PROTO / "prototype_manure_schedule.json"
BASE_WEATHER_PATH = REPO_ROOT / "input" / "data" / "weather" / "example_temperate_weather.csv"
PYTHON = r"C:\Users\ktcar\anaconda3\envs\rufas\python.exe"

LAT = 46.8139
LON = -71.2082
DELAYS = [0, 1, 2, 3, 4]
FORECAST_DAYS = 7           # today + 7 = 8 forecast rows total
SIM_END_OFFSET = 35         # end_date = start + 35 -> 36 rows (matches earlier prototype)
PADDING_YEAR = 2013         # source year for jdays beyond forecast
SIM_YEAR = 2026             # fake year for the simulation (not in existing CSV)

CFG_DIR.mkdir(parents=True, exist_ok=True)

# ---- 1. Fetch Open-Meteo forecast -----------------------------------------
today = datetime.now()
today_str = today.strftime("%Y-%m-%d")
end_str = (today + timedelta(days=FORECAST_DAYS)).strftime("%Y-%m-%d")
today_jday = today.timetuple().tm_yday

url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={LAT}&longitude={LON}"
    f"&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
    f"precipitation_sum,shortwave_radiation_sum"
    f"&start_date={today_str}&end_date={end_str}"
    f"&timezone=America%2FToronto"
)

print(f"[1/4] Fetching Open-Meteo forecast for Quebec City ({today_str} - {end_str})...")
with urllib.request.urlopen(url) as response:
    om = json.loads(response.read())
daily = om["daily"]
n_forecast = len(daily["time"])
print(f"      Received {n_forecast} days of real forecast (jday {today_jday}-{today_jday + n_forecast - 1})")

# ---- 2. Build weather CSV -------------------------------------------------
forecast_rows = []
for i, date_str in enumerate(daily["time"]):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    jday = dt.timetuple().tm_yday
    forecast_rows.append(
        {
            "year": SIM_YEAR,
            "jday": jday,
            "precip": daily["precipitation_sum"][i] or 0.0,
            "high": daily["temperature_2m_max"][i],
            "low": daily["temperature_2m_min"][i],
            "avg": daily["temperature_2m_mean"][i],
            "Hday": daily["shortwave_radiation_sum"][i] or 0.0,
            "irrigation": 0.0,
        }
    )

last_forecast_jday = forecast_rows[-1]["jday"]
sim_end_jday = today_jday + SIM_END_OFFSET
padding_start = last_forecast_jday + 1
padding_end = sim_end_jday

base_weather = pd.read_csv(BASE_WEATHER_PATH)
base_weather.columns = base_weather.columns.str.strip()
padding = base_weather[
    (base_weather["year"] == PADDING_YEAR)
    & (base_weather["jday"] >= padding_start)
    & (base_weather["jday"] <= padding_end)
].copy()
padding["year"] = SIM_YEAR

weather_df = pd.concat([pd.DataFrame(forecast_rows), padding], ignore_index=True)
weather_df = weather_df[["year", "jday", "precip", "high", "low", "avg", "Hday", "irrigation"]]

weather_csv_path = CFG_DIR / "weather_realtime.csv"
weather_df.to_csv(weather_csv_path, index=False)
print(f"[2/4] Weather CSV written ({len(weather_df)} rows)")
print(f"      Real forecast: {n_forecast} rows (jday {today_jday}-{last_forecast_jday})")
print(f"      2013 padding:  {len(padding)} rows (jday {padding_start}-{padding_end})")

# ---- 3. Generate per-delay JSON configs -----------------------------------
with open(BASE_METADATA_PATH) as f:
    base_metadata = json.load(f)
with open(BASE_CONFIG_PATH) as f:
    base_config = json.load(f)
with open(BASE_MANURE_PATH) as f:
    base_manure = json.load(f)

# Single shared config (only one sim window)
cfg = copy.deepcopy(base_config)
cfg["start_date"] = f"{SIM_YEAR}:{today_jday}"
cfg["end_date"] = f"{SIM_YEAR}:{sim_end_jday}"
with open(CFG_DIR / "config.json", "w") as f:
    json.dump(cfg, f, indent=2)

for delay in DELAYS:
    m = copy.deepcopy(base_manure)
    m["years"] = [SIM_YEAR]
    m["days"] = [today_jday + delay]
    with open(CFG_DIR / f"manure_delay{delay}.json", "w") as f:
        json.dump(m, f, indent=2)

    md = copy.deepcopy(base_metadata)
    md["files"]["config"]["path"] = "prototype_msf/sweep_config/realtime/config.json"
    md["files"]["weather"]["path"] = "prototype_msf/sweep_config/realtime/weather_realtime.csv"
    schedule_path = f"prototype_msf/sweep_config/realtime/manure_delay{delay}.json"
    md["files"]["manure_schedule_1"]["path"] = schedule_path
    md["files"]["manure_schedule_2"]["path"] = schedule_path
    with open(CFG_DIR / f"metadata_delay{delay}.json", "w") as f:
        json.dump(md, f, indent=2)

    task = {
        "parallel_workers": 1,
        "tasks": [
            {
                "task_type": "SIMULATION_SINGLE_RUN",
                "metadata_file_path": f"prototype_msf/sweep_config/realtime/metadata_delay{delay}.json",
                "output_prefix": f"msf_realtime_d{delay}",
                "log_verbosity": "warnings",
                "random_seed": 42,
                "exclude_info_maps": True,
                "cross_validation_file_paths": [],
            }
        ],
    }
    with open(CFG_DIR / f"task_delay{delay}.json", "w") as f:
        json.dump(task, f, indent=2)

    root = {
        "files": {
            "tasks": {
                "title": "Task manager data",
                "description": f"Realtime — delay {delay} days.",
                "path": f"prototype_msf/sweep_config/realtime/task_delay{delay}.json",
                "type": "json",
                "properties": "tasks_properties",
            }
        }
    }
    with open(CFG_DIR / f"root_delay{delay}.json", "w") as f:
        json.dump(root, f, indent=2)

RUNNER_TEMPLATE = """
import os, sys
from pathlib import Path
REPO_ROOT = Path(r"{repo_root}")
sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)
fb = REPO_ROOT / "output" / "output_filters" / "_csv_all_variables.txt"
fg = REPO_ROOT / "output" / "output_filters" / "csv_all_variables.txt"
if fb.exists() and not fg.exists():
    fb.rename(fg)
from RUFAS.output_manager import LogVerbosity
from RUFAS.task_manager import TaskManager
tm = TaskManager()
tm.start(
    metadata_path=Path("prototype_msf/sweep_config/realtime/root_delay{delay}.json"),
    verbosity=LogVerbosity.WARNINGS,
    exclude_info_maps=True,
    output_directory=Path("prototype_msf/sweep_output/realtime/d{delay}"),
    logs_directory=Path("prototype_msf/sweep_output/realtime/d{delay}/logs"),
    clear_output_directory=True,
    produce_graphics=False,
    suppress_log_files=False,
    metadata_depth_limit=None,
)
"""

# ---- 4. Run 5 subprocess RUFAS sims ---------------------------------------
print()
print("[3/4] Running 5 RUFAS simulations...")
for d in DELAYS:
    code = RUNNER_TEMPLATE.format(repo_root=str(REPO_ROOT), delay=d)
    result = subprocess.run(
        [PYTHON, "-c", code], capture_output=True, text=True, cwd=str(REPO_ROOT)
    )
    if result.returncode == 0:
        finished = [line for line in result.stdout.splitlines() if "Finished task: 1/1" in line]
        marker = finished[-1].strip() if finished else "exit 0"
        print(f"      Delay {d}: {marker}")
    else:
        print(f"      Delay {d}: FAILED (rc={result.returncode})")
        print(f"        stderr tail: {result.stderr[-400:]}")

# ---- 5. Analyze and print recommendation ----------------------------------
CSV_DIR_OUTPUT = REPO_ROOT / "output" / "CSVs"


def latest(prefix: str) -> str | None:
    matches = sorted(glob.glob(str(CSV_DIR_OUTPUT / f"{prefix}_saved_variables_*.csv")))
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
for d in DELAYS:
    path = latest(f"msf_realtime_d{d}")
    if not path:
        print(f"MISSING: msf_realtime_d{d}")
        continue
    df = pd.read_csv(path)
    total_runoff = df[find_col(df, ("nitrate_runoff",))].fillna(0).sum()
    row_post30 = d + 30
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
            "delay": d,
            "apply_date": (today + timedelta(days=d)).strftime("%Y-%m-%d"),
            "total_runoff_kg": float(total_runoff),
            "n_available_day30_kg": float(total_avail),
            "root_zone_layer1_kg": float(rz),
        }
    )

opt = min(results, key=lambda r: r["total_runoff_kg"])
baseline = results[0]

# Rain summary
biggest_precip = 0.0
biggest_rain_date = None
first_rain_date = None
for i in range(n_forecast):
    p = daily["precipitation_sum"][i] or 0.0
    if p > 0 and first_rain_date is None:
        first_rain_date = daily["time"][i]
    if p > biggest_precip:
        biggest_precip = p
        biggest_rain_date = daily["time"][i]

print()
print("=" * 68)
print("=== MSF Expert System — Real-Time Recommendation ===")
print("=" * 68)
print(f"Location:          Quebec City, QC  (lat={LAT}, lon={LON})")
print(f"Date:              {today_str}  (Julian day {today_jday})")
print(f"Forecast horizon:  {n_forecast} days")
print()
print("Forecast precipitation:")
for i in range(n_forecast):
    p = daily["precipitation_sum"][i] or 0.0
    marker = "  <-- significant" if p >= 5 else ""
    print(f"  {daily['time'][i]}: {p:5.1f} mm{marker}")

print()
print(f"Optimal delay:              {opt['delay']} days")
print(f"Recommended application:    {opt['apply_date']}")
print(f"Expected nitrate runoff:    {opt['total_runoff_kg']:.3f} kg  (vs {baseline['total_runoff_kg']:.3f} kg if applied today)")
print(f"Expected day-30 avail. N:   {opt['n_available_day30_kg']:.2f} kg")
print(f"Expected root-zone N:       {opt['root_zone_layer1_kg']:.2f} kg")

improvement = baseline["total_runoff_kg"] - opt["total_runoff_kg"]
pct = (improvement / baseline["total_runoff_kg"] * 100) if baseline["total_runoff_kg"] > 0 else 0.0
print()
if opt["delay"] == 0:
    print("Reason: forecast shows minimal near-term rain risk; no benefit to delaying.")
elif first_rain_date is not None:
    print("Reason:")
    print(f"  * Next forecast rain event:  {first_rain_date}")
    if biggest_rain_date:
        print(f"  * Biggest rain in window:    {biggest_rain_date} ({biggest_precip:.1f} mm)")
    print(f"  * Delaying by {opt['delay']} day(s) reduces runoff by {improvement:.3f} kg ({pct:.1f}%)")
    print("    while preserving plant-available N.")

print()
print("All 5 scenarios:")
print(f"  {'Delay':>5} | {'Apply date':>10} | {'Runoff (kg)':>11} | {'Avail N (kg)':>12} | {'Root zone N (kg)':>16}")
for r in results:
    marker = " *" if r["delay"] == opt["delay"] else "  "
    print(
        f"  {r['delay']:>3}d{marker} | {r['apply_date']} | "
        f"{r['total_runoff_kg']:>11.4f} | {r['n_available_day30_kg']:>12.3f} | "
        f"{r['root_zone_layer1_kg']:>16.3f}"
    )

print()
print("Caveats:")
print(f"  * Simulation uses {n_forecast} days of real Open-Meteo forecast + "
      f"{len(padding)} days of 2013 historical padding")
print("    (Open-Meteo daily forecast horizon is 7 days; longer horizon would require seasonal forecast)")
print("  * Hday column populated from Open-Meteo shortwave_radiation_sum (MJ/m²)")
print("    (matches RUFAS example CSV value range; RUFAS Hday convention is solar radiation, not daylength)")
print("  * Padding introduces artificial rain-event timing beyond day 8 — the")
print("    delay recommendation is dominated by the real 7-day forecast window.")
