"""
Parametric sweep — 5 simulations, manure application day varied 202..206.

For each day:
  1. Generate metadata catalog (based on prototype_metadata.json) pointing at the
     day-specific manure schedule.
  2. Generate a task JSON with unique output_prefix so all 5 CSVs coexist.
  3. Generate a root wrapper.
  4. Spawn a fresh Python subprocess to run TaskManager.start() — one process per
     simulation, guaranteeing state isolation.

Sweep configs are written to prototype_msf/sweep_config/.
Simulation logs land in prototype_msf/sweep_output/day{N}/.
Actual per-day CSV output goes to output/CSVs/ (RUFAS default).
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PROTO_DIR = REPO_ROOT / "prototype_msf"
SWEEP_CFG = PROTO_DIR / "sweep_config"
BASE_METADATA = PROTO_DIR / "prototype_metadata.json"
PYTHON = r"C:\Users\ktcar\anaconda3\envs\rufas\python.exe"

DAYS = [202, 203, 204, 205, 206]

SWEEP_CFG.mkdir(parents=True, exist_ok=True)

with open(BASE_METADATA) as f:
    base_metadata = json.load(f)


def make_metadata(day: int) -> Path:
    md = copy.deepcopy(base_metadata)
    schedule_path = f"prototype_msf/prototype_manure_schedule_day{day}.json"
    md["files"]["manure_schedule_1"]["path"] = schedule_path
    md["files"]["manure_schedule_1"]["description"] = f"Sweep — apply day {day}."
    md["files"]["manure_schedule_2"]["path"] = schedule_path
    md["files"]["manure_schedule_2"]["description"] = f"Sweep — apply day {day}."
    p = SWEEP_CFG / f"metadata_day{day}.json"
    with open(p, "w") as f:
        json.dump(md, f, indent=2)
    return p


def make_task(day: int) -> Path:
    task = {
        "parallel_workers": 1,
        "tasks": [
            {
                "task_type": "SIMULATION_SINGLE_RUN",
                "metadata_file_path": f"prototype_msf/sweep_config/metadata_day{day}.json",
                "output_prefix": f"msf_prototype_day{day}",
                "log_verbosity": "warnings",
                "random_seed": 42,
                "exclude_info_maps": True,
                "cross_validation_file_paths": [],
            }
        ],
    }
    p = SWEEP_CFG / f"task_day{day}.json"
    with open(p, "w") as f:
        json.dump(task, f, indent=2)
    return p


def make_root(day: int) -> Path:
    root = {
        "files": {
            "tasks": {
                "title": "Task manager data",
                "description": f"Sweep run — apply day {day}.",
                "path": f"prototype_msf/sweep_config/task_day{day}.json",
                "type": "json",
                "properties": "tasks_properties",
            }
        }
    }
    p = SWEEP_CFG / f"root_day{day}.json"
    with open(p, "w") as f:
        json.dump(root, f, indent=2)
    return p


RUNNER_CODE_TEMPLATE = textwrap.dedent("""\
    import os
    import sys
    from pathlib import Path

    REPO_ROOT = Path(r"{repo_root}")
    sys.path.insert(0, str(REPO_ROOT))
    os.chdir(REPO_ROOT)

    filter_bogus = REPO_ROOT / "output" / "output_filters" / "_csv_all_variables.txt"
    filter_good = REPO_ROOT / "output" / "output_filters" / "csv_all_variables.txt"
    if filter_bogus.exists() and not filter_good.exists():
        filter_bogus.rename(filter_good)

    from RUFAS.output_manager import LogVerbosity
    from RUFAS.task_manager import TaskManager

    tm = TaskManager()
    tm.start(
        metadata_path=Path("prototype_msf/sweep_config/root_day{day}.json"),
        verbosity=LogVerbosity.WARNINGS,
        exclude_info_maps=True,
        output_directory=Path("prototype_msf/sweep_output/day{day}"),
        logs_directory=Path("prototype_msf/sweep_output/day{day}/logs"),
        clear_output_directory=True,
        produce_graphics=False,
        suppress_log_files=False,
        metadata_depth_limit=None,
    )
""")


def run_one(day: int) -> int:
    make_metadata(day)
    make_task(day)
    make_root(day)
    runner_path = SWEEP_CFG / f"_runner_day{day}.py"
    with open(runner_path, "w") as f:
        f.write(RUNNER_CODE_TEMPLATE.format(repo_root=str(REPO_ROOT), day=day))
    print(f"  Day {day}: starting subprocess...")
    result = subprocess.run(
        [PYTHON, str(runner_path)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    if result.returncode == 0:
        # Look for the "Finished task: 1/1 with 0 error(s)" line as success marker
        finished = [line for line in result.stdout.splitlines() if "Finished task: 1/1" in line]
        if finished:
            print(f"  Day {day}: {finished[-1].strip()}")
        else:
            print(f"  Day {day}: exit 0 but no completion marker (check logs)")
    else:
        print(f"  Day {day}: FAILED (exit {result.returncode})")
        print(f"    stderr tail: {result.stderr[-400:]}")
    return result.returncode


print(f"=== RUFAS parametric sweep — {len(DAYS)} runs, days {DAYS} ===")
print(f"    Config dir: {SWEEP_CFG}")
print()
exit_codes = []
for d in DAYS:
    exit_codes.append(run_one(d))

print()
if all(rc == 0 for rc in exit_codes):
    print(f"=== ALL {len(DAYS)} RUNS SUCCESSFUL ===")
    print("Run sweep_results.py to build the comparison table.")
else:
    failed = [DAYS[i] for i, rc in enumerate(exit_codes) if rc != 0]
    print(f"=== FAILURES on days: {failed} ===")
    sys.exit(1)
