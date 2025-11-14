# RuFaS Practical Guides

This document provides step-by-step guides for common RuFaS tasks, from installation to advanced simulations.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Running Your First Simulation](#running-your-first-simulation)
3. [Understanding Input Configuration](#understanding-input-configuration)
4. [Using the Data Collection App](#using-the-data-collection-app)
5. [Interpreting Simulation Results](#interpreting-simulation-results)
6. [Running Sensitivity Analysis](#running-sensitivity-analysis)
7. [Customizing Farm Configurations](#customizing-farm-configurations)
8. [Debugging Simulations](#debugging-simulations)
9. [Contributing to RuFaS](#contributing-to-rufas)
10. [Advanced Workflows](#advanced-workflows)

---

## Getting Started

### Prerequisites

**System Requirements**:
- Python 3.12 or 3.13
- 4GB+ RAM (8GB recommended for large simulations)
- 500MB disk space
- Linux, macOS, or Windows

**Required Knowledge**:
- Basic Python programming
- Command line/terminal usage
- JSON file format
- Basic understanding of dairy farming (helpful but not required)

### Installation

#### Option 1: From Source (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/RuminantFarmSystems/RuFaS.git
cd RuFaS

# Create virtual environment
python3.12 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -e .

# Verify installation
python main.py --help
```

#### Option 2: Using Poetry

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Clone and install
git clone https://github.com/RuminantFarmSystems/RuFaS.git
cd RuFaS
poetry install
poetry shell
```

### Verify Installation

```bash
# Run example simulation
python main.py -p input/task_manager_metadata.json -v logs

# Run tests (should see 95%+ pass rate)
pytest tests/

# Check code quality
flake8 RUFAS/
black --check RUFAS/
```

**Expected Output**:
```
✅ Simulation complete
✅ Total simulation time: ~30-120 seconds (depending on hardware)
✅ Output files generated in output/
```

---

## Running Your First Simulation

### Step 1: Understand the Metadata Structure

The `task_manager_metadata.json` is the entry point for all simulations.

**Basic Structure**:
```json
{
  "task_type": "A single simulation run",
  "random_seed": 42,
  "files": {
    "properties": "input/properties.json",
    "farm_config": "input/farm_config.json",
    "animal_config": "input/animal_config.json",
    "crop_schedule": "input/crop_schedule.json",
    "field_config": "input/field_config.json",
    "manure_management": "input/manure_management.json"
  }
}
```

**Key Fields**:
- `task_type` - Type of simulation (see TaskType enum in API.md)
- `random_seed` - For reproducibility (optional)
- `files` - Paths to all input data files

### Step 2: Prepare Input Files

**Minimum Required Files**:
1. `task_manager_metadata.json` - Main configuration
2. `properties.json` - Data schemas
3. `farm_config.json` - Farm-level settings
4. `animal_config.json` - Herd configuration
5. `crop_schedule.json` - Crop planting/harvest schedule
6. `field_config.json` - Field definitions
7. `manure_management.json` - Manure handling configuration

**Use Provided Examples**:
```bash
# Copy example inputs to your working directory
cp -r input/examples/simple_dairy input/my_farm
```

### Step 3: Run the Simulation

**Basic Command**:
```bash
python main.py -p input/my_farm/task_manager_metadata.json
```

**With Options**:
```bash
# Verbose logging with graphics
python main.py -p input/my_farm/task_manager_metadata.json -v logs

# Clear output directory first
python main.py -p input/my_farm/task_manager_metadata.json -c

# Custom output directory
python main.py -p input/my_farm/task_manager_metadata.json -o output/run_2024_11_14
```

### Step 4: Check the Output

**Output Directory Structure**:
```
output/
├── variables.json          # All simulation variables
├── logs/
│   ├── logs.json           # Informational logs
│   ├── warnings.json       # Warnings (non-fatal)
│   └── errors.json         # Errors (may be fatal)
├── reports/
│   ├── summary.html        # Overview report
│   ├── animal_report.html  # Animal module details
│   ├── manure_report.html  # Manure module details
│   └── *.csv               # CSV exports
└── graphs/
    ├── milk_production.png
    ├── feed_inventory.png
    ├── emissions.png
    └── *.png
```

**Quick Validation**:
```bash
# Check for errors
cat output/logs/errors.json

# View summary (if jq installed)
jq '.simulation_summary' output/variables.json

# Open HTML report in browser
open output/reports/summary.html  # macOS
xdg-open output/reports/summary.html  # Linux
start output/reports/summary.html  # Windows
```

---

## Understanding Input Configuration

### Farm Configuration (`farm_config.json`)

**Purpose**: Define farm-level parameters like location, simulation period, economic factors.

**Example**:
```json
{
  "farm_name": "Green Valley Dairy",
  "location": {
    "latitude": 42.5,
    "longitude": -76.5,
    "elevation_m": 250
  },
  "simulation_start_date": "2024-01-01",
  "simulation_length_years": 1,
  "weather_file": "input/weather/ithaca_2024.csv",
  "milk_price_per_kg": 0.40,
  "feed_purchase_enabled": true
}
```

**Key Parameters**:
- `simulation_length_years` - Duration (1-10 years typical)
- `weather_file` - Daily weather data (temp, precipitation, solar radiation)
- `milk_price_per_kg` - Economic output (USD/kg)
- `feed_purchase_enabled` - Allow buying feed if inventory low

### Animal Configuration (`animal_config.json`)

**Purpose**: Define herd structure, genetics, management.

**Example**:
```json
{
  "cows": {
    "initial_count": 100,
    "breed": "Holstein",
    "average_body_weight_kg": 650,
    "average_days_in_milk": 150,
    "target_milk_production_kg_per_day": 35,
    "breeding_strategy": "year_round",
    "culling_rate_annual": 0.30
  },
  "heifers": {
    "heifer_I_count": 50,
    "heifer_II_count": 40,
    "age_at_first_breeding_months": 15,
    "target_age_at_first_calving_months": 24
  },
  "calves": {
    "male_calf_retention": "none",
    "calf_mortality_rate": 0.05,
    "weaning_age_days": 56
  }
}
```

**Key Decisions**:
- **Breed**: Holstein (high milk), Jersey (high fat/protein), crossbred
- **Breeding strategy**: year_round, seasonal, split_herd
- **Culling rate**: 25-40% typical for dairy

### Crop Schedule (`crop_schedule.json`)

**Purpose**: Define what crops are grown, when, and on which fields.

**Example**:
```json
{
  "crops": [
    {
      "crop_name": "corn_silage",
      "planting_date": "2024-05-15",
      "harvest_date": "2024-09-20",
      "target_yield_tonnes_per_ha": 50,
      "fields": ["field_1", "field_2"]
    },
    {
      "crop_name": "alfalfa",
      "planting_date": "2024-04-20",
      "first_harvest_date": "2024-06-01",
      "harvest_interval_days": 35,
      "number_of_harvests": 4,
      "target_yield_tonnes_per_ha": 12,
      "fields": ["field_3", "field_4"]
    }
  ]
}
```

**Common Crops**:
- `corn_silage` - High energy, single harvest
- `alfalfa` - High protein, multiple harvests
- `grass_hay` - Moderate quality, multiple harvests
- `corn_grain` - Concentrated energy

### Manure Management (`manure_management.json`)

**Purpose**: Define how manure is collected, stored, and applied.

**Example**:
```json
{
  "collection": {
    "parlor_washing": {
      "type": "flush_system",
      "flush_volume_liters_per_cow_per_day": 100
    },
    "freestall_scraping": {
      "type": "mechanical_scraper",
      "frequency_per_day": 4
    }
  },
  "storage": [
    {
      "type": "anaerobic_lagoon",
      "capacity_cubic_meters": 2000,
      "covered": false,
      "methane_capture": false
    },
    {
      "type": "slurry_tank",
      "capacity_cubic_meters": 500,
      "covered": true
    }
  ],
  "application": {
    "strategy": "scheduled_events",
    "events": [
      {
        "date": "2024-04-10",
        "fields": ["field_1", "field_2"],
        "rate_tonnes_per_ha": 40,
        "method": "injection"
      }
    ]
  }
}
```

**Storage Options**:
- `anaerobic_lagoon` - Low cost, high emissions
- `slurry_tank` - Covered storage, lower emissions
- `composting` - Solid manure, nutrient-rich
- `bedded_pack` - Deep bedding systems

---

## Using the Data Collection App

### Overview

The Data Collection App (DCA) is an HTML/JavaScript interface for creating input files without editing JSON manually.

**Location**: `DataCollectionApp/index.html`

### Opening the App

```bash
# Open in browser (from RuFaS root directory)
open DataCollectionApp/index.html  # macOS
xdg-open DataCollectionApp/index.html  # Linux
start DataCollectionApp/index.html  # Windows
```

### Creating a New Configuration

**Step 1: Select Configuration Type**

Click the tab for the configuration you want to create:
- Farm Configuration
- Animal Configuration
- Crop Schedule
- Field Configuration
- Manure Management

**Step 2: Fill in Form Fields**

The app generates forms based on JSON schemas. Each field has:
- **Label** - Field name
- **Description** - Help text
- **Input Type** - Text box, dropdown, number, date picker
- **Validation** - Required fields, min/max values

**Example: Creating Animal Config**

1. Click "Animal Configuration" tab
2. Fill in cow parameters:
   - Initial Count: 100
   - Breed: Select "Holstein" from dropdown
   - Average Body Weight: 650 (kg)
   - Target Milk Production: 35 (kg/day)
3. Fill in heifer parameters
4. Fill in calf parameters
5. Click "Validate" to check for errors
6. Click "Download JSON" to save file

**Step 3: Import Existing Configuration**

To modify existing JSON:
1. Click "Import JSON" button
2. Select your JSON file
3. Form fields populate automatically
4. Edit as needed
5. Click "Validate"
6. Download updated JSON

### Advanced Features

**JSON Editor Mode**:
- Click "Switch to JSON Editor" for direct JSON editing
- Uses ACE Editor with syntax highlighting
- Validates on-the-fly

**Templates**:
- Click "Load Template" to use pre-built configurations
- Templates available for common farm types:
  - Small dairy (50 cows)
  - Medium dairy (100-200 cows)
  - Large dairy (500+ cows)

**Data Compression**:
- Large configurations auto-compress using LZ-String
- Reduces file size by 60-80%
- Automatically decompressed on import

---

## Interpreting Simulation Results

### Variables File (`variables.json`)

**Structure**:
```json
{
  "variable_name": [
    {
      "value": <actual value>,
      "info_map": {
        "class": "SourceClass",
        "function": "source_function",
        "units": "kg",
        "simulation_day": 0
      }
    },
    ...
  ]
}
```

**Key Variables**:

#### Milk Production
```json
"daily_milk_kg": [
  {"value": 3450, "info_map": {"units": "kg", "simulation_day": 0}},
  {"value": 3475, "info_map": {"units": "kg", "simulation_day": 1}},
  ...
]
```

#### Feed Inventory
```json
"feed_inventory": [
  {
    "value": {
      "corn_silage_kg_dm": 45000,
      "alfalfa_hay_kg_dm": 12000,
      "corn_grain_kg_dm": 8000
    },
    "info_map": {"units": "kg_dm", "simulation_day": 0}
  },
  ...
]
```

#### Greenhouse Gas Emissions
```json
"daily_enteric_methane_kg": [...],
"daily_manure_methane_kg": [...],
"daily_nitrous_oxide_kg": [...],
"daily_co2_equivalent_tonnes": [...]
```

### Analyzing Results with Python

```python
import json
import pandas as pd
import matplotlib.pyplot as plt

# Load variables
with open('output/variables.json') as f:
    variables = json.load(f)

# Extract daily milk production
milk_data = [entry['value'] for entry in variables['daily_milk_kg']]
days = range(len(milk_data))

# Plot
plt.figure(figsize=(12, 6))
plt.plot(days, milk_data)
plt.xlabel('Simulation Day')
plt.ylabel('Milk Production (kg/day)')
plt.title('Herd Milk Production Over Time')
plt.grid(True)
plt.savefig('milk_production_analysis.png')

# Calculate statistics
mean_milk = sum(milk_data) / len(milk_data)
max_milk = max(milk_data)
min_milk = min(milk_data)

print(f"Average Daily Milk: {mean_milk:.2f} kg")
print(f"Peak Production: {max_milk:.2f} kg")
print(f"Minimum Production: {min_milk:.2f} kg")
```

### HTML Reports

**Summary Report** (`reports/summary.html`):
- Farm overview
- Key performance indicators (KPIs)
- Total milk production
- Feed consumption
- Emissions summary
- Economic metrics

**Domain-Specific Reports**:
- `animal_report.html` - Herd dynamics, reproduction, health
- `manure_report.html` - Manure flows, storage levels, emissions
- `field_report.html` - Crop yields, nutrient balances
- `feed_report.html` - Feed inventory, purchases, degradation

### Warning and Error Interpretation

**Common Warnings** (`logs/warnings.json`):

```json
{
  "low_feed_inventory": {
    "message": "Corn silage inventory below 7-day threshold",
    "source": "FeedManager.check_inventory",
    "simulation_day": 245,
    "action": "Consider purchasing feed or adjusting rations"
  }
}
```

**Action**:
- Review crop schedule (increase planting)
- Enable feed purchasing in farm_config
- Reduce animal count

**Common Errors** (`logs/errors.json`):

```json
{
  "invalid_ration": {
    "message": "Ration violates minimum protein constraint",
    "source": "RationOptimizer.validate_ration",
    "required": "0.12",
    "provided": "0.10",
    "action": "Increase protein feed availability"
  }
}
```

**Action**:
- Increase alfalfa/protein supplement in feed mix
- Adjust crop schedule to plant more protein crops
- Review ration formulation parameters

---

## Running Sensitivity Analysis

### Purpose

Sensitivity Analysis (SA) identifies which input parameters most influence outputs (e.g., milk production, emissions).

**Use Cases**:
- Understand model behavior
- Identify key decision variables
- Quantify uncertainty
- Optimize farm management

### Configuring Sensitivity Analysis

**Metadata File** (`input/sensitivity_analysis.json`):

```json
{
  "task_type": "Sensitivity Analysis",
  "sa_method": "sobol",
  "num_samples": 1024,
  "parameters": [
    {
      "name": "feed_protein_fraction",
      "address": "animal_config.ration.protein_fraction",
      "bounds": [0.12, 0.20]
    },
    {
      "name": "milk_price",
      "address": "farm_config.milk_price_per_kg",
      "bounds": [0.30, 0.50]
    },
    {
      "name": "corn_silage_yield",
      "address": "crop_schedule.crops[0].target_yield_tonnes_per_ha",
      "bounds": [40, 60]
    }
  ],
  "output_variables": [
    "total_annual_milk_kg",
    "total_annual_emissions_tonnes_co2e",
    "feed_cost_per_kg_milk"
  ]
}
```

**SA Methods**:

1. **Sobol** - Global sensitivity, first-order and total-order indices
   - Best for: Identifying interactions
   - Samples: 1024-4096 (N*(2D+2) where D=params)
   - Runtime: Long (hours to days)

2. **Morris** - Elementary effects screening
   - Best for: Quick parameter ranking
   - Samples: 100-500
   - Runtime: Medium (minutes to hours)

3. **Fractional Factorial** - Main effects and 2-way interactions
   - Best for: Designed experiments
   - Samples: 2^k designs (k=params)
   - Runtime: Short (minutes)

### Running Sensitivity Analysis

```bash
# Basic SA run
python main.py -p input/sensitivity_analysis.json -v logs

# Suppress graphics to save time
python main.py -p input/sensitivity_analysis.json -g

# Use multiple CPU cores (automatic with multiprocessing)
# RuFaS automatically detects available cores
```

**Progress Monitoring**:
```
Running Sobol Sensitivity Analysis...
Sample 0/1024 complete (0%)
Sample 100/1024 complete (10%)
Sample 500/1024 complete (49%)
Sample 1024/1024 complete (100%)
Calculating sensitivity indices...
```

### Interpreting SA Results

**Output File** (`output/sensitivity_analysis_results.json`):

```json
{
  "method": "sobol",
  "num_samples": 1024,
  "results": {
    "total_annual_milk_kg": {
      "first_order": {
        "feed_protein_fraction": 0.15,
        "milk_price": 0.02,
        "corn_silage_yield": 0.45
      },
      "total_order": {
        "feed_protein_fraction": 0.22,
        "milk_price": 0.03,
        "corn_silage_yield": 0.68
      }
    }
  }
}
```

**Interpretation**:
- **First-order (S1)**: Direct effect of parameter alone
  - `corn_silage_yield: 0.45` → 45% of milk variance explained by silage yield alone
- **Total-order (ST)**: Total effect including interactions
  - `corn_silage_yield: 0.68` → 68% including interactions with other params
- **Interaction (ST - S1)**: Synergistic effects
  - `corn_silage_yield: 0.68 - 0.45 = 0.23` → 23% from interactions

**Decision Making**:
1. Focus management efforts on high first-order parameters
2. Investigate interactions for high (ST - S1) values
3. Parameters with low ST can be fixed at nominal values

### Visualizing SA Results

```python
import json
import matplotlib.pyplot as plt

# Load SA results
with open('output/sensitivity_analysis_results.json') as f:
    sa_results = json.load(f)

# Extract Sobol indices for milk production
results = sa_results['results']['total_annual_milk_kg']
params = list(results['first_order'].keys())
s1 = [results['first_order'][p] for p in params]
st = [results['total_order'][p] for p in params]

# Plot
fig, ax = plt.subplots(figsize=(10, 6))
x = range(len(params))
width = 0.35
ax.bar([i - width/2 for i in x], s1, width, label='First-order (S1)')
ax.bar([i + width/2 for i in x], st, width, label='Total-order (ST)')
ax.set_xlabel('Parameters')
ax.set_ylabel('Sensitivity Index')
ax.set_title('Sobol Sensitivity Analysis: Milk Production')
ax.set_xticks(x)
ax.set_xticklabels(params, rotation=45, ha='right')
ax.legend()
plt.tight_layout()
plt.savefig('sensitivity_analysis.png')
```

---

## Customizing Farm Configurations

### Creating Custom Crops

**Step 1: Define Crop Properties**

Edit `input/properties.json` to add new crop:

```json
{
  "crops": {
    "sorghum_silage": {
      "type": "forage",
      "dry_matter_fraction": 0.30,
      "nutrients": {
        "cp_fraction": 0.08,  // Crude protein
        "ndf_fraction": 0.55,  // Neutral detergent fiber
        "nfc_fraction": 0.30,  // Non-fiber carbohydrate
        "fat_fraction": 0.03,
        "ash_fraction": 0.04
      },
      "energy_mcal_per_kg_dm": 2.4,
      "storage_degradation_rate_per_day": 0.002
    }
  }
}
```

**Step 2: Add to Crop Schedule**

```json
{
  "crops": [
    {
      "crop_name": "sorghum_silage",
      "planting_date": "2024-06-01",
      "harvest_date": "2024-09-15",
      "target_yield_tonnes_per_ha": 45,
      "fields": ["field_5"]
    }
  ]
}
```

### Custom Ration Formulation

**Override Default Ration**:

```json
{
  "animal_config": {
    "cows": {
      "custom_ration": {
        "corn_silage_fraction": 0.35,
        "alfalfa_hay_fraction": 0.25,
        "corn_grain_fraction": 0.20,
        "soybean_meal_fraction": 0.10,
        "mineral_supplement_fraction": 0.05,
        "fat_supplement_fraction": 0.05
      },
      "ration_reformulation_interval_days": 30
    }
  }
}
```

**Ration Constraints**:
```json
{
  "ration_constraints": {
    "min_protein_fraction": 0.16,
    "max_protein_fraction": 0.20,
    "min_ndf_fraction": 0.28,
    "max_ndf_fraction": 0.35,
    "min_nfc_fraction": 0.35,
    "max_nfc_fraction": 0.45,
    "target_energy_mcal_per_day": 65
  }
}
```

### Custom Manure Treatment

**Add Anaerobic Digester**:

```json
{
  "manure_management": {
    "treatment": {
      "anaerobic_digester": {
        "capacity_cubic_meters_per_day": 50,
        "retention_time_days": 20,
        "temperature_celsius": 38,
        "methane_capture_efficiency": 0.85,
        "biogas_electricity_conversion_kwh_per_m3": 2.0,
        "digestate_separation": true
      }
    }
  }
}
```

**Benefits**:
- Methane capture (reduce emissions + energy)
- Nutrient concentration
- Odor reduction

---

## Debugging Simulations

### Common Issues and Solutions

#### Issue 1: Input Validation Errors

**Symptom**:
```
ValueError: Data validation failed for animal_config.cows.initial_count
Expected type: integer, Found: string
```

**Solution**:
```json
// ❌ Wrong
{"initial_count": "100"}

// ✅ Correct
{"initial_count": 100}
```

**Prevention**:
- Use Data Collection App (auto-validates)
- Check `properties.json` for required types
- Run with `-v logs` to see detailed validation messages

#### Issue 2: Feed Shortages

**Symptom**:
```
Warning: Feed shortage on day 245
Requested: 1200 kg corn_silage
Available: 800 kg
```

**Debug Steps**:

1. Check feed inventory over time:
```python
import json
with open('output/variables.json') as f:
    vars = json.load(f)
inventory = vars['feed_storage_levels']
# Plot to identify when shortage starts
```

2. Review crop yields:
```bash
grep "harvest" output/logs/logs.json
```

3. Increase production or enable purchases:
```json
// Increase yield
{"target_yield_tonnes_per_ha": 55}  // was 50

// Enable purchases
{"feed_purchase_enabled": true}
```

#### Issue 3: Slow Simulation

**Symptom**: Simulation takes >5 minutes for 1-year run

**Profiling**:
```bash
# Run with Python profiler
python -m cProfile -o profile.stats main.py -p input/config.json

# Analyze with snakeviz
pip install snakeviz
snakeviz profile.stats
```

**Common Bottlenecks**:
- Large herd size (>1000 animals) → Consider aggregated pens
- Daily ration optimization → Increase `ration_reformulation_interval_days`
- Excessive output variables → Filter variables in post-processing

**Optimization**:
```json
{
  "performance_settings": {
    "enable_numba_jit": true,  // Use JIT compilation
    "output_frequency_days": 7,  // Log weekly instead of daily
    "aggregate_small_pens": true  // Group similar animals
  }
}
```

#### Issue 4: Unexpected Results

**Symptom**: Milk production 50% lower than expected

**Debug Workflow**:

1. **Check warnings/errors**:
```bash
cat output/logs/warnings.json | jq '.feed_quality'
```

2. **Trace feed intake**:
```python
# Check if animals are getting enough feed
dry_matter_intake = vars['daily_dmi_kg']
target_dmi = vars['target_dmi_kg']
deficit = [t - a for t, a in zip(target_dmi, dry_matter_intake)]
```

3. **Review ration quality**:
```bash
# Check if ration meets energy/protein requirements
grep "ration" output/logs/logs.json
```

4. **Validate inputs**:
```bash
# Re-run with input audit
python main.py -p input/audit_metadata.json
# audit_metadata.json:
# {"task_type": "Validates input data and saves metadata properties as CSV"}
```

---

## Contributing to RuFaS

### Contribution Workflow

**Step 1: Fork and Clone**

```bash
# Fork on GitHub UI
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/RuFaS.git
cd RuFaS
git remote add upstream https://github.com/RuminantFarmSystems/RuFaS.git
```

**Step 2: Create Feature Branch**

```bash
# Sync with upstream
git fetch upstream
git checkout dev
git merge upstream/dev

# Create feature branch
git checkout -b feature/your-feature-name
```

**Step 3: Develop with Tests**

```bash
# Install dev dependencies
pip install -e .[dev]

# Write code following style guide
# - Black formatting (120 char lines)
# - Type hints (Mypy strict mode)
# - Docstrings (Google style)

# Write tests
# Create tests/test_your_feature.py

# Run tests locally
pytest tests/test_your_feature.py -v

# Check coverage
pytest --cov=RUFAS tests/test_your_feature.py
```

**Step 4: Format and Lint**

```bash
# Format code
black RUFAS/ tests/

# Lint
flake8 RUFAS/ tests/

# Type check
mypy RUFAS/
```

**Step 5: Commit and Push**

```bash
# Stage changes
git add RUFAS/your_module.py tests/test_your_feature.py

# Commit with conventional message
git commit -m "feat(animal): add custom lactation curve models

- Implement Wood's, Dijkstra, and Wilmink curves
- Add parameter estimation from farm data
- Include tests with 95% coverage
- Update documentation

Closes #123"

# Push to your fork
git push origin feature/your-feature-name
```

**Step 6: Open Pull Request**

1. Go to GitHub
2. Click "Compare & Pull Request"
3. Fill in template:
   - **Description**: What and why
   - **Testing**: How you tested
   - **Documentation**: Updated docs
   - **Checklist**: Format, lint, tests pass
4. Tag reviewers (e.g., @maintainer1)
5. Wait for CI checks to pass
6. Address review comments
7. Merge when approved

### Code Style Guidelines

**Docstring Example**:

```python
def calculate_milk_yield(
    self,
    body_weight_kg: float,
    days_in_milk: int,
    energy_intake_mcal: float
) -> float:
    """
    Calculate daily milk yield using energy balance.

    Parameters
    ----------
    body_weight_kg : float
        Current body weight in kilograms.
    days_in_milk : int
        Days since calving (0-305 typical).
    energy_intake_mcal : float
        Net energy for lactation consumed (Mcal/day).

    Returns
    -------
    float
        Daily milk yield in kilograms.

    Raises
    ------
    ValueError
        If body_weight_kg <= 0 or days_in_milk < 0.

    Examples
    --------
    >>> cow = Animal()
    >>> milk_kg = cow.calculate_milk_yield(650, 100, 35.5)
    >>> print(f"Milk: {milk_kg:.1f} kg")
    Milk: 32.5 kg

    Notes
    -----
    Uses NASEM (2021) energy partitioning equations.
    """
```

### Running Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

**Hooks Check**:
- Black formatting
- Flake8 linting
- Trailing whitespace
- YAML/JSON syntax
- Large file prevention

---

## Advanced Workflows

### Multi-Run Uncertainty Quantification

**Purpose**: Quantify output variability from stochastic processes (weather, animal variation, etc.).

**Configuration**:
```json
{
  "task_type": "Multiple simulation with different random seeds",
  "num_runs": 50,
  "random_seed_start": 0,
  "output_aggregation": "all",
  "parallel_execution": true
}
```

**Analysis**:
```python
import json
import numpy as np

# Load multi-run results
runs = []
for i in range(50):
    with open(f'output/run_{i}/variables.json') as f:
        runs.append(json.load(f))

# Extract annual milk production from each run
annual_milk = [sum(run['daily_milk_kg']) for run in runs]

# Calculate statistics
mean = np.mean(annual_milk)
std = np.std(annual_milk)
ci_95 = (np.percentile(annual_milk, 2.5), np.percentile(annual_milk, 97.5))

print(f"Mean: {mean:.0f} kg")
print(f"Std Dev: {std:.0f} kg")
print(f"95% CI: {ci_95}")
```

### End-to-End Testing

**Purpose**: Ensure simulation results match expected values (regression testing).

**Setup**:
```bash
# Generate expected results
python main.py -p input/e2e_test_config.json

# Save as expected
cp output/variables.json tests/e2e/expected_results.json

# Run E2E test
python main.py -p input/e2e_metadata.json
# e2e_metadata.json:
# {"task_type": "Run e2e testing"}
```

**Comparison**:
- Automatic comparison with expected results
- Tolerance for floating-point differences
- Reports any deviations

### Integrating External Weather Data

**Weather File Format** (`weather.csv`):
```csv
date,temp_min_c,temp_max_c,precip_mm,solar_radiation_mj_m2
2024-01-01,-5,2,0,8.5
2024-01-02,-3,4,2.5,6.2
2024-01-03,0,7,0,10.1
...
```

**Download from Online Sources**:
```python
import requests
import pandas as pd

# Example: NOAA API (requires API key)
api_key = "YOUR_API_KEY"
station = "USW00014733"  # Ithaca, NY
start_date = "2024-01-01"
end_date = "2024-12-31"

url = f"https://www.ncdc.noaa.gov/cdo-web/api/v2/data"
params = {
    "datasetid": "GHCND",
    "stationid": station,
    "startdate": start_date,
    "enddate": end_date,
    "units": "metric"
}
headers = {"token": api_key}

response = requests.get(url, params=params, headers=headers)
data = response.json()

# Convert to RuFaS format
df = pd.DataFrame(data['results'])
df.to_csv('input/weather/custom_weather.csv', index=False)
```

**Alternative: Use Synthetic Weather**:
```python
# RuFaS includes weather generator for sensitivity tests
{
  "weather": {
    "source": "synthetic",
    "location": {"latitude": 42.5, "longitude": -76.5},
    "year": 2024,
    "variability": "typical"  // "dry", "wet", "typical"
  }
}
```

---

*For more guides and tutorials, visit the [RuFaS documentation](https://ruminantfarmsystems.github.io/RuFaS/).*
