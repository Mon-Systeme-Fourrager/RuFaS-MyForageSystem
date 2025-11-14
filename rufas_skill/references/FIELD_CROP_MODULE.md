# Field & Crop Module Reference

Comprehensive reference for RuFaS field and crop modeling.

---

## Overview

The Field & Crop Module simulates:
- Crop growth and development
- Soil processes (water, nutrients, carbon)
- Nutrient cycling (N, P, C)
- Field management operations
- Harvest scheduling and yield prediction
- Environmental impacts (erosion, leaching, GHG)

**Location**: `RUFAS/routines/field/`

---

## Core Classes

### FieldManager

**File**: `manager/field_manager.py`

**Purpose**: Orchestrates all field-level operations across the farm.

**Key Attributes**:
```python
fields: list[Field]                    # All field instances
output_gatherer: FieldDataReporter     # Data collection
crop_to_rufas_ids: dict                # Crop-to-feed mapping
```

**Key Methods**:
```python
daily_update_routine(
    weather: Weather,
    time: RufasTime,
    manure_applications: list
) -> list[HarvestedCrop]:
    """
    Execute daily routines for all fields.

    Returns crops harvested today.
    """

get_next_harvest_dates(crop_names: list[str]) -> dict[str, date]:
    """Get projected harvest dates for planning."""

get_crop_configs_to_rufas_ids() -> dict:
    """Map crop types to feed IDs for animal feeding."""
```

### Field

**File**: `field/field.py`

**Purpose**: Represents individual field with crop and soil.

**Key Components**:
```python
field_data: FieldData                  # Static field properties
soil: Soil                             # Soil profile and processes
current_crop: Crop | None              # Currently growing crop
crop_schedule: CropSchedule            # Planting/harvest timing
```

**Daily Routine**:
```python
def daily_routine(weather, time, manure_nutrients) -> list[HarvestedCrop]:
    """
    1. Update soil moisture and temperature
    2. Process inputs (manure, fertilizer, tillage)
    3. Calculate crop growth
    4. Update nutrient cycling
    5. Check harvest triggers
    6. Execute harvest if ready
    """
```

---

## Crop Growth

### Crop Base Class

**File**: `crop/crop.py`

**Purpose**: Simulates crop growth and development.

**Growth Stages**:
```python
class GrowthStage(Enum):
    PLANTING = "planting"
    EMERGENCE = "emergence"
    VEGETATIVE = "vegetative"
    REPRODUCTIVE = "reproductive"
    MATURITY = "maturity"
    SENESCENCE = "senescence"
```

**Key Processes**:

#### 1. Heat Unit Accumulation

**File**: `crop/heat_units.py`

**Growing Degree Days (GDD)**:
```python
# Base temperature method
GDD = max(0, (T_max + T_min) / 2 - T_base)

# Crop-specific base temperatures:
# - Corn: 10°C
# - Alfalfa: 5°C
# - Grass: 0°C
# - Small grains: 0°C

# Maturity triggers:
# - Corn silage: 1200-1400 GDD
# - Corn grain: 2400-2800 GDD
# - Alfalfa: 400-600 GDD per cutting
```

#### 2. Biomass Accumulation

**File**: `crop/biomass_allocation.py`

**Daily Growth**:
```python
# Radiation use efficiency (RUE) model
daily_growth_kg_ha = (
    intercepted_PAR_MJ_m2 *
    RUE_g_MJ *
    10  # Convert to kg/ha
)

# Intercepted PAR
intercepted_PAR = incident_PAR * (1 - exp(-k * LAI))
# k = extinction coefficient (0.4-0.6)
# LAI = leaf area index

# Stress factors
daily_growth *= water_stress_factor
daily_growth *= nitrogen_stress_factor
daily_growth *= temperature_stress_factor
```

**Partitioning**:
```python
# Biomass allocation to plant parts
if growth_stage == "vegetative":
    root_fraction = 0.40
    leaf_fraction = 0.50
    stem_fraction = 0.10
elif growth_stage == "reproductive":
    root_fraction = 0.10
    leaf_fraction = 0.20
    stem_fraction = 0.30
    grain_fraction = 0.40
```

#### 3. Leaf Area Index (LAI)

**File**: `crop/leaf_area_index.py`

