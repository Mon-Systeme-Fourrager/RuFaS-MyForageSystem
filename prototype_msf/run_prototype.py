"""
MSF Expert System — Prototype 1
Question: If I apply dairy slurry today, how much N will be available in 30 days?

Simulation window: 2013:202 -> 2013:237 (July 21 -> Aug 25, using 2013 weather as
a proxy for "today" — Open-Meteo -> RUFAS Python-side bridge is a follow-up).
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)  # RUFAS resolves catalog paths relative to CWD

from RUFAS.output_manager import LogVerbosity
from RUFAS.task_manager import TaskManager

print("=== MSF Expert System — Prototype 1 ===")
print("Question: If I apply dairy slurry today, how much N will be available in 30 days?")
print("  Field:     10 ha (US-shim FIPS 55025 — Quebec analogue TBD)")
print("  Manure:    30 t/ha dairy slurry, broadcast surface")
print("  N applied: 780 kg total = 78 kg N/ha (RT-06: 2.6 kg N/t x 30 t/ha)")
print("  Window:    2013-07-21 -> 2013-08-25 (35 days, using 2013 weather)")
print()

task_manager = TaskManager()
task_manager.start(
    metadata_path=Path("prototype_msf/prototype_root.json"),
    verbosity=LogVerbosity.WARNINGS,
    exclude_info_maps=True,
    output_directory=Path("prototype_msf/output"),
    logs_directory=Path("prototype_msf/output/logs"),
    clear_output_directory=True,
    produce_graphics=False,
    suppress_log_files=False,
    metadata_depth_limit=None,
)

print()
print("=== Run complete ===")
print("Look in prototype_msf/output/ for:")
print("  - Soil layer CSVs (available_nitrogen per layer per day)")
print("  - Field-level summary CSV (nitrogen_uptake, nitrate_content)")
print("  - Manure application log (verify the day-202 event fired)")
