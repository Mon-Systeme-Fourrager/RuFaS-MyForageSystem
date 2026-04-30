# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is RuFaS

RuFaS (Ruminant Farm Systems) is an open-source whole-farm modeling environment that simulates dairy farm production and environmental impact. This fork (`RuFaS-MyForageSystem`) is maintained on the `dev-msf` branch and serves as a dependency for downstream projects (`rufas_api`, `ration-simulator`). The `dev-msf` branch must never be deleted.

## Commands

**Install dependencies:**
```bash
pip install .
```

**Run all tests:**
```bash
pytest
```

**Run a single test file:**
```bash
pytest tests/path/to/test_file.py
```

**Run tests with coverage:**
```bash
coverage run --rcfile=.github/.coveragerc
coverage report --rcfile=.github/.coveragerc
```

**Lint (Flake8):**
```bash
flake8 .
```

**Format (Black):**
```bash
black <file_or_directory>
```

**Type-check (Mypy):**
```bash
python -m mypy .
```

**Lint + type-check only changed files vs a base branch:**
```bash
./check_changes.sh [BASEBRANCH]   # defaults to dev
```

**Run the simulation:**
```bash
python main.py -p input/task_manager_metadata.json
```

Key CLI flags for `main.py`: `-v` (verbosity: errors/warnings/logs/credits/none), `-g` (no graphics), `-o` (output dir), `-l` (logs dir), `-c` (clear output dir first), `-s` (suppress log files).

## Code Style

- **Black**: line length 120, target Python 3.12.
- **Flake8**: max line length 120, max complexity 10, ignores E203 and W503.
- **Mypy**: strict mode. New code must not increase the mypy error count compared to `dev`.
- All PRs must update `changelog.md` or the CI will block the merge.
- Protected example input files under `input/` must not be modified without maintainer approval (CI enforces this).

## Architecture

### Entry Point & Orchestration

`main.py` → `TaskManager` (`RUFAS/task_manager.py`) → `SimulationEngine` (`RUFAS/simulation_engine.py`)

- **TaskManager** reads a metadata JSON (default `input/task_manager_metadata.json`) that specifies the `TaskType` (single run, multi-run, sensitivity analysis, end-to-end testing, herd initialization, etc.) and dispatches accordingly.
- **SimulationEngine** owns the main simulation loop. Each day it drives: `Weather` → `HerdManager` → `FeedManager` → `ManureManager` → `FieldManager`. Annual routines run once per simulated year.
- **InputManager** and **OutputManager** are singletons used across the entire codebase for reading JSON/CSV inputs and logging/writing outputs respectively.

### Module Layout (`RUFAS/`)

```
RUFAS/
├── simulation_engine.py   # daily/annual simulation loop
├── task_manager.py        # task dispatch, multi-run, sensitivity analysis
├── input_manager.py       # singleton; loads/validates JSON+CSV input data
├── output_manager.py      # singleton; logging pools, CSV/JSON output, graphs
├── rufas_time.py          # simulation calendar abstraction
├── weather.py             # weather data access
├── units.py               # unit system (metric/imperial) selection
├── general_constants.py   # physical conversion constants
├── data_structures/       # cross-module data transfer objects (connections between modules)
├── biophysical/           # self-contained biophysical component classes
│   ├── animal/            # HerdManager, Animal life-cycle, nutrition, reproduction, genetics, bedding
│   ├── feed_storage/      # FeedManager, hay/silage/baleage/grain/purchased storage
│   └── manure/            # ManureManager, handlers, separators, digesters, storage types
└── routines/              # stateless calculation routines called by biophysical managers
    ├── animal/            # life-cycle, ration, manure excretion, health, genetics
    ├── feed/              # feed quality dynamics (carbon/nitrogen loss, protein degradation)
    ├── feed_storage/      # storage-specific routines
    ├── field/             # FieldManager, crop growth, soil N/P/C cycling, water dynamics
    ├── manure/            # manure treatment calculations, gas emissions, nutrient tracking
    └── EEE/              # Economic and Environmental Evaluation module
```

### Key Design Patterns

- **Singleton managers**: `InputManager` and `OutputManager` use `__new__`-based singletons; instantiate with `InputManager()` / `OutputManager()` anywhere to get the shared instance.
- **Data structures as connections**: Files in `RUFAS/data_structures/` define typed dataclasses/TypedDicts that cross module boundaries (e.g., `FeedStorageToAnimalConnection`, `ManureToCropSoilConnection`). These are the contracts between the animal, manure, feed, and field modules.
- **biophysical vs routines**: `biophysical/` holds stateful manager classes; `routines/` holds pure calculation functions/classes. Managers call into routines.
- **Input data**: all simulation inputs are JSON files under `input/data/` (animal, crop, field, manure, feed, soil, weather, etc.) assembled by a metadata JSON that `InputManager` resolves. The `DataCollectionApp` (HTML + JSON schema) can generate these input files.

### Testing

Tests mirror the source structure under `tests/`. Files prefixed with `_test_` (older convention) and `test_` (newer) are both collected by pytest. Coverage target is ~96%.

## Slash Commands & Development Workflow

### Plan-based development workflow

Use these four commands in sequence for any non-trivial change:

```
/diagnose          → analyse, questions interactives → PLAN_<slug>.md
/challenge-plan    → sous-agent critique le plan (auto-cycle jusqu'à ✅)
/refine-plan       → corrections manuelles si cycle interrompu
/apply-plan        → exécution TDD + double review + PR
```

- Plans are stored as `PLAN_<slug>.md` at the repo root (work artifact, never committed to the PR).
- `/apply-plan` runs per-task: `pytest` + `flake8` + `mypy` must all pass before moving to the next task.
- All PRs go through GitHub MCP tools (`mcp__github__*`). Never push directly to `main`.

### OpenSpec workflow (spec-driven)

```
/opsx:propose      → proposal + design + tasks artifacts
/challenge-plan openspec:<name>
/apply-plan openspec:<name>
/opsx:archive      → archive after PR merged
```

### Utility commands

- `/sync-claude-md` — audits the codebase and proposes an updated CLAUDE.md.

### Hooks

- `.claude/hooks/session-start.sh` — installs `@fission-ai/openspec` automatically in remote sessions (Claude Code Web). Injects Graphify dependency report when available.