**LAI Development**:
```python
# Early season (exponential)
LAI(t) = LAI_initial * exp(k * GDD)

# Mid-season (plateau)
LAI(t) = LAI_max

# Late season (senescence)
LAI(t) = LAI_max * exp(-k_sen * days_after_maturity)

# Typical LAI_max values:
# - Corn: 5-7
# - Alfalfa: 4-6
# - Grass: 3-5
```

#### 4. Root Development

**File**: `crop/root_development.py`

**Root Growth**:
```python
# Rooting depth
root_depth_cm = root_depth_max * (1 - exp(-k * GDD / GDD_max))

# Maximum rooting depths:
# - Corn: 150-200 cm
# - Alfalfa: 200-300 cm
# - Grass: 60-100 cm
# - Small grains: 100-150 cm

# Root density distribution (exponential decay)
root_density(z) = root_mass_surface * exp(-extinction * z)
```

---

## Nutrient Uptake

### Nitrogen Uptake

**File**: `crop/nitrogen_uptake.py`

**N Demand**:
```python
# Crop N requirement
N_demand_kg_ha = biomass_kg_ha * N_concentration_target

# N concentration targets (% of DM):
# - Corn vegetative: 3.5%
# - Corn grain fill: 1.5%
# - Alfalfa: 3.5-4.5%
# - Grass: 2.5-3.5%

# N uptake rate
daily_N_uptake = min(N_demand, N_supply)

# N supply from soil
N_supply = (
    soil_NO3_N_ppm *
    root_density *
    soil_water_content *
    uptake_efficiency
)
```

**N Stress**:
```python
N_stress_factor = actual_N_uptake / optimal_N_uptake

if N_stress_factor < 0.8:
    # Reduce growth
    biomass_growth *= N_stress_factor
    # Increase root allocation
    root_fraction *= 1.2
```

### Phosphorus Uptake

**File**: `crop/phosphorus_uptake.py`

**P Demand**:
```python
# Crop P requirement
P_demand_kg_ha = biomass_kg_ha * P_concentration_target

# P concentration targets (% of DM):
# - Corn: 0.3-0.4%
# - Alfalfa: 0.25-0.35%
# - Grass: 0.25-0.30%

# P uptake (Michaelis-Menten kinetics)
P_uptake = (V_max * soil_P) / (K_m + soil_P)
# V_max = maximum uptake rate
# K_m = half-saturation constant
```

### Water Uptake

**File**: `crop/water_uptake.py`

**Transpiration**:
```python
# Potential evapotranspiration (Penman-Monteith)
ET_pot_mm = (
    0.408 * delta * (Rn - G) +
    gamma * (900 / (T + 273)) * u2 * (es - ea)
) / (delta + gamma * (1 + 0.34 * u2))

# Crop coefficient method
ET_crop = ET_pot * Kc

# Kc values (growth stage dependent):
# - Initial: 0.3-0.5
# - Mid-season: 1.0-1.2
# - Late season: 0.5-0.7

# Water stress
water_stress_factor = actual_ET / potential_ET
```

**Root Water Extraction**:
```python
# Extract water from each soil layer
for layer in soil_layers:
    available_water = (
        (layer.water_content - layer.wilting_point) *
        layer.thickness
    )
    potential_uptake = (
        ET_crop *
        root_density_fraction[layer] *
        water_stress_response
    )
    actual_uptake = min(available_water, potential_uptake)
```

---

## Soil Processes

### Soil Class

**File**: `soil/soil.py`

**Purpose**: Multi-layer soil profile with physical and chemical processes.

**Soil Layers**:
```python
class LayerData:
    """Represents a single soil layer."""
    thickness_cm: float                # Layer depth
    bulk_density_g_cm3: float          # Soil compaction
    clay_fraction: float               # 0-1
    sand_fraction: float               # 0-1
    silt_fraction: float               # 0-1
    organic_matter_pct: float          # %
    pH: float                          # 4-9
    water_content_mm: float            # Current moisture
    field_capacity_mm: float           # Maximum storage
    wilting_point_mm: float            # Plant unavailable
```

### Water Dynamics

#### Infiltration

**File**: `soil/infiltration.py`

**Green-Ampt Model**:
```python
infiltration_rate_mm_hr = (
    hydraulic_conductivity *
    (1 + (suction_head * deficit) / cumulative_infiltration)
)

# Hydraulic conductivity by texture:
# - Sand: 10-30 mm/hr
# - Loam: 5-15 mm/hr
# - Clay: 1-5 mm/hr
```

