# Manure Module Reference

Comprehensive reference for RuFaS manure management modeling.

---

## Overview

The Manure Module simulates:
- Manure collection from animal housing
- Manure treatment and separation
- Storage systems (lagoons, tanks, composting)
- Nutrient transformations
- Greenhouse gas emissions
- Land application

**Location**: `RUFAS/biophysical/manure/`

---

## Core Classes

### ManureManager

**File**: `manure_manager.py`

**Purpose**: Orchestrates all manure pathways from collection to application.

**Key Components**:
```python
handlers: list[ManureHandler]          # Collection systems
separators: list[ManureSeparator]      # Solid-liquid separation
storages: list[ManureStorage]          # Storage facilities
treatments: list[ManureTreatment]      # Advanced treatments
```

**Key Methods**:
```python
process_daily_manure(manure: ManureProduction, time: RufasTime) -> None
    """Route daily manure through management system."""

calculate_daily_emissions() -> EmissionResults
    """Calculate CH4, N2O, NH3 emissions."""

apply_manure_to_fields(application_event: ManureApplication) -> None
    """Transfer manure nutrients to crop fields."""

update_storage_levels(time: RufasTime) -> None
    """Track storage capacity and decomposition."""
```

---

## Manure Collection

### Handler Types

**Location**: `RUFAS/biophysical/manure/handler/`

#### 1. Flush System

**File**: `flush_handler.py`

**Configuration**:
```python
{
  "type": "flush_system",
  "flush_volume_liters_per_cow_per_day": 100,
  "flush_frequency_per_day": 4,
  "water_source": "recycled",  # or "fresh"
  "collection_efficiency": 0.85
}
```

**Characteristics**:
- High water usage (80-150 L/cow/day)
- Dilutes manure (2-4% solids)
- Good for sloped barns
- Requires lagoon or separator

**Mass Balance**:
```python
total_volume_L = flush_water_L + manure_volume_L
total_solids_pct = (fecal_DM_kg + urine_solids_kg) / total_volume_L * 100
```

#### 2. Scraper System

**File**: `scraper_handler.py`

**Configuration**:
```python
{
  "type": "mechanical_scraper",
  "frequency_per_day": 6,
  "alley_length_m": 100,
  "collection_efficiency": 0.75
}
```

**Characteristics**:
- Low water usage (<10 L/cow/day)
- Thicker manure (8-12% solids)
- Good for flat barns
- Can route to slurry tank or separator

#### 3. Vacuum System

**File**: `vacuum_handler.py`

**Configuration**:
```python
{
  "type": "vacuum_system",
  "vacuum_frequency_per_day": 2,
  "collection_efficiency": 0.90
}
```

**Characteristics**:
- Moderate water usage (30-50 L/cow/day)
- Medium consistency (5-8% solids)
- Excellent for robotic milking
- Low ammonia emissions from floors

#### 4. Bedded Pack

**File**: `bedded_pack_handler.py`

**Configuration**:
```python
{
  "type": "compost_bedded_pack",
  "bedding_addition_kg_per_cow_per_day": 5,
  "pack_depth_cm": 45,
  "tilling_frequency_per_week": 7,
  "composting_active": true
}
```

**Characteristics**:
- High bedding usage (4-7 kg/cow/day)
- Composting in-place (if managed correctly)
- Dry manure (30-40% solids)
- Lower ammonia but higher temperature

---

## Manure Treatment

### Separator Systems

**Location**: `RUFAS/biophysical/manure/separation/`

#### Mechanical Separator

**File**: `mechanical_separator.py`

**Types**:
1. **Screw Press**
   - Solids removal: 25-35%
   - Liquid solids: 3-5%
   - Solid solids: 25-35%
   - Cost: Medium

2. **Roller Press**
   - Solids removal: 30-40%
   - Liquid solids: 2-4%
   - Solid solids: 28-38%
   - Cost: Medium-High

3. **Centrifuge**
   - Solids removal: 40-60%
   - Liquid solids: 1-2%
   - Solid solids: 35-45%
   - Cost: High

