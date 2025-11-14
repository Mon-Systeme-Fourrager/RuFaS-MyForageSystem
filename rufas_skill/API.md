# RuFaS API Reference

This document provides detailed API documentation for RuFaS core modules, classes, and functions.

---

## Table of Contents

1. [TaskManager](#taskmanager)
2. [SimulationEngine](#simulationengine)
3. [InputManager](#inputmanager)
4. [OutputManager](#outputmanager)
5. [DataValidator](#datavalidator)
6. [HerdManager](#herdmanager)
7. [ManureManager](#manuremanager)
8. [FeedManager](#feedmanager)
9. [FieldManager](#fieldmanager)
10. [Utility Functions](#utility-functions)

---

## TaskManager

**Location**: `RUFAS/task_manager.py`

### Overview
Orchestrates different task types for RuFaS simulations including single runs, multi-runs, sensitivity analysis, E2E testing, and data validation.

### Class Definition

```python
class TaskManager:
    """Manager class for handling tasks related to simulations and analyses."""
```

### Constructor

```python
def __init__(self) -> None:
    """Initializes TaskManager with OutputManager instance."""
```

### Main Methods

#### `start()`

```python
def start(
    self,
    metadata_path: Path,
    verbosity: LogVerbosity,
    exclude_info_maps: bool,
    output_directory: Path,
    logs_directory: Path,
    clear_output_directory: bool,
    produce_graphics: bool,
    suppress_log_files: bool,
    metadata_depth_limit: int,
) -> None:
    """
    Initializes and starts the task management process.

    Parameters
    ----------
    metadata_path : Path
        Path to the metadata file that contains task management inputs.
    verbosity : LogVerbosity
        Level of verbosity for logging (NONE, CREDITS, ERRORS, WARNINGS, LOGS).
    exclude_info_maps : bool
        Flag to exclude information maps from output.
    output_directory : Path
        Path to the directory where outputs will be saved.
    logs_directory : Path
        Path to the directory where logs from the Task Manager will be saved.
    clear_output_directory : bool
        Whether to clear the output directory before starting.
    produce_graphics : bool
        Whether to generate graphs/visualizations.
    suppress_log_files : bool
        Prevent log file writing to disk.
    metadata_depth_limit : int
        Maximum depth for metadata validation (default: 7).

    Raises
    ------
    ValueError
        If task type is invalid or dependencies are not met.
    RuntimeError
        If simulation encounters fatal errors.
    """
```

**Example Usage**:
```python
from RUFAS.task_manager import TaskManager
from RUFAS.output_manager import LogVerbosity
from pathlib import Path

task_manager = TaskManager()
task_manager.start(
    metadata_path=Path("input/task_manager_metadata.json"),
    verbosity=LogVerbosity.LOGS,
    exclude_info_maps=False,
    output_directory=Path("output/"),
    logs_directory=Path("output/logs"),
    clear_output_directory=True,
    produce_graphics=True,
    suppress_log_files=False,
    metadata_depth_limit=7
)
```

### TaskType Enum

```python
class TaskType(Enum):
    """Enum for different task types handled by TaskManager."""

    HERD_INITIALIZATION = "Herd Initialization"
    SIMULATION_SINGLE_RUN = "A single simulation run"
    SIMULATION_MULTI_RUN = "Multiple simulation with different random seeds"
    SENSITIVITY_ANALYSIS = "Run sensitivity analysis"
    INPUT_DATA_AUDIT = "Validates input data and saves metadata properties as CSV"
    END_TO_END_TESTING = "Run e2e testing"
    POST_PROCESSING = "Bypass simulation engine and directly run Output Manager"
    COMPARE_METADATA_PROPERTIES = "Compares 2 metadata properties files"
    DATA_COLLECTION_APP_UPDATE = "Updates the schema and interface of the Data Collection App"
    UPDATE_E2E_TEST_RESULTS = "Updates end-to-end expected test results"
```

**Methods**:
- `from_string(input_str: str) -> TaskType` - Convert string to TaskType
- `is_multi_run() -> bool` - Check if task involves multiple runs

**Example**:
```python
task_type = TaskType.from_string("Sensitivity Analysis")
if task_type.is_multi_run():
    print("This is a multi-run task")
```

### Private Methods

#### `_run_simulation()`
```python
def _run_simulation(self, random_seed: int | None = None) -> None:
    """
    Executes a single simulation run.

    Parameters
    ----------
    random_seed : int | None
        Random seed for NumPy (0 to 2^32-1). If None, uses default.
    """
```

#### `_run_sensitivity_analysis()`
```python
def _run_sensitivity_analysis(self) -> None:
    """
    Runs sensitivity analysis using SALib samplers (Sobol, Morris, or Fractional Factorial).

    Generates parameter samples, runs parallel simulations, and collects results.
    """
```

---

## SimulationEngine

**Location**: `RUFAS/simulation_engine.py`

### Overview
The core simulation loop that advances time, executes daily/annual routines, and coordinates all farm subsystems.

### Class Definition

```python
class SimulationEngine:
    """
    The SimulationEngine class is responsible for orchestrating the entire simulation
    process for RuFaS. It manages the simulation's lifecycle, advancing time, executing
    daily and annual routines, and logging simulation progress.
    """
```

### Attributes

```python
weather : Weather
    The weather object containing weather data.
time : RufasTime
    Time management object for accessing/manipulating simulation time.
feed_manager : FeedManager
    Manages feed inventory and storage.
herd_manager : HerdManager
    Manages all animals in the herd.
manure_manager : ManureManager
    Manages manure pathways and treatments.
field_manager : FieldManager
    Manages all crop fields in the simulation.
```

### Constructor

```python
def __init__(self) -> None:
    """
    Initializes the simulation engine.

    Sets up:
    - OutputManager instance
    - InputManager instance
    - RufasTime instance
    - Calls _initialize_simulation()
    """
```

### Main Methods

#### `simulate()`

```python
def simulate(self) -> None:
    """
    Executes the simulation.

    Process:
    1. Run main simulation loop (daily/annual routines)
    2. Generate end-of-simulation reports (animal statistics, feed inventory)
    3. Calculate and log total simulation time
    4. Mark simulation as complete

    Side Effects
    ------------
    - Modifies all farm component states
    - Writes results to OutputManager pools
    - Generates logs and timing information
    """
```

**Example Usage**:
```python
from RUFAS.simulation_engine import SimulationEngine

# After InputManager has loaded data
engine = SimulationEngine()
engine.simulate()  # Run full simulation
```

#### `_daily_simulation()`

```python
def _daily_simulation(self) -> None:
    """
    Executes the daily simulation routines.

    Daily Workflow:
    1. Generate manure applications for fields
    2. Update field/crop status (growth, harvests)
    3. Receive harvested crops into feed storage
    4. Recalculate max daily feeds (periodic)
    5. Reformulate rations (periodic)
    6. Process animal feed requests
    7. Execute animal daily routines (intake, milk, growth, reproduction)
    8. Process manure production and management
    9. Advance simulation day

    Side Effects
    ------------
    - Updates all subsystem states
    - Writes daily variables to OutputManager
    - May trigger warnings/errors for feed shortages
    """
```

#### `_annual_simulation()`

```python
def _annual_simulation(self) -> None:
    """
    Executes annual routines for one simulation year (365 days).

    Process:
    1. Loop through 365 days
    2. Execute _daily_simulation() for each day
    3. Process annual events (year-end summaries, herd culling, etc.)
    """
```

### Private Helper Methods

#### `_initialize_simulation()`
```python
def _initialize_simulation(self) -> None:
    """
    Initializes all farm components from InputManager data.

    Initializes:
    - Weather data
    - Feed storage and inventory
    - Animal herds (cows, heifers, calves)
    - Manure management systems
    - Crop fields
    - Ration formulation schedule
    """
```

#### `_formulate_ration()`
```python
def _formulate_ration(self) -> None:
    """
    Formulates optimal rations for all animal groups.

    Uses:
    - Available feed inventory
    - Nutrient requirements (NASEM/NRC)
    - Feed costs
    - Nutritional constraints

    Updates:
    - Animal group rations
    - Next ration reformulation date
    """
```

#### `generate_daily_manure_applications()`
```python
def generate_daily_manure_applications(self) -> ManureEventNutrientRequestResults:
    """
    Generates manure applications for fields based on scheduled events.

    Returns
    -------
    ManureEventNutrientRequestResults
        Nutrient amounts (N, P, C) applied to each field from manure.
    """
```

---

## InputManager

**Location**: `RUFAS/input_manager.py`

### Overview
Singleton class for loading, validating, and providing access to input data (JSON/CSV). Ensures data integrity before simulation.

### Class Definition

```python
class InputManager:
    """
    Input Manager class responsible for loading, validating, and providing
    access to input data.
    """
```

### Singleton Pattern

```python
def __new__(cls, metadata_depth_limit: int | None = None) -> "InputManager":
    """
    Ensures only one InputManager instance exists.

    Parameters
    ----------
    metadata_depth_limit : int | None
        Maximum depth for metadata validation (default: 7).

    Returns
    -------
    InputManager
        The singleton InputManager instance.
    """
```

### Properties

#### `meta_data`
```python
@property
def meta_data(self) -> Dict[str, Any]:
    """
    Getter for metadata dictionary.

    Returns
    -------
    Dict[str, Any]
        The loaded and validated metadata.
    """

@meta_data.setter
def meta_data(self, incoming_metadata: Dict[str, Any]) -> None:
    """Setter for metadata dictionary."""
```

#### `pool`
```python
@property
def pool(self) -> Dict[str, Any]:
    """
    Getter for data pool (all loaded input data).

    Returns
    -------
    Dict[str, Any]
        Dictionary containing all validated input data accessible by key.
    """

@pool.setter
def pool(self, incoming_pool: Dict[str, Any]) -> None:
    """Setter for data pool."""
```

### Main Methods

#### `start_data_processing()`

```python
def start_data_processing(
    self,
    metadata_path: Path,
    eager_termination: bool = True
) -> bool:
    """
    Starts the pipeline for organizing metadata and input data processing.

    Parameters
    ----------
    metadata_path : Path
        File path to the metadata JSON file.
    eager_termination : bool, default=True
        If True, terminate as soon as invalid data is found.
        If False, validate entire dataset before terminating.

    Returns
    -------
    bool
        True if all data is valid, False otherwise.

    Raises
    ------
    ValueError
        If metadata or data validation fails.
    FileNotFoundError
        If metadata file doesn't exist.

    Process
    -------
    1. Load metadata from JSON
    2. Validate metadata structure
    3. Load properties (data schemas)
    4. Validate properties against schemas
    5. Populate data pool from files
    6. Validate all input data
    7. Route validation logs to OutputManager
    """
```

**Example Usage**:
```python
from RUFAS.input_manager import InputManager
from pathlib import Path

im = InputManager(metadata_depth_limit=7)
is_valid = im.start_data_processing(
    metadata_path=Path("input/task_manager_metadata.json"),
    eager_termination=True
)

if is_valid:
    # Access data
    animal_data = im.get_data("animal_config")
else:
    print("Input validation failed")
```

#### `get_data()`

```python
def get_data(
    self,
    address: str,
    info_map: dict[str, Any] | None = None
) -> Any:
    """
    Retrieves data from the pool by address (key).

    Parameters
    ----------
    address : str
        The key/path to the desired data in the pool.
    info_map : dict[str, Any] | None
        Optional metadata for logging (class, function names).

    Returns
    -------
    Any
        The requested data from the pool.

    Raises
    ------
    KeyError
        If address doesn't exist in pool.

    Notes
    -----
    Logs all data access for debugging and traceability.
    """
```

**Example**:
```python
# Get animal configuration
animal_config = im.get_data("animal_config")

# Get with info_map for better logging
feed_data = im.get_data(
    "feed_storage_config",
    info_map={"class": "MyClass", "function": "my_function"}
)
```

#### `delete_data()`

```python
def delete_data(
    self,
    address: str,
    info_map: dict[str, Any] | None = None
) -> None:
    """
    Deletes data from the pool.

    Parameters
    ----------
    address : str
        The key/path to the data to delete.
    info_map : dict[str, Any] | None
        Optional metadata for logging.

    Raises
    ------
    KeyError
        If address doesn't exist in pool.

    Notes
    -----
    Logs deletion for audit trail.
    """
```

### Private Methods

#### `_load_metadata()`
```python
def _load_metadata(self, metadata_path: Path) -> None:
    """
    Loads metadata from JSON file to IM metadata dict.

    Parameters
    ----------
    metadata_path : Path
        The path to the metadata file.

    Raises
    ------
    Exception
        If error occurs while opening or reading the file.
    """
```

#### `_load_properties()`
```python
def _load_properties(self) -> None:
    """
    Loads properties data (schemas) from specified JSON file and updates metadata.

    Process:
    1. Read properties file path from metadata
    2. Verify file exists
    3. Load properties into metadata
    4. Remove original properties reference from metadata

    Raises
    ------
    FileNotFoundError
        If properties file doesn't exist.
    """
```

#### `_populate_pool()`
```python
def _populate_pool(self, eager_termination: bool) -> bool:
    """
    Populates the data pool from input files (JSON/CSV) with validation.

    Parameters
    ----------
    eager_termination : bool
        If True, stop on first validation error.

    Returns
    -------
    bool
        True if all data valid, False otherwise.

    Process
    -------
    1. Iterate through all input files in metadata
    2. Load data based on format (JSON/CSV)
    3. Validate against schemas
    4. Attempt to fix fixable errors (type conversions)
    5. Add to pool if valid
    6. Collect validation errors/warnings
    """
```

---

## OutputManager

**Location**: `RUFAS/output_manager.py`

### Overview
Singleton class for centralized logging, results collection, and output file generation. Manages variables, logs, warnings, and errors in separate pools.

### Class Definition

```python
class OutputManager:
    """
    Output manager for RuFaS simulation results. Works by collecting variables,
    logs, warnings, and errors into separate pools, and populates requested
    output channels from the pools once the simulation is done.

    OutputManager is singleton, i.e., only one instance of it can exist.
    """
```

### Enums

#### LogVerbosity

```python
class LogVerbosity(Enum):
    """
    The different types of logs printed by Output Manager.

    Attributes
    ----------
    NONE : str
        Don't print anything.
    CREDITS : str
        Print credits only (default).
    ERRORS : str
        Print credits and errors.
    WARNINGS : str
        Print credits, warnings, and errors.
    LOGS : str
        Print credits, logs, warnings, and errors.
    """
    NONE = "none"
    CREDITS = "credits"
    ERRORS = "errors"
    WARNINGS = "warnings"
    LOGS = "logs"
```

**Comparison Support**:
```python
def __le__(self, other: "LogVerbosity") -> bool:
    """Compare verbosity levels (NONE < CREDITS < ERRORS < WARNINGS < LOGS)."""
```

**Example**:
```python
from RUFAS.output_manager import LogVerbosity

verb = LogVerbosity.WARNINGS
if verb >= LogVerbosity.ERRORS:
    print("Will print errors")  # True
```

#### OriginLabel

```python
class OriginLabel(Enum):
    """
    Labels for data origins when generating JSON output files.

    Attributes
    ----------
    TRUE_AND_REPORT_ORIGINS : str
        Include both true and report origins.
    TRUE_ORIGIN : str
        Include only true origin.
    REPORT_ORIGIN : str
        Include only report origin.
    NONE : str
        No origin information.
    """
    TRUE_AND_REPORT_ORIGINS = "true and report origins"
    TRUE_ORIGIN = "true origin"
    REPORT_ORIGIN = "report origin"
    NONE = "none"
```

### Attributes

```python
variables_pool : dict[str, dict[str, list[dict[str, Any]]]]
    Contains variables reported to the output manager.
warnings_pool : dict[str, dict[str, list[dict[str, Any]]]]
    Contains warnings.
errors_pool : dict[str, dict[str, list[dict[str, Any]]]]
    Contains errors.
logs_pool : dict[str, dict[str, list[dict[str, Any]]]]
    Contains logs.
chunkification : bool
    Enable chunkification for large output pools.
available_memory : int
    Available system memory (bytes).
```

### Main Methods

#### `add_variable()`

```python
def add_variable(
    self,
    name: str,
    value: Any,
    info_map: dict[str, Any],
    report_as: str | None = None
) -> None:
    """
    Adds a variable to the variables pool.

    Parameters
    ----------
    name : str
        Variable name/key.
    value : Any
        Variable value (can be int, float, str, list, dict, Enum, etc.).
    info_map : dict[str, Any]
        Metadata including:
        - "class": Source class name
        - "function": Source function name
        - "units": MeasurementUnits enum (optional)
        - Other custom metadata
    report_as : str | None
        Alternative name for reporting (defaults to `name`).

    Notes
    -----
    - Automatically handles Enum serialization
    - Tracks memory usage for chunkification
    - Excludes info_maps if flag is set
    """
```

**Example**:
```python
from RUFAS.output_manager import OutputManager
from RUFAS.units import MeasurementUnits

om = OutputManager()
info_map = {
    "class": "Animal",
    "function": "calculate_milk_yield",
    "units": MeasurementUnits.KILOGRAMS
}

om.add_variable("daily_milk_kg", 25.5, info_map)
```

#### `add_log()`

```python
def add_log(
    self,
    name: str,
    message: str,
    info_map: dict[str, Any]
) -> None:
    """
    Adds a log message to the logs pool.

    Parameters
    ----------
    name : str
        Log identifier/key.
    message : str
        Log message content.
    info_map : dict[str, Any]
        Metadata (class, function, etc.).

    Notes
    -----
    Prints to terminal if verbosity >= LOGS.
    """
```

**Example**:
```python
om.add_log(
    "herd_initialized",
    "Successfully initialized 100 cows",
    {"class": "HerdManager", "function": "__init__"}
)
```

#### `add_warning()`

```python
def add_warning(
    self,
    name: str,
    message: str,
    info_map: dict[str, Any]
) -> None:
    """
    Adds a warning message to the warnings pool.

    Parameters
    ----------
    name : str
        Warning identifier/key.
    message : str
        Warning message content.
    info_map : dict[str, Any]
        Metadata (class, function, etc.).

    Notes
    -----
    Prints to terminal if verbosity >= WARNINGS.
    """
```

**Example**:
```python
om.add_warning(
    "low_feed_inventory",
    "Corn silage inventory below 7-day threshold",
    {"class": "FeedManager", "function": "check_inventory"}
)
```

#### `add_error()`

```python
def add_error(
    self,
    name: str,
    message: str,
    info_map: dict[str, Any]
) -> None:
    """
    Adds an error message to the errors pool.

    Parameters
    ----------
    name : str
        Error identifier/key.
    message : str
        Error message content.
    info_map : dict[str, Any]
        Metadata (class, function, etc.).

    Notes
    -----
    Prints to terminal if verbosity >= ERRORS.
    """
```

**Example**:
```python
om.add_error(
    "invalid_ration",
    "Ration violates minimum protein constraint (12% required, 10% provided)",
    {"class": "RationOptimizer", "function": "validate_ration"}
)
```

### Output Generation Methods

#### `dump_all_pools()`

```python
def dump_all_pools(
    self,
    output_directory: Path,
    exclude_info_maps: bool,
    origin_label: str
) -> None:
    """
    Writes all pools (variables, logs, warnings, errors) to JSON files.

    Parameters
    ----------
    output_directory : Path
        Directory where JSON files will be written.
    exclude_info_maps : bool
        If True, exclude metadata from output.
    origin_label : str
        Type of origin information to include.

    Outputs
    -------
    - variables.json
    - logs.json
    - warnings.json
    - errors.json
    """
```

#### `dump_all_nondata_pools()`

```python
def dump_all_nondata_pools(
    self,
    logs_directory: Path,
    exclude_info_maps: bool,
    origin_label: str
) -> None:
    """
    Writes non-data pools (logs, warnings, errors) to files.

    Parameters
    ----------
    logs_directory : Path
        Directory for log files.
    exclude_info_maps : bool
        If True, exclude metadata.
    origin_label : str
        Origin label type.

    Outputs
    -------
    - logs.json
    - warnings.json
    - errors.json
    """
```

#### `generate_reports()`

```python
def generate_reports(
    self,
    output_directory: Path,
    report_config: dict[str, Any]
) -> None:
    """
    Generates HTML and CSV reports from variables pool.

    Parameters
    ----------
    output_directory : Path
        Directory for report files.
    report_config : dict[str, Any]
        Report configuration (filters, groupings, etc.).

    Uses
    ----
    ReportGenerator class to create structured reports.

    Outputs
    -------
    - Multiple HTML reports (summary, detailed, domain-specific)
    - CSV exports of key variables
    """
```

#### `generate_graphs()`

```python
def generate_graphs(
    self,
    output_directory: Path,
    graph_config: dict[str, Any]
) -> None:
    """
    Generates PNG graphs from variables pool.

    Parameters
    ----------
    output_directory : Path
        Directory for graph files.
    graph_config : dict[str, Any]
        Graph configuration (variables to plot, styles, etc.).

    Uses
    ----
    GraphGenerator class with matplotlib.

    Outputs
    -------
    - Multiple PNG files (time series, bar charts, distributions)
    """
```

### Utility Methods

#### `create_directory()`

```python
def create_directory(self, directory_path: Path) -> None:
    """
    Creates a directory if it doesn't exist.

    Parameters
    ----------
    directory_path : Path
        Path to the directory to create.

    Notes
    -----
    Creates parent directories as needed (equivalent to mkdir -p).
    """
```

#### `clear_directory()`

```python
def clear_directory(self, directory_path: Path) -> None:
    """
    Deletes all contents of a directory.

    Parameters
    ----------
    directory_path : Path
        Path to the directory to clear.

    Warning
    -------
    This is destructive and cannot be undone.
    """
```

#### `route_logs()`

```python
def route_logs(self, event_logs: list[dict[str, Any]]) -> None:
    """
    Routes event logs to appropriate pools (logs, warnings, errors).

    Parameters
    ----------
    event_logs : list[dict[str, Any]]
        List of log events from DataValidator or other sources.
        Each event has "type" (log/warning/error) and message.

    Notes
    -----
    Used to integrate validation logs into main output system.
    """
```

---

## DataValidator

**Location**: `RUFAS/data_validator.py`

### Overview
Validates input data against schemas with comprehensive error reporting.

### Key Classes

#### Modifiability Enum

```python
class Modifiability(Enum):
    """
    Enum for data modifiability levels.

    Attributes
    ----------
    REQUIRED : str
        Data must be provided and cannot be empty.
    OPTIONAL : str
        Data can be omitted or empty.
    FIXED : str
        Data cannot be modified by user (system-generated).
    """
    REQUIRED = "required"
    OPTIONAL = "optional"
    FIXED = "fixed"
```

### Main Methods

#### `validate_metadata()`

```python
def validate_metadata(
    self,
    metadata: dict[str, Any],
    valid_input_types: set[str],
    address_to_inputs: str
) -> tuple[bool, str]:
    """
    Validates metadata structure.

    Parameters
    ----------
    metadata : dict[str, Any]
        The metadata to validate.
    valid_input_types : set[str]
        Allowed input formats ({"json", "csv"}).
    address_to_inputs : str
        Key for files section ("files").

    Returns
    -------
    tuple[bool, str]
        (is_valid, error_message)
    """
```

#### `validate_properties()`

```python
def validate_properties(
    self,
    metadata: dict[str, Any],
    depth_limit: int
) -> tuple[bool, str]:
    """
    Validates properties (schemas) in metadata.

    Parameters
    ----------
    metadata : dict[str, Any]
        Metadata containing properties.
    depth_limit : int
        Maximum nesting depth allowed.

    Returns
    -------
    tuple[bool, str]
        (is_valid, error_message)

    Checks
    ------
    - Required fields present
    - Type definitions valid
    - Nested structure within depth limit
    - Modifiability correctly specified
    """
```

#### `validate_data()`

```python
def validate_data(
    self,
    data: Any,
    schema: dict[str, Any],
    path: str = ""
) -> tuple[bool, str]:
    """
    Validates data against a schema.

    Parameters
    ----------
    data : Any
        The data to validate.
    schema : dict[str, Any]
        The schema definition.
    path : str
        Path to current data location (for error messages).

    Returns
    -------
    tuple[bool, str]
        (is_valid, error_message)

    Validates
    ---------
    - Data type matches schema
    - Required fields present
    - Value ranges (min/max)
    - String lengths
    - List/dict structures
    - Enum values
    """
```

---

## HerdManager

**Location**: `RUFAS/biophysical/animal/herd_manager.py`

### Overview
Manages all animals in the dairy herd including cows, heifers, and calves.

### Main Methods

#### `daily_update_routine()`

```python
def daily_update_routine(
    self,
    time: RufasTime
) -> dict[str, Any]:
    """
    Executes daily routines for all animals.

    Parameters
    ----------
    time : RufasTime
        Current simulation time.

    Returns
    -------
    dict[str, Any]
        Daily statistics (milk production, feed intake, manure, etc.).

    Process
    -------
    1. Update animal ages
    2. Process feed intake
    3. Calculate milk production (lactating cows)
    4. Update body weight (growth)
    5. Process reproduction (breeding, calving)
    6. Calculate manure production
    7. Update health status
    8. Process culling/deaths
    9. Collect statistics
    """
```

#### `collect_daily_feed_request()`

```python
def collect_daily_feed_request(self) -> dict[str, float]:
    """
    Collects feed requirements from all animal groups.

    Returns
    -------
    dict[str, float]
        Feed requests by feed type (kg dry matter).

    Uses
    ----
    - NASEM nutrient requirements
    - Current rations
    - Animal group sizes
    """
```

---

## ManureManager

**Location**: `RUFAS/biophysical/manure/manure_manager.py`

### Overview
Manages manure collection, treatment, storage, and application.

### Main Methods

#### `process_daily_manure()`

```python
def process_daily_manure(
    self,
    manure_production: dict[str, Any],
    time: RufasTime
) -> None:
    """
    Processes daily manure from animals through management pathways.

    Parameters
    ----------
    manure_production : dict[str, Any]
        Manure amount and composition from animals.
    time : RufasTime
        Current simulation time.

    Process
    -------
    1. Route manure to handlers (parlor, freestall, etc.)
    2. Process through separators (if configured)
    3. Direct to storage (slurry, lagoon, compost, etc.)
    4. Calculate emissions (CH4, N2O, NH3)
    5. Track nutrient transformations
    6. Update storage levels
    """
```

---

## FeedManager

**Location**: `RUFAS/biophysical/feed_storage/feed_manager.py`

### Overview
Manages feed inventory, storage degradation, and feed distribution.

### Main Methods

#### `manage_daily_feed_request()`

```python
def manage_daily_feed_request(
    self,
    requested_feed: dict[str, float],
    time: RufasTime
) -> bool:
    """
    Fulfills daily feed request from inventory.

    Parameters
    ----------
    requested_feed : dict[str, float]
        Feed requests by type (kg DM).
    time : RufasTime
        Current simulation time.

    Returns
    -------
    bool
        True if all feed requests met, False if shortages.

    Process
    -------
    1. Check inventory levels
    2. Deduct requested amounts
    3. Apply storage degradation
    4. Update nutritional composition
    5. Generate warnings for low inventory
    """
```

---

## FieldManager

**Location**: `RUFAS/routines/field/manager/field_manager.py`

### Overview
Manages crop fields, growth simulation, and harvest scheduling.

### Main Methods

#### `daily_update_routine()`

```python
def daily_update_routine(
    self,
    weather: Weather,
    time: RufasTime,
    manure_applications: ManureEventNutrientRequestResults
) -> list[HarvestedCrop]:
    """
    Updates all fields daily.

    Parameters
    ----------
    weather : Weather
        Current weather data.
    time : RufasTime
        Current simulation time.
    manure_applications : ManureEventNutrientRequestResults
        Manure nutrients applied today.

    Returns
    -------
    list[HarvestedCrop]
        Crops harvested today.

    Process
    -------
    1. Update soil moisture and temperature
    2. Process manure applications
    3. Calculate crop growth (GDD, LAI)
    4. Update nutrient uptake
    5. Check harvest triggers
    6. Execute harvests
    7. Calculate yields
    8. Update soil health
    """
```

---

## Utility Functions

**Location**: `RUFAS/util.py`

### Data Aggregation

#### `aggregate_by_sum()`

```python
def aggregate_by_sum(
    data: list[dict[str, Any]],
    key: str
) -> float:
    """
    Sums values from list of dictionaries.

    Parameters
    ----------
    data : list[dict[str, Any]]
        List of dictionaries containing numeric data.
    key : str
        Key to sum across dictionaries.

    Returns
    -------
    float
        Sum of all values.

    Example
    -------
    >>> data = [{"milk": 20}, {"milk": 25}, {"milk": 22}]
    >>> aggregate_by_sum(data, "milk")
    67.0
    """
```

#### `aggregate_by_mean()`

```python
def aggregate_by_mean(
    data: list[dict[str, Any]],
    key: str
) -> float:
    """
    Calculates mean of values from list of dictionaries.

    Parameters
    ----------
    data : list[dict[str, Any]]
        List of dictionaries containing numeric data.
    key : str
        Key to average across dictionaries.

    Returns
    -------
    float
        Mean of all values.
    """
```

### Data Transformations

#### `convert_enum_to_string()`

```python
def convert_enum_to_string(data: Any) -> Any:
    """
    Recursively converts Enum values to strings in nested structures.

    Parameters
    ----------
    data : Any
        Data structure (dict, list, Enum, or primitive).

    Returns
    -------
    Any
        Data with Enums converted to strings.

    Example
    -------
    >>> from enum import Enum
    >>> class Color(Enum):
    ...     RED = "red"
    >>> convert_enum_to_string({"color": Color.RED})
    {"color": "red"}
    """
```

---

## MeasurementUnits Enum

**Location**: `RUFAS/units.py`

### Common Units

```python
class MeasurementUnits(Enum):
    """
    Enumeration of measurement units used throughout RuFaS.
    """
    # Mass
    KILOGRAMS = "kg"
    GRAMS = "g"
    TONNES = "tonnes"

    # Volume
    LITERS = "L"
    MILLILITERS = "mL"

    # Time
    DAYS = "days"
    YEARS = "years"

    # Energy
    MEGACALORIES = "Mcal"
    MEGAJOULES = "MJ"

    # Concentration
    PERCENT = "%"
    PARTS_PER_MILLION = "ppm"

    # Area
    HECTARES = "ha"
    SQUARE_METERS = "m2"

    # Temperature
    CELSIUS = "°C"

    # Other
    UNITLESS = "unitless"
    COUNT = "count"
```

---

## RufasTime

**Location**: `RUFAS/rufas_time.py`

### Time Management

```python
class RufasTime:
    """Manages simulation time using Julian dates."""

    @property
    def current_date(self) -> datetime:
        """Current simulation date."""

    @property
    def simulation_day(self) -> int:
        """Day number in simulation (0-indexed)."""

    @property
    def simulation_length_years(self) -> int:
        """Total simulation length in years."""

    def advance_day(self) -> None:
        """Advance simulation by one day."""

    def get_day_of_year(self) -> int:
        """Get current day of year (1-365)."""
```

---

## Error Handling Patterns

### Standard Info Map

All functions should use consistent info_map structure:

```python
info_map = {
    "class": self.__class__.__name__,
    "function": method_name.__name__,
    "units": MeasurementUnits.APPROPRIATE_UNIT,  # If applicable
    # Additional context-specific keys
}
```

### Error Reporting

```python
# Report errors to OutputManager
om = OutputManager()
om.add_error(
    "error_identifier",
    f"Descriptive error message with context: {variable}",
    info_map
)
```

### Validation Pattern

```python
# Validate input
if not is_valid(data):
    om.add_warning(
        "validation_warning",
        f"Data validation failed for {data_name}",
        info_map
    )
    return default_value
```

---

*For complete implementation details, see the source files in the `RUFAS/` directory.*
