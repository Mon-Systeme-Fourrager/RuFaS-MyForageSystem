"""
Multi-year robustness sweep — 6 years × 5 delays = 30 RUFAS simulations.

For each (year, delay) combo:
  1. Generate per-year config (start/end dates)
  2. Generate per-(year, delay) manure schedule (year and day)
  3. Generate metadata catalog pointing at both
  4. Generate task JSON with unique output_prefix
  5. Generate root wrapper
  6. Spawn a fresh Python subprocess to run TaskManager.start()

Sweep configs land in prototype_msf/sweep_config/multiyr/.
Simulation logs land in prototype_msf/sweep_output/multiyr/y{Y}_d{D}/.
Per-run CSVs land at output/CSVs/msf_multiyr_y{Y}_d{D}_saved_variables_*.csv.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PROTO = REPO_ROOT / "prototype_msf"
SWEEP_CFG = PROTO / "sweep_config" / "multiyr"
BASE_METADATA_PATH = PROTO / "prototype_metadata.json"
BASE_CONFIG_PATH = PROTO / "prototype_config.json"
BASE_MANURE_PATH = PROTO / "prototype_manure_schedule.json"
PYTHON = r"C:\Users\ktcar\anaconda3\envs\rufas\python.exe"
RUNNER = PROTO / "_multiyr_runner.py"

YEARS = [2020, 2003, 2002, 2010, 2007, 2013]
DELAYS = [0, 1, 2, 3, 4]

SWEEP_CFG.mkdir(parents=True, exist_ok=True)

with open(BASE_METADATA_PATH) as f:
    base_metadata = json.load(f)
with open(BASE_CONFIG_PATH) as f:
    base_config = json.load(f)
with open(BASE_MANURE_PATH) as f:
    base_manure = json.load(f)


def make_config(year: int) -> None:
    cfg = copy.deepcopy(base_config)
    cfg["start_date"] = f"{year}:202"
    cfg["end_date"] = f"{year}:237"
    p = SWEEP_CFG / f"config_year{year}.json"
    with open(p, "w") as f:
        json.dump(cfg, f, indent=2)


def make_manure(year: int, day: int) -> None:
    m = copy.deepcopy(base_manure)
    m["years"] = [year]
    m["days"] = [day]
    p = SWEEP_CFG / f"manure_year{year}_day{day}.json"
    with open(p, "w") as f:
        json.dump(m, f, indent=2)


def make_metadata(year: int, day: int) -> None:
    md = copy.deepcopy(base_metadata)
    md["files"]["config"]["path"] = f"prototype_msf/sweep_config/multiyr/config_year{year}.json"
    schedule_path = f"prototype_msf/sweep_config/multiyr/manure_year{year}_day{day}.json"
    md["files"]["manure_schedule_1"]["path"] = schedule_path
    md["files"]["manure_schedule_1"]["description"] = f"Multi-year — year {year}, day {day}"
    md["files"]["manure_schedule_2"]["path"] = schedule_path
    md["files"]["manure_schedule_2"]["description"] = f"Multi-year — year {year}, day {day}"
    p = SWEEP_CFG / f"metadata_year{year}_day{day}.json"
    with open(p, "w") as f:
        json.dump(md, f, indent=2)


def make_task(year: int, day: int) -> None:
    task = {
        "parallel_workers": 1,
        "tasks": [
            {
                "task_type": "SIMULATION_SINGLE_RUN",
                "metadata_file_path": f"prototype_msf/sweep_config/multiyr/metadata_year{year}_day{day}.json",
                "output_prefix": f"msf_multiyr_y{year}_d{day}",
                "log_verbosity": "warnings",
                "random_seed": 42,
                "exclude_info_maps": True,
                "cross_validation_file_paths": [],
            }
        ],
    }
    p = SWEEP_CFG / f"task_year{year}_day{day}.json"
    with open(p, "w") as f:
        json.dump(task, f, indent=2)


def make_root(year: int, day: int) -> None:
    root = {
        "files": {
            "tasks": {
                "title": "Task manager data",
                "description": f"Multi-year sweep — year {year}, day {day}.",
                "path": f"prototype_msf/sweep_config/multiyr/task_year{year}_day{day}.json",
                "type": "json",
                "properties": "tasks_properties",
            }
        }
    }
    p = SWEEP_CFG / f"root_year{year}_day{day}.json"
    with open(p, "w") as f:
        json.dump(root, f, indent=2)


def run_one(year: int, day: int) -> tuple[int, str, str]:
    make_config(year)
    make_manure(year, day)
    make_metadata(year, day)
    make_task(year, day)
    make_root(year, day)
    result = subprocess.run(
        [PYTHON, str(RUNNER), str(year), str(day)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    return result.returncode, result.stdout, result.stderr


print(f"=== Multi-year sweep — {len(YEARS)} years × {len(DELAYS)} delays = {len(YEARS) * len(DELAYS)} runs ===")
print(f"    Years:  {YEARS}")
print(f"    Delays: {DELAYS}")
print()

n = 0
n_ok = 0
for year in YEARS:
    for delay in DELAYS:
        day = 202 + delay
        n += 1
        rc, out, err = run_one(year, day)
        if rc == 0:
            finished = [line for line in out.splitlines() if "Finished task: 1/1" in line]
            marker = finished[-1].strip() if finished else "exit 0 (no completion marker)"
            n_ok += 1
            print(f"  [{n:>2}/30] y{year} d{day}: {marker}")
        else:
            print(f"  [{n:>2}/30] y{year} d{day}: FAILED (rc={rc})")
            print(f"          stderr tail: {err[-400:]}")

print()
if n_ok == n:
    print(f"=== ALL {n} RUNS SUCCESSFUL ===")
    print("Run analyze_multiyr.py to build the summary table and plot.")
else:
    print(f"=== {n_ok}/{n} RUNS SUCCESSFUL — some failed ===")
    sys.exit(1)