**Mass Balance**:
```python
# Input manure: 1000 kg at 10% solids
solids_in = 100 kg
liquid_in = 900 kg

# Separator efficiency: 30% solids removal
solids_removed = 30 kg
solids_in_liquid = 70 kg

# Outputs:
solid_stream = 30 kg / 0.30 = 100 kg total (30% DM)
liquid_stream = 900 kg total (70/900 = 7.8% DM)
```

**Nutrient Partitioning**:
```python
# Phosphorus: 80-90% to solids
solid_stream_P = 0.85 * total_P
liquid_stream_P = 0.15 * total_P

# Nitrogen: 20-30% to solids
solid_stream_N = 0.25 * total_N
liquid_stream_N = 0.75 * total_N

# Carbon: 70-80% to solids
solid_stream_C = 0.75 * total_C
liquid_stream_C = 0.25 * total_C
```

---

## Storage Systems

### Anaerobic Lagoon

**Location**: `RUFAS/biophysical/manure/storage/`

**File**: `anaerobic_lagoon.py`

**Design Parameters**:
```python
{
  "capacity_cubic_meters": 2000,
  "depth_meters": 4,
  "covered": false,
  "loading_rate_kg_vs_per_m3_per_day": 0.05,
  "retention_time_days": 180
}
```

**Decomposition Model**:
```python
# Volatile Solids (VS) degradation
VS_degradation_rate = 0.6  # 60% in lagoon

# CH4 production
CH4_m3 = VS_degraded_kg * 0.35  # 0.35 m3 CH4/kg VS
CH4_kg = CH4_m3 * 0.717  # density at 20°C

# Temperature effect
if temp_C < 10:
    degradation_rate *= 0.3
elif temp_C < 20:
    degradation_rate *= 0.6
elif temp_C > 30:
    degradation_rate *= 1.2
```

**Emissions**:
```python
# Methane (no cover)
CH4_kg_per_day = VS_loading_kg * 0.6 * 0.35 * 0.717

# Ammonia volatilization
NH3_kg_per_day = TAN_kg * 0.15  # 15% of total ammonia nitrogen

# Nitrous oxide (minimal in anaerobic)
N2O_kg_per_day = total_N_kg * 0.005
```

### Slurry Tank

**File**: `slurry_tank.py`

**Design Parameters**:
```python
{
  "capacity_cubic_meters": 1500,
  "covered": true,
  "cover_type": "natural_crust",  # or "synthetic", "straw"
  "mixing_frequency_per_month": 2
}
```

**Emissions Reduction from Cover**:
```python
# Natural crust: 40-60% CH4 reduction
# Straw cover: 30-50% CH4 reduction
# Synthetic cover: 80-95% CH4 reduction

if cover_type == "synthetic":
    CH4_emissions *= 0.10  # 90% reduction
elif cover_type == "natural_crust":
    CH4_emissions *= 0.50  # 50% reduction
```

### Composting

**File**: `composting.py`

**Design Parameters**:
```python
{
  "type": "windrow_composting",
  "turning_frequency_days": 3,
  "bulking_agent": "sawdust",
  "bulking_agent_ratio": 0.3,  # 30% by weight
  "moisture_target_pct": 55
}
```

**Composting Phases**:

1. **Active Phase** (0-30 days)
   - Temperature: 55-75°C
   - Pathogen kill: >99.9%
   - C/N ratio: 25:1 → 20:1
   - Mass loss: 30-40%

2. **Curing Phase** (30-90 days)
   - Temperature: 35-45°C
   - Stabilization
   - C/N ratio: 20:1 → 15:1
   - Mass loss: 10-20%

**Emission Factors**:
```python
# CH4 (aerobic composting minimal)
CH4_kg = initial_C_kg * 0.01  # 1% of C

# N2O (significant)
N2O_kg = initial_N_kg * 0.02  # 2% of N

# NH3 (high without covers)
NH3_kg = TAN_kg * 0.25  # 25% without cover
NH3_kg = TAN_kg * 0.10  # 10% with cover
```

---

## Greenhouse Gas Emissions

### Methane (CH4)

**Location**: `RUFAS/biophysical/manure/emissions/`

**File**: `methane_emissions.py`