#### Percolation

**File**: `soil/percolation.py`

**Downward Flow**:
```python
# Tipping bucket model
if layer.water_content > layer.field_capacity:
    excess_water = layer.water_content - layer.field_capacity
    percolation = excess_water * drainage_coefficient
    layer_below.water_content += percolation
```

#### Evaporation

**File**: `soil/evaporation.py`

**Soil Surface Evaporation**:
```python
# Stage 1: Energy-limited (wet soil)
evaporation_stage1 = 0.8 * ET_pot * exp(-0.4 * LAI)

# Stage 2: Soil-limited (dry soil)
evaporation_stage2 = (
    sqrt(hydraulic_conductivity * time_since_wetting) *
    0.35
)
```

---

## Nutrient Cycling

### Nitrogen Cycling

**File**: `soil/nitrogen_cycling/nitrogen_cycling.py`

**N Pools**:
```python
# Inorganic N
nitrate_N_kg_ha: float                 # Plant-available, mobile
ammonium_N_kg_ha: float                # Less mobile

# Organic N
active_N_kg_ha: float                  # Fast cycling (1-5 years)
slow_N_kg_ha: float                    # Slow cycling (20-50 years)
passive_N_kg_ha: float                 # Very slow (100+ years)
```

#### Mineralization

**File**: `soil/nitrogen_cycling/mineralization_decomp.py`

**Net Mineralization**:
```python
# From decomposition
gross_mineralization = (
    organic_N_pool *
    decomposition_rate *
    temperature_factor *
    moisture_factor
)

# C:N ratio effect
if residue_C_N_ratio > 30:
    # Immobilization (microbes consume N)
    net_mineralization = negative
elif residue_C_N_ratio < 20:
    # Mineralization (N released)
    net_mineralization = positive

# Temperature factor (Q10 = 2)
temp_factor = Q10 ** ((T - 20) / 10)

# Moisture factor (optimum at field capacity)
moisture_factor = (
    (water_content - wilting_point) /
    (field_capacity - wilting_point)
)
```

#### Nitrification

**File**: `soil/nitrogen_cycling/nitrification_volatilization.py`

**NH4+ → NO3-**:
```python
nitrification_rate = (
    ammonium_N *
    0.10 *  # 10% per day at optimum
    temperature_factor *
    pH_factor *
    moisture_factor
)

# pH effect (optimum pH 7-8)
pH_factor = exp(-((pH - 7.5) ** 2) / 2)

# Volatilization (NH3 loss)
if pH > 7.5:
    volatilization_fraction = 0.05 + 0.10 * (pH - 7.5)
    NH3_loss = ammonium_N * volatilization_fraction
```

#### Denitrification

**File**: `soil/nitrogen_cycling/denitrification.py`

**NO3- → N2O + N2**:
```python
# Occurs in anaerobic conditions
if water_filled_pore_space > 0.60:
    denitrification_rate = (
        nitrate_N *
        available_carbon *
        (1 - oxygen_factor) *
        temperature_factor
    )

    # N2O:N2 ratio (depends on NO3- and C)
    N2O_fraction = 0.02  # 2% typical
    N2O_emissions = denitrification_rate * N2O_fraction
```

#### Leaching

**File**: `soil/nitrogen_cycling/leaching_runoff_erosion.py`

**NO3- Leaching**:
```python
# Nitrate moves with water
leached_N = (
    nitrate_N_concentration_ppm *
    percolation_mm /
    10  # Convert to kg/ha
)

# Concentration in drainage water
NO3_concentration = (
    nitrate_N_kg_ha /
    (soil_water_content_mm * 0.1)
)
```

### Phosphorus Cycling

**File**: `soil/phosphorus_cycling/phosphorus_cycling.py`

**P Pools**:
```python
# Inorganic P
soluble_P_kg_ha: float                 # Immediately available
labile_P_kg_ha: float                  # Adsorbed, reversible
bound_P_kg_ha: float                   # Strongly bound

# Organic P
active_P_kg_ha: float                  # Microbial biomass
stable_P_kg_ha: float                  # Humus-bound
```

