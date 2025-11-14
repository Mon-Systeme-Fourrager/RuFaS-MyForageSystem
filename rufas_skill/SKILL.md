# RuFaS: Ruminant Farm Systems - Claude AI Skill

## Overview

**RuFaS (Ruminant Farm Systems)** is an open-source, next-generation whole-farm modeling environment that simulates dairy farm production and environmental impact. This skill provides comprehensive knowledge about the RuFaS codebase, architecture, APIs, and development practices.

### Version Information
- **Current Version**: 0.9.2
- **License**: GPLv3
- **Python Requirements**: 3.12 - 3.13
- **Repository**: https://github.com/RuminantFarmSystems/RuFaS
- **Documentation**: https://ruminantfarmsystems.github.io/RuFaS/
- **Website**: https://rufas.org

---

## Vision & Mission

### Vision
To support research and sustainable decision-making in ruminant animal production through a state-of-the-art, open-source modeling environment that evolves with scientific and technological advances.

### Mission
Build an integrated, whole-farm modeling platform simulating:
- Milk, meat, and crop production
- Greenhouse gas emissions
- Water quality impacts
- Soil health
- Other sustainability outcomes

---

## Core Technologies

### Backend Stack
- **Python 3.12+** - Primary language with strict type checking
- **NumPy 2.2.0** - Numerical computations
- **SciPy 1.15.1** - Scientific algorithms
- **Pandas 2.2.3** - Data processing and analysis
- **SALib 1.5.1** - Sensitivity analysis (Sobol, Morris, Fractional Factorial)
- **Matplotlib 3.10.0** - Visualization and graph generation
- **Numba 0.61.0** - JIT compilation for performance

### Frontend Stack (Data Collection App)
- **HTML5 & JavaScript** - User interface
- **JSON Editor** - Interactive form-based input
- **ACE Editor** - Advanced JSON editing
- **LZ-String** - Data compression

### Development Tools
- **Pytest 7.4.4** - Testing framework (95% coverage)
- **Black 25.1.0** - Code formatting (120 char line length)
- **Flake8 7.1.1** - Linting
- **Mypy 1.15.0** - Static type checking (strict mode)
- **Sphinx 8.1.3** - Documentation generation
- **DeepDiff 8.2.0** - Data comparison for testing
- **Freezegun 1.5.1** - Time manipulation for testing

---

## Project Architecture

### High-Level Structure

```
RuFaS-MyForageSystem/
├── RUFAS/                      # Core backend (12,272+ lines)
│   ├── task_manager.py         # Task orchestration (967 lines)
│   ├── simulation_engine.py    # Main simulation loop (286 lines)
│   ├── input_manager.py        # Input validation (1,413 lines)
│   ├── output_manager.py       # Results & logging (2,883 lines)
│   ├── data_validator.py       # Data validation (1,886 lines)
│   ├── report_generator.py     # Report generation (989 lines)
│   ├── graph_generator.py      # Visualization (691 lines)
│   ├── biophysical/            # Scientific models (106+ files)
│   └── routines/               # Simulation routines (164+ files)
├── DataCollectionApp/          # HTML/JS frontend
├── rufas_api/                  # API entry point
├── tests/                      # 243+ test files (95% coverage)
├── docs/                       # Sphinx documentation
├── input/                      # Input data & schemas
├── output/                     # Simulation results
├── main.py                     # CLI entry point
└── pyproject.toml              # Project metadata
```

### Core Components

#### 1. Task Manager (`task_manager.py`)
**Purpose**: Orchestrates different types of simulation tasks and manages lifecycle.

**Task Types**:
```python
class TaskType(Enum):
    HERD_INITIALIZATION           # Initialize animal herds
    SIMULATION_SINGLE_RUN         # Single simulation run
    SIMULATION_MULTI_RUN          # Multiple runs with different seeds
    SENSITIVITY_ANALYSIS          # Sobol/Morris/Fractional Factorial
    INPUT_DATA_AUDIT              # Validate and export metadata
    END_TO_END_TESTING            # E2E test execution
    POST_PROCESSING               # Direct output processing
    COMPARE_METADATA_PROPERTIES   # Metadata comparison
    DATA_COLLECTION_APP_UPDATE    # Update DCA schemas
    UPDATE_E2E_TEST_RESULTS       # Update E2E expected results
```

**Key Methods**:
- `start()` - Initialize and execute tasks
- `_run_simulation()` - Execute single simulation
- `_run_sensitivity_analysis()` - Run SA with SALib
- `_validate_dependencies()` - Check Python/package versions

