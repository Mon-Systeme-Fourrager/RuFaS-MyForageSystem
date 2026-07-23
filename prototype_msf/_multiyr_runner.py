"""
Shared runner for multi-year sweep. Called by run_multiyr_sweep.py via subprocess
with year and day as CLI args. One file instead of 30.
"""

import os
import sys
from pathlib import Path

if len(sys.argv) != 3:
    print("Usage: _multiyr_runner.py <year> <day>", file=sys.stderr)
    sys.exit(2)

year = int(sys.argv[1])
day = int(sys.argv[2])

REPO_ROOT = Path(__file__).parent.parent
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
    metadata_path=Path(f"prototype_msf/sweep_config/multiyr/root_year{year}_day{day}.json"),
    verbosity=LogVerbosity.WARNINGS,
    exclude_info_maps=True,
    output_directory=Path(f"prototype_msf/sweep_output/multiyr/y{year}_d{day}"),
    logs_directory=Path(f"prototype_msf/sweep_output/multiyr/y{year}_d{day}/logs"),
    clear_output_directory=True,
    produce_graphics=False,
    suppress_log_files=False,
    metadata_depth_limit=None,
)