**Emission Factors by System**:

| System | MCF* | CH4 kg/kg VS |
|--------|------|--------------|
| Anaerobic lagoon | 0.70 | 0.17 |
| Slurry tank (no cover) | 0.17 | 0.04 |
| Slurry tank (covered) | 0.05 | 0.01 |
| Solid storage | 0.02 | 0.005 |
| Composting | 0.01 | 0.002 |
| Daily spread | 0.001 | 0.0002 |

*MCF = Methane Conversion Factor

**Calculation**:
```python
# IPCC Tier 2 method
CH4_kg = VS_excreted_kg * MCF * 0.67 * B0

# B0 = maximum methane production capacity (0.24 m3 CH4/kg VS)
# 0.67 = conversion factor (kg/m3)
```

### Nitrous Oxide (N2O)

**File**: `nitrous_oxide_emissions.py`

**Direct Emissions**:
```python
# From storage
N2O_direct_kg = total_N_kg * EF_storage

# Emission factors:
EF_lagoon = 0.000  # Anaerobic, no nitrification
EF_slurry = 0.002  # 0.2%
EF_solid = 0.005   # 0.5%
EF_compost = 0.020 # 2.0%
```

**Indirect Emissions**:
```python
# From NH3 and NOx volatilization
N2O_indirect_kg = (NH3_N_kg + NOx_N_kg) * 0.01  # 1% of volatilized N

# From leaching
N2O_leaching_kg = (TAN_kg * leach_fraction) * 0.0075  # 0.75% of leached N
```

### Ammonia (NH3)

**File**: `ammonia_emissions.py`

**Volatilization Factors**:

| System | % TAN Lost as NH3 |
|--------|-------------------|
| Flush (in-barn) | 5-10% |
| Scraper (in-barn) | 15-25% |
| Anaerobic lagoon | 20-40% |
| Slurry tank (uncovered) | 10-20% |
| Slurry tank (covered) | 2-5% |
| Composting (uncovered) | 25-50% |
| Composting (covered) | 10-20% |

**Calculation**:
```python
# Daily NH3 emissions
NH3_N_kg = TAN_kg * volatilization_factor

# Factors affecting volatilization:
# - Temperature: +3% per °C above 15°C
# - Wind speed: +2% per m/s
# - pH: Exponential above pH 7 (+10% per 0.5 pH unit)
# - Surface area: Linear with area/volume ratio
```

---

## Nutrient Transformations

### Nitrogen Cycle

**File**: `nitrogen_cycle.py`

**N Forms in Manure**:
```python
# Organic N (50-60% of total)
organic_N = fecal_N + undigested_protein_N

# Total Ammonia Nitrogen - TAN (40-50% of total)
TAN = urinary_N + mineralized_N

# Mineralization rate in storage
mineralization_rate = 0.02  # 2% of organic N per day (at 20°C)
daily_TAN_from_mineralization = organic_N * mineralization_rate
```

**N Losses**:
```python
# Volatilization (NH3)
NH3_loss = TAN * volatilization_factor

# Denitrification (N2 and N2O)
denitrification_loss = total_N * denitrification_factor

# Remaining plant-available N
PAN = TAN - NH3_loss + (organic_N * mineralization_factor)
```

### Phosphorus Dynamics

**File**: `phosphorus_cycle.py`

**P Conservation**:
```python
# Phosphorus is conserved (not volatile)
# All P excreted remains in manure

# But partitioning changes:
# - Soluble P (immediately plant-available): 20-40%
# - Bound P (requires mineralization): 60-80%

# In separation:
solid_P_fraction = 0.85  # 85% to solids
liquid_P_fraction = 0.15  # 15% to liquid
```

### Carbon Cycle

**File**: `carbon_cycle.py`

**C Forms**:
```python
# Volatile solids (organic C)
VS_C = fecal_organic_matter * 0.45  # 45% C in OM

# Decomposition pathways:
if storage_type == "anaerobic":
    # CH4 production
    C_to_CH4 = VS_C * 0.35 * MCF
    # CO2 production
    C_to_CO2 = VS_C * 0.30 * MCF
    # Remaining as stable C
    stable_C = VS_C * (1 - MCF)

elif storage_type == "aerobic":
    # Mostly CO2 (composting)
    C_to_CO2 = VS_C * 0.60
    # Stable humus
    stable_C = VS_C * 0.40
```

