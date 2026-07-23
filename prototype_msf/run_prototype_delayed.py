"""
MSF Expert System — Prototype 1, delayed variant
Question: What if I wait 3 days (skip the day-1 rain) before applying?

Same 35-day window (2013:202 -> 2013:237); manure event moved from day 202 to day 205.
The day-203 rain now falls BEFORE the application — 2 days of dry soil ingesting the manure.
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)

# Defensive fix for RUFAS's default filter file (leading underscore fails its own prefix check)
filter_bogus = REPO_ROOT / "output" / "output_filters" / "_csv_all_variables.txt"
filter_good = REPO_ROOT / "output" / "output_filters" / "csv_all_variables.txt"
if filter_bogus.exists() and not filter_good.exists():
    filter_bogus.rename(filter_good)

from RUFAS.output_manager import LogVerbosity
from RUFAS.task_manager import TaskManager

print("=== MSF Expert System — Prototype 1 (DELAYED) ===")
print("Question: What if I wait 3 days before applying?")
print("  Field:     10 ha (US-shim FIPS 55025)")
print("  Manure:    30 t/ha dairy slurry, broadcast surface, applied day 205")
print("  Rain:      Day 203 (BEFORE application — no manure to run off)")
print("  Window:    2013-07-21 -> 2013-08-25 (35 days, using 2013 weather)")
print()

task_manager = TaskManager()
task_manager.start(
    metadata_path=Path("prototype_msf/prototype_root_delayed.json"),
    verbosity=LogVerbosity.WARNINGS,
    exclude_info_maps=True,
    output_directory=Path("prototype_msf/output_delayed"),
    logs_directory=Path("prototype_msf/output_delayed/logs"),
    clear_output_directory=True,
    produce_graphics=False,
    suppress_log_files=False,
    metadata_depth_limit=None,
)

print()
print("=== Run complete ===")
