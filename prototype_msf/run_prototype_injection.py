"""
MSF Expert System — Prototype 1, injection variant
Same 35-day window and application day as run 1 (broadcast). Only difference:
manure injected 30 mm into soil, only 20% left on surface.
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)

filter_bogus = REPO_ROOT / "output" / "output_filters" / "_csv_all_variables.txt"
filter_good = REPO_ROOT / "output" / "output_filters" / "csv_all_variables.txt"
if filter_bogus.exists() and not filter_good.exists():
    filter_bogus.rename(filter_good)

from RUFAS.output_manager import LogVerbosity
from RUFAS.task_manager import TaskManager

print("=== MSF Expert System — Prototype 1 (INJECTION) ===")
print("Question: If I inject the manure instead of broadcasting, how much less runoff?")
print("  Field:     10 ha (US-shim FIPS 55025)")
print("  Manure:    30 t/ha dairy slurry, INJECTED 30 mm, 20% surface remainder")
print("  Applied:   Day 202 (same day as run 1)")
print("  Window:    2013-07-21 -> 2013-08-25 (35 days, using 2013 weather)")
print()

task_manager = TaskManager()
task_manager.start(
    metadata_path=Path("prototype_msf/prototype_root_injection.json"),
    verbosity=LogVerbosity.WARNINGS,
    exclude_info_maps=True,
    output_directory=Path("prototype_msf/output_injection"),
    logs_directory=Path("prototype_msf/output_injection/logs"),
    clear_output_directory=True,
    produce_graphics=False,
    suppress_log_files=False,
    metadata_depth_limit=None,
)

print()
print("=== Run complete ===")