---

## Land Application

### Application Methods

**Location**: `RUFAS/biophysical/manure/application/`

#### Broadcast Spreading

**File**: `broadcast_application.py`

**Characteristics**:
- Low cost
- High NH3 losses (30-50% of TAN)
- Good for solid manure
- Surface application only

**Emission Factor**:
```python
NH3_loss_fraction = 0.40  # 40% of TAN

# Reduced by incorporation:
if incorporated_within_24h:
    NH3_loss_fraction = 0.15  # 15% of TAN
```

#### Injection

**File**: `injection_application.py`

**Characteristics**:
- Higher cost
- Low NH3 losses (5-10% of TAN)
- Best for liquid manure
- Subsurface placement (10-20 cm depth)

**Emission Factor**:
```python
NH3_loss_fraction = 0.07  # 7% of TAN
```

#### Irrigation

**File**: `irrigation_application.py`

**Types**:
1. **Traveling gun** - High NH3 losses (40-50%)
2. **Center pivot** - Medium losses (20-30%)
3. **Drip irrigation** - Low losses (5-10%)

**Application Rate Limits**:
```python
# Nutrient-based limits
max_N_rate_kg_per_ha = crop_N_requirement * 1.2
max_P_rate_kg_per_ha = crop_P_requirement * 1.5

# Hydraulic loading limit
max_application_rate_mm = soil_infiltration_rate * safety_factor
```

---

## Nutrient Credits

### Plant-Available Nutrients

**File**: `nutrient_availability.py`

**Nitrogen Availability**:
```python
# First year availability
N_available_year1 = (
    TAN * (1 - NH3_loss_fraction) +  # Immediately available
    organic_N * 0.25  # 25% of organic N mineralizes in year 1
)

# Subsequent years (residual organic N)
N_available_year2 = organic_N * 0.10
N_available_year3 = organic_N * 0.05
```

**Phosphorus Availability**:
```python
# All P considered available (conservative)
P_available = total_P

# Phytin P availability (needs mineralization)
phytin_P_available_year1 = phytin_P * 0.70
```

**Potassium Availability**:
```python
# All K immediately available (soluble)
K_available = total_K
```

### Fertilizer Replacement Value

```python
# Economic value of manure nutrients
N_value_per_kg = 1.00  # $/kg N
P_value_per_kg = 1.50  # $/kg P2O5
K_value_per_kg = 0.80  # $/kg K2O

total_value_per_tonne = (
    N_available_kg * N_value_per_kg +
    P_available_kg * 2.29 * P_value_per_kg +  # Convert P to P2O5
    K_available_kg * 1.20 * K_value_per_kg    # Convert K to K2O
)
```

---

## Performance Metrics

### Storage Capacity

**Design Guidelines**:
```python
# Minimum storage duration
months_storage = {
    "cold_climate": 6,   # 180 days (winter shutdown)
    "temperate": 4,      # 120 days (application windows)
    "warm": 3            # 90 days (year-round application)
}

# Capacity calculation
daily_production_m3 = cows * 0.06  # 60 L/cow/day
required_capacity_m3 = daily_production_m3 * months_storage * 30

# Safety factor
design_capacity = required_capacity_m3 * 1.25  # 25% extra
```

### Emission Targets

**GHG Reduction Goals**:
```python
# Baseline (uncovered lagoon): 100 kg CO2e/cow/year
# Targets:
covered_lagoon = 40  # 60% reduction
anaerobic_digester = 20  # 80% reduction
daily_spread = 10  # 90% reduction
```

**NH3 Reduction**:
```python
# Baseline (open lot): 50 kg NH3-N/cow/year
# Best practices:
flush_system = 35  # 30% reduction
covered_storage = 25  # 50% reduction
injection_application = 15  # 70% reduction
```

---

*For implementation details, see source code in `RUFAS/biophysical/manure/` and `RUFAS/routines/manure/`.*