#### 2. Simulation Engine (`simulation_engine.py`)
**Purpose**: Main simulation loop executing daily and annual routines.

**Workflow**:
1. Initialize farm components (animals, fields, manure systems)
2. Execute daily routines for each simulated day
3. Process annual events (calving, harvests, etc.)
4. Collect results and update state
5. Generate outputs and reports

#### 3. Input Manager (`input_manager.py`)
**Purpose**: Load, validate, and manage input data (JSON/CSV).

**Capabilities**:
- JSON schema validation
- CSV data loading
- Metadata depth limiting
- Data type checking
- Error reporting with line numbers
- Singleton pattern for global access

#### 4. Output Manager (`output_manager.py`)
**Purpose**: Centralized logging, results collection, and file I/O.

**Features**:
- Multi-level logging (errors, warnings, logs, credits)
- Data pooling for efficient memory usage
- Report generation (HTML, CSV)
- Graph generation (PNG)
- Info maps for debugging
- Log verbosity control

#### 5. Data Validator (`data_validator.py`)
**Purpose**: Comprehensive input validation with detailed error messages.

**Validation Types**:
- Type checking (int, float, string, bool, lists, dicts)
- Range validation (min/max values)
- Required field checking
- Cross-field dependencies
- Unit consistency
- Date/time validation

---

## Biophysical Module Architecture

### Animal Module (~60 files)

**Core Components**:
- `herd_manager.py` - Population management
- `animal.py` / `pen.py` - Individual/group representations
- **Genetics** (`animal_genetics/`) - Trait modeling
- **Health** (`animal_health/`) - Disease tracking
- **Nutrition** (`nutrients/`) - NASEM/NRC requirements
- **Growth** (`growth/`) - Body weight development
- **Reproduction** (`reproduction/`) - Breeding, lactation
- **Milk Production** (`milk/`) - Lactation curves
- **Digestive System** (`digestive_system/`) - Enteric methane
- **Ration Management** (`ration/`) - Feed optimization
- **Bedding** (`bedding/`) - Bedding materials