**P Transformations**:
```python
# Mineralization
organic_P_mineralization = organic_P * 0.02  # 2% per year

# Adsorption-desorption (Langmuir isotherm)
adsorbed_P = (K_ads * max_P * solution_P) / (1 + K_ads * solution_P)

# Precipitation (forms with Ca, Fe, Al)
if soil_pH > 7.0:
    # Calcium phosphate
    precipitated_P = soluble_P * 0.05
elif soil_pH < 5.5:
    # Iron/aluminum phosphate
    precipitated_P = soluble_P * 0.10
```

### Carbon Cycling

**File**: `soil/carbon_cycling/carbon_cycle.py`

**C Pools**:
```python
# Plant residues
structural_C_kg_ha: float              # Cellulose, lignin
metabolic_C_kg_ha: float               # Sugars, proteins

# Soil organic matter (CENTURY model)
active_C_kg_ha: float                  # Fast pool (1-5 years)
slow_C_kg_ha: float                    # Medium (20-50 years)
passive_C_kg_ha: float                 # Slow (100-1000 years)
```

#### Decomposition

**File**: `soil/carbon_cycling/decomposition.py`

**Decomposition Rates**:
```python
# Residue decomposition
structural_decomp_rate = 0.01 * (1 - lignin_fraction)
metabolic_decomp_rate = 0.05

# SOM decomposition
active_SOM_decomp = active_C * 0.014  # 50-year half-life
slow_SOM_decomp = slow_C * 0.0007     # 1000-year half-life

# CO2 respiration (30-60% of decomposed C)
CO2_emissions = decomposed_C * 0.45

# Microbial efficiency (40-70% incorporated)
microbial_C_gain = decomposed_C * 0.55
```

---

## Field Management

### Tillage Operations

**File**: `field/tillage_application.py`

**Tillage Types**:
```python
class TillageType(Enum):
    PLOW = "moldboard_plow"            # Deep inversion
    CHISEL = "chisel_plow"             # Medium depth
    DISK = "disk_harrow"               # Shallow mixing
    CULTIVATOR = "field_cultivator"    # Surface disturbance
    NO_TILL = "no_till"                # No soil disturbance
```

**Tillage Effects**:
```python
# Residue incorporation
if tillage_type == PLOW:
    residue_incorporated = 0.95       # 95% buried
    mixing_depth_cm = 20
elif tillage_type == DISK:
    residue_incorporated = 0.70
    mixing_depth_cm = 10

# SOM decomposition increase (Tillage effect)
decomposition_rate *= 1.5             # 50% increase for 30 days

# Soil compaction
bulk_density += 0.05 * passes         # Increases with traffic
```

### Fertilizer Application

**File**: `field/fertilizer_application.py`

**Fertilizer Types**:
```python
# Nitrogen fertilizers
urea_N_fraction = 0.46                # 46-0-0
UAN_N_fraction = 0.32                 # 32% N solution
anhydrous_ammonia = 0.82              # 82% N

# Phosphorus fertilizers
DAP_N = 0.18, DAP_P2O5 = 0.46        # 18-46-0
MAP_N = 0.11, MAP_P2O5 = 0.52        # 11-52-0

# Potassium fertilizers
potash_K2O = 0.60                     # 0-0-60
```

**Application Methods**:
```python
# Broadcast
efficiency_N = 0.70                   # 30% loss to volatilization

# Incorporated
efficiency_N = 0.85                   # 15% loss

# Injected
efficiency_N = 0.95                   # 5% loss

# Split application
# Apply 30% at planting, 70% at side-dress
# Improves efficiency by 10-15%
```

### Manure Application

**File**: `field/manure_application.py`

**Application Timing**:
```python
# Fall application
mineralization_first_year = 0.20      # 20% N available
carryover_year2 = 0.10
carryover_year3 = 0.05

# Spring application
mineralization_first_year = 0.30      # 30% N available
carryover_year2 = 0.10

# In-season (side-dress)
mineralization_first_year = 0.40      # 40% N available
```

---

## Harvest Operations

### Harvest Triggers

**File**: `crop/harvest_operations.py`

**Trigger Types**:

1. **Calendar Date**
```python
if current_date >= scheduled_harvest_date:
    execute_harvest()
```

2. **Growing Degree Days**
```python
if accumulated_GDD >= target_GDD:
    execute_harvest()
```

3. **Moisture Content**
```python
# Corn grain
if grain_moisture_pct <= 25:
    execute_harvest()

# Corn silage
if whole_plant_moisture_pct == 65:  # 35% DM
    execute_harvest()
```

4. **Plant Stage**
```python
# Alfalfa (multiple cuts)
if growth_stage == "10%_bloom":
    execute_harvest()
```

### Yield Calculation

```python
# Harvested biomass
harvestable_biomass_kg_ha = (
    total_above_ground_biomass *
    harvest_index *
    harvest_efficiency
)

# Harvest index (grain:total biomass)
# - Corn grain: 0.50
# - Wheat: 0.45
# - Soybean: 0.40

# Harvest efficiency
# - Corn grain: 0.98
# - Corn silage: 0.95
# - Alfalfa hay: 0.85 (field losses)

# Adjust for moisture
DM_yield_kg_ha = (
    harvestable_biomass_kg_ha *
    (1 - moisture_fraction)
)
```

---

## Environmental Impacts

### Soil Erosion

**File**: `soil/soil_erosion.py`

**USLE (Universal Soil Loss Equation)**:
```python
soil_loss_tonnes_ha_yr = R * K * LS * C * P

# R = Rainfall erosivity factor
# K = Soil erodibility factor (0.05-0.45)
# LS = Slope length-steepness factor
# C = Cover management factor (0.001-1.0)
# P = Support practice factor (0.2-1.0)
```

**C Factor by Management**:
```python
# No-till corn: 0.05
# Conventional corn: 0.35
# Alfalfa: 0.01
# Fallow: 1.00
```

### Runoff and Leaching

**Water Quality Impacts**:
```python
# Nitrate leaching risk
if NO3_N_ppm > 10:  # Drinking water standard
    risk = "HIGH"

# Phosphorus runoff (soil test P)
if Olsen_P_ppm > 50:
    risk = "HIGH"

# Sediment delivery
sediment_delivered = soil_loss * delivery_ratio
# delivery_ratio = 0.1-0.5 depending on distance to water
```

---

## Crop Configurations

### Supported Crops

**File**: `crop/crop_data_factory.py`

#### Corn (Zea mays)

```python
CropConfiguration(
    name="corn_silage",
    category=CropCategory.CORN,
    base_temp_C=10,
    GDD_to_maturity=1300,
    max_LAI=6.0,
    max_root_depth_cm=180,
    RUE_g_MJ=3.2,
    N_concentration_pct=1.5,
    rufas_ids=["corn_silage_whole_plant"]
)
```

#### Alfalfa (Medicago sativa)

```python
CropConfiguration(
    name="alfalfa",
    category=CropCategory.ALFALFA,
    base_temp_C=5,
    GDD_per_cutting=500,
    max_LAI=5.5,
    max_root_depth_cm=250,
    RUE_g_MJ=2.8,
    N_concentration_pct=3.5,
    N_fixation_pct=0.70,  # 70% from atmosphere
    rufas_ids=["alfalfa_hay_mature", "alfalfa_silage"]
)
```

#### Grass (Mixed cool-season)

```python
CropConfiguration(
    name="grass_hay",
    category=CropCategory.GRASS,
    base_temp_C=0,
    GDD_per_cutting=600,
    max_LAI=4.5,
    max_root_depth_cm=90,
    RUE_g_MJ=2.5,
    N_concentration_pct=2.5,
    rufas_ids=["grass_hay_mature", "grass_silage"]
)
```

---

## Performance Metrics

### Crop Yields

**Typical Ranges** (tonnes DM/ha):
- Corn silage: 15-25
- Corn grain: 10-15
- Alfalfa (4 cuts): 8-15
- Grass hay (3 cuts): 6-12
- Soybeans: 3-5
- Wheat: 4-8

### Nutrient Removal

**Per Tonne DM Harvested**:
- Corn silage: 15 kg N, 3 kg P, 12 kg K
- Alfalfa: 40 kg N, 4 kg P, 30 kg K
- Grass: 25 kg N, 4 kg P, 25 kg K

### Soil Health Indicators

```python
# Organic matter target: 3-5%
# pH range: 6.0-7.0 (optimal for most crops)
# Soil test P (Olsen): 20-40 ppm
# Soil test K: 150-250 ppm
# Bulk density: <1.4 g/cm³ (cropland)
```

---

*For implementation details, see source code in `RUFAS/routines/field/` and related submodules.*