**Key Equations**:
- NASEM (National Academies of Sciences, Engineering, and Medicine) nutrient requirements
- NRC (National Research Council) feed formulation
- Enteric methane emission models
- Lactation curve modeling (Wood's equation)

### Manure Module (~50 files)

**Pathway Types**:
- **Storage Systems**:
  - Open lot storage
  - Slurry tanks
  - Bedded pack
  - Anaerobic lagoons
  - Composting
- **Treatment**: Digestion, separation, daily spread
- **Collection**: Parlor cleaning, scraping systems

**Environmental Tracking**:
- Nutrient flow (N, P, C)
- Gas emissions (CH4, N2O, NH3)
- Odor generation
- Pathogen reduction

### Field/Crop Module

**Capabilities**:
- Crop growth simulation
- Soil health tracking
- Nutrient cycling (N, P, C, K)
- Field management operations
- Harvest scheduling
- Tillage and planting

**Soil Processes**:
- Carbon sequestration
- Nitrogen mineralization
- Phosphorus dynamics
- Water infiltration
- Erosion modeling

### Feed Storage Module

**Storage Types**:
- Silage (fermentation modeling)
- Hay (dry matter loss)
- Grain (spoilage tracking)

**Degradation Models**:
- Aerobic spoilage
- Anaerobic fermentation
- Temperature effects
- Moisture content impact
- Nutrient loss quantification

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────┐
│         User Input (DataCollectionApp or JSON)      │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│  InputManager (Validation & Loading)                │
│  - JSON schema validation                           │
│  - Type checking                                    │
│  - Range validation                                 │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│  TaskManager (Task Selection)                       │
│  - Single/Multi-run                                 │
│  - Sensitivity Analysis                             │
│  - E2E Testing                                      │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│  SimulationEngine (Main Loop)                       │
│  - Initialize components                            │
│  - Daily routine execution                          │
│  - Annual event processing                          │
└─────────────────────┬───────────────────────────────┘
                      ▼
        ┌─────────────┴─────────────┐
        ▼                           ▼
┌───────────────┐           ┌───────────────┐
│ Animal        │           │ Field/Crop    │
│ Routines      │           │ Routines      │
└───────┬───────┘           └───────┬───────┘
        │                           │
        ▼                           ▼
┌───────────────┐           ┌───────────────┐
│ Manure        │           │ Feed Storage  │
│ Routines      │           │ Routines      │
└───────┬───────┘           └───────┬───────┘
        │                           │
        └─────────────┬─────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│  OutputManager (Collection & Reporting)             │
│  - Data pooling                                     │
│  - Log aggregation                                  │
│  - Error tracking                                   │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│  Report/Graph Generation                            │
│  - HTML reports                                     │
│  - CSV exports                                      │
│  - PNG graphs                                       │
└─────────────────────────────────────────────────────┘
```

---

## CLI Usage

### Basic Command
```bash
python main.py -p input/task_manager_metadata.json
```

### Command-Line Arguments

| Flag | Long Form | Description | Default |
|------|-----------|-------------|---------|
| `-p` | `--path-to-metadata` | Path to task manager metadata | `input/task_manager_metadata.json` |
| `-o` | `--output-dir` | Output directory | `output/` |
| `-l` | `--logs-dir` | Logs directory | `output/logs` |
| `-v` | `--verbose` | Log verbosity level | `credits` |
| `-g` | `--no-graphics` | Disable graph generation | `False` |
| `-c` | `--clear-output` | Clear output directory before run | `False` |
| `-i` | `--exclude_info_maps` | Exclude info maps from output | `False` |
| `-s` | `--suppress-log-files` | Prevent log file writing | `False` |
| `-m` | `--metadata-depth-limit` | Override metadata depth limit | None |

### Verbosity Levels
- `errors` - Show only errors
- `warnings` - Show errors and warnings
- `logs` - Show all logs
- `credits` - Show all logs + attribution
- `none` - Suppress all terminal output

### Example Commands

**Run single simulation with verbose logging**:
```bash
python main.py -p input/my_farm.json -v logs
```

**Run sensitivity analysis without graphics**:
```bash
python main.py -p input/sensitivity_config.json -g
```

**Clear output and run with custom output directory**:
```bash
python main.py -p input/config.json -c -o output/run_2024
```

**Run E2E testing with suppressed logs**:
```bash
python main.py -p input/e2e_test.json -s -v none
```

---

## Key Design Patterns

### 1. Singleton Pattern
**Used in**: `InputManager`, `OutputManager`

**Rationale**: Ensures single source of truth for input data and centralized logging across entire simulation.

### 2. Factory Pattern
**Used in**: `HerdFactory`, component initialization

**Rationale**: Flexible creation of complex objects (animals, pens) with varying configurations.

### 3. Strategy Pattern
**Used in**: Manure pathway selection, ration optimization

**Rationale**: Runtime selection of algorithms based on farm configuration.

### 4. Observer Pattern
**Used in**: Event tracking, state changes

**Rationale**: Decouple event generation from event handling for flexibility.

### 5. Template Method Pattern
**Used in**: Daily/annual routines

**Rationale**: Define simulation skeleton with customizable steps per domain.

---

## Testing Strategy

### Test Coverage: 95%

### Test Categories

1. **Unit Tests** (`tests/test_*.py`)
   - Individual function testing
   - Edge case validation
   - Type checking verification

2. **Integration Tests**
   - Module interaction testing
   - Data flow validation
   - Cross-module dependencies

3. **End-to-End Tests** (`tests/e2e/`)
   - Full simulation runs
   - Result comparison against expected values
   - Regression prevention

4. **Domain-Specific Tests**
   - `animal_module_tests/` - Animal model validation
   - `_test_manure_module/` - Manure pathway verification
   - `soil_crop_tests/` - Crop/soil model testing
   - `test_feed_storage_module/` - Feed storage accuracy

### Testing Tools
- **Pytest** - Test runner and fixtures
- **pytest-mock** - Mocking framework
- **DeepDiff** - Result comparison
- **Freezegun** - Time manipulation
- **Coverage** - Code coverage analysis

### Quality Gates (GitHub Actions)
- ✅ Flake8 linting (95%+ compliance)
- ✅ Pytest all tests passing
- ✅ 95%+ code coverage
- ⚠️ Mypy type checking (3,275 errors - work in progress)
- ✅ Black formatting

---

## Sensitivity Analysis

### Supported Methods (via SALib)

1. **Sobol Analysis**
   - Global sensitivity indices
   - First-order and total-order effects
   - Interaction identification

2. **Morris Method**
   - Elementary effects
   - Screening influential parameters
   - Computational efficiency

3. **Fractional Factorial**
   - Main effects estimation
   - Two-way interactions
   - Efficient parameter exploration

### Configuration Example
```json
{
  "task_type": "Sensitivity Analysis",
  "sa_method": "sobol",
  "num_samples": 1024,
  "parameters": [
    {"name": "feed_protein", "bounds": [0.12, 0.20]},
    {"name": "milk_price", "bounds": [0.30, 0.50]}
  ]
}
```

---

## Performance Optimization

### Strategies
1. **Numba JIT Compilation** - Accelerate numerical loops
2. **Data Pooling** - Efficient memory management
3. **Lazy Evaluation** - Defer computations when possible
4. **Multiprocessing** - Parallel sensitivity analysis runs
5. **Chunked I/O** - Large dataset handling

### Memory Management
- Pool-based data collection minimizes allocation overhead
- Lazy loading of large datasets
- Periodic garbage collection in long simulations

---

## Development Standards

### Code Style
- **Black formatting** (120 char lines)
- **Type hints required** (Mypy strict mode)
- **Docstrings** (Google style)
- **Flake8 compliance** (95%+)

### Branching Strategy
- `main` - Stable releases
- `dev` - Development branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Critical fixes

### Commit Messages
Follow conventional commits:
```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Pull Request Process
1. Fork repository
2. Create feature branch
3. Implement with tests
4. Ensure CI passes (Flake8, Pytest, Coverage)
5. Submit PR with clear description
6. Tag relevant maintainers
7. Address review comments

---

## Scientific Foundation

### Peer-Reviewed Models
- NASEM (2021) nutrient requirements
- NRC feed formulation standards
- IPCC emission factors
- USDA soil models
- University-validated lactation curves

### Research Collaboration
- Active partnerships with universities
- Industry stakeholder input
- Continuous model validation
- Transparent methodology

---

## Environmental Impact Modeling

### Greenhouse Gas Emissions
- **Enteric methane** - Rumen fermentation
- **Manure methane** - Anaerobic decomposition
- **Nitrous oxide** - Soil/manure N cycling
- **Carbon dioxide** - Respiration, fuel use

### Water Quality
- Nitrogen runoff
- Phosphorus leaching
- Sediment transport
- Pathogen loading

### Soil Health
- Carbon sequestration
- Organic matter accumulation
- Nutrient balance
- Soil structure

---

## Contact & Support

- **Email**: contact@rufas.org
- **Documentation**: https://ruminantfarmsystems.github.io/RuFaS/
- **Issues**: https://github.com/RuminantFarmSystems/RuFaS/issues
- **Discussions**: GitHub Discussions

---

## License

RuFaS is licensed under **GPLv3** (GNU General Public License v3.0).

### Key Points
- ✅ Open source and free to use
- ✅ Modifications must be shared under GPLv3
- ✅ Commercial use allowed
- ✅ Patent protection
- ❌ Warranty disclaimer
- ❌ Liability disclaimer

See `COPYING.txt` and `COPYING.LESSER.txt` for full details.

---

## Contribution Levels

RuFaS uses a 5-level contributor system:

1. **Level 1** - First contribution merged
2. **Level 2** - 3+ meaningful contributions
3. **Level 3** - Significant feature implementation
4. **Level 4** - Major subsystem ownership
5. **Level 5** - Core maintainer status

See `CONTRIBUTING.md` for detailed progression criteria.

---

## Future Roadmap

### Short-Term (2025)
- Complete Mypy type checking (eliminate 3,275 errors)
- Expand test coverage to 98%+
- Add more crop types
- Improve UI/UX of Data Collection App

### Medium-Term (2026)
- Web-based simulation dashboard
- Real-time farm data integration
- Machine learning for optimization
- Multi-farm comparison tools

### Long-Term (2027+)
- Global farm network integration
- Climate scenario modeling
- Economic optimization engine
- Mobile app for field data collection

---

## References & Resources

### Official Documentation
- [GitHub Pages](https://ruminantfarmsystems.github.io/RuFaS/)
- [Wiki Articles](https://ruminantfarmsystems.github.io/RuFaS/_wiki/)
- [API Documentation](https://ruminantfarmsystems.github.io/RuFaS/api/)

### Key Wiki Articles
- Best Practices
- Unit Testing & TDD
- Type Checking with Mypy
- Flake8 Linting Guide
- GitHub Actions CI/CD
- Input Manager Guide
- Data Collection App
- End-to-End Testing
- Report Generator
- Code Review Process

### Scientific Documentation
- Research papers in `scientific_documentation/`
- Model validation studies
- Peer review reports

---

*This skill was generated to provide comprehensive Claude AI assistance for RuFaS development, usage, and contribution.*
