# Animal Module Reference

Comprehensive reference for RuFaS animal modeling components.

---

## Overview

The Animal Module simulates dairy cattle herd dynamics including:
- Individual animal tracking
- Milk production
- Growth and body weight
- Reproduction and breeding
- Health status
- Nutrition and feeding
- Manure production
- Enteric methane emissions

**Location**: `RUFAS/biophysical/animal/`

---

## Core Classes

### HerdManager

**File**: `herd_manager.py`

**Purpose**: Orchestrates all herd-level operations.

**Key Attributes**:
```python
cows: list[Animal]                     # Lactating and dry cows
heiferIIs: list[Animal]                # Bred heifers (post-breeding)
heiferIs: list[Animal]                 # Young heifers (pre-breeding)
calves: list[Animal]                   # Calves (birth to weaning)
bulls: list[Animal]                    # Breeding bulls (if applicable)
herd_statistics: HerdStatistics        # Population metrics
herd_reproduction_statistics: dict     # Breeding performance
```

**Key Methods**:
```python
daily_update_routine(time: RufasTime) -> dict
    """Execute all daily animal routines."""

collect_daily_feed_request() -> dict[str, float]
    """Aggregate feed needs from all animals."""

process_calvings(time: RufasTime) -> None
    """Handle calving events and newborn calves."""

process_culling() -> None
    """Remove animals based on culling criteria."""

update_all_max_daily_feeds(...) -> dict
    """Recalculate maximum feed intake capacities."""
```

### Animal

**File**: `animal.py`

**Purpose**: Represents individual animal with all traits and state.

**Key Attributes**:
```python
animal_id: int                         # Unique identifier
birth_date: date                       # Date of birth
breed: Breed                           # Genetics (Holstein, Jersey, etc.)
sex: Sex                               # Male/Female
body_weight_kg: float                  # Current weight
age_days: int                          # Age in days
lactation_number: int                  # Parity (0 = heifer)
days_in_milk: int                      # Days since calving (if lactating)
milk_yield_kg_per_day: float           # Current milk production
is_pregnant: bool                      # Pregnancy status
health_status: HealthStatus            # Health state
pen_assignment: Pen                    # Current housing location
```

**Key Methods**:
```python
calculate_daily_milk_yield() -> float
    """Calculate milk production using lactation curve."""

calculate_body_weight_change() -> float
    """Calculate growth or weight loss."""

calculate_feed_intake() -> float
    """Calculate dry matter intake capacity."""

calculate_nutrient_requirements() -> dict
    """Calculate NASEM nutrient needs."""

calculate_manure_production() -> ManureOutput
    """Calculate fecal and urinary excretion."""

calculate_enteric_methane() -> float
    """Calculate CH4 from rumen fermentation."""

update_reproductive_status(time: RufasTime) -> None
    """Update breeding, pregnancy, calving."""
```

### Pen

**File**: `pen.py`

**Purpose**: Groups animals with similar management.

**Pen Types**:
- `lactating_cows` - High-producing cows
- `dry_cows` - Non-lactating cows
- `fresh_cows` - Recently calved (0-21 DIM)
- `heifer_II` - Bred heifers
- `heifer_I` - Young heifers
- `calves` - Pre-weaned calves

**Key Attributes**:
```python
pen_name: str
animals: list[Animal]
ration: Ration                         # Assigned feed mix
max_capacity: int                      # Space limit
bedding_type: BeddingType
feeding_system: FeedingSystem
```

---

## Submodules

### Milk Production

**Location**: `RUFAS/biophysical/animal/milk/`

#### Lactation Curves

**Supported Models**:

1. **Wood's Curve** (Default)
```python
milk(t) = a * t^b * exp(-c * t)

# Parameters:
# a: scale (initial production)
# b: inclining slope (rate of increase)
# c: declining slope (rate of decrease)
# t: days in milk
```

**Typical Parameters**:
- High-producing Holstein: a=25, b=0.15, c=0.0025
- Jersey: a=20, b=0.18, c=0.003

2. **Dijkstra Curve** (Optional)
```python
milk(t) = a * (1 - exp(-b * t)) * exp(-c * t)
```

3. **Wilmink Curve** (Optional)
```python
milk(t) = a + b * t + c * exp(-0.05 * t)
```

#### Milk Components

**File**: `milk_composition.py`

**Calculated Components**:
- Fat percentage
- Protein percentage
- Lactose percentage
- Somatic cell count (SCC)
- Milk urea nitrogen (MUN)

**Influencing Factors**:
- Genetics
- Days in milk
- Diet composition (NDF, starch, fat)
- Energy balance

---

### Growth

**Location**: `RUFAS/biophysical/animal/growth/`

#### Body Weight Models

**File**: `growth_models.py`

**Calf Growth** (0-2 months):
```python
# Linear growth based on milk/starter intake
ADG_kg = 0.5 + 0.12 * milk_intake_kg + 0.25 * starter_intake_kg
```

**Heifer Growth** (2-24 months):
```python
# Exponential to mature weight
BW(t) = MW * (1 - exp(-k * age_months))

# MW: mature weight (650 kg Holstein)
# k: growth rate (0.06 typical)
```

**Cow Weight Dynamics**:
- **Lactation**: Mobilize body reserves (lose 0.5-1.5 kg/day early lactation)
- **Dry period**: Regain condition (gain 0.3-0.7 kg/day)

**Body Condition Score (BCS)**:
```python
BCS = 1 + 4 * (current_weight / target_weight)

# Scale: 1 (emaciated) to 5 (obese)
# Target: 3.0-3.5 at calving, 2.5-3.0 mid-lactation
```

---

### Reproduction

**Location**: `RUFAS/biophysical/animal/reproduction/`

#### Breeding Strategies

**File**: `breeding_manager.py`

**Strategies**:
1. **Year-Round Breeding**
   - Breed cows as eligible (60+ days in milk)
   - Continuous calving distribution

2. **Seasonal Breeding**
   - Breeding window (e.g., April-June)
   - Synchronized calvings (Jan-Mar)

3. **Split-Herd**
   - Half herd spring calving
   - Half herd fall calving

**Breeding Eligibility**:
```python
def is_eligible_for_breeding(animal: Animal) -> bool:
    return (
        animal.days_in_milk >= voluntary_waiting_period  # 60 days typical
        and not animal.is_pregnant
        and animal.health_status == HealthStatus.HEALTHY
        and animal.body_condition_score >= 2.5
    )
```

**Conception Rate Factors**:
```python
conception_rate = base_rate * (
    parity_factor *           # Lower for heifers and old cows
    heat_stress_factor *      # Reduced in summer (THI > 72)
    bcs_factor *              # Reduced if BCS < 2.5 or > 4.0
    breeding_number_factor    # Decreases after 3+ attempts
)

# Typical base rates:
# - Heifers: 55-65%
# - Cows (1st service): 40-50%
# - Cows (2nd service): 35-45%
```

#### Calving

**File**: `calving.py`

**Calving Process**:
1. Gestation length: 280 days (range: 270-290)
2. Calf birth weight:
   - Female calf: 40-45 kg
   - Male calf: 45-50 kg
3. Calving difficulty:
   - Easy: 85%
   - Moderate: 12%
   - Difficult: 3%
4. Calf mortality:
   - Stillbirth: 3-5%
   - Pre-weaning: 5-8%

**Transition Cow Management**:
```python
# Dry period: 60 days before calving
# Close-up period: 21 days before calving
# Fresh period: 21 days after calving

dry_off_date = expected_calving_date - timedelta(days=60)
close_up_date = expected_calving_date - timedelta(days=21)
```

---

### Nutrition

**Location**: `RUFAS/biophysical/animal/nutrients/`

#### NASEM Requirements

**File**: `nasem_requirements.py`

**Net Energy Requirements** (Mcal/day):
```python
NE_maintenance = 0.08 * body_weight_kg^0.75

NE_lactation = milk_kg * (0.0929 * fat_pct + 0.0563 * protein_pct + 0.0395)

NE_pregnancy = 0  # negligible until month 7
# Month 8: 1.5 Mcal/day
# Month 9: 2.5 Mcal/day

NE_growth = ADG_kg * (4.92 - 0.05 * body_weight_kg) / 0.69

Total_NE = NE_m + NE_l + NE_p + NE_g
```

**Protein Requirements** (g/day):
```python
MP_maintenance = 4.0 * body_weight_kg^0.75

MP_lactation = milk_kg * (protein_pct * 10)  # g protein per kg milk

MP_pregnancy = 0  # negligible until month 7
# Month 8: 200 g/day
# Month 9: 350 g/day

MP_growth = ADG_kg * (268 - 0.25 * body_weight_kg)

Total_MP = MP_m + MP_l + MP_p + MP_g
```

#### Feed Intake Prediction

**File**: `feed_intake.py`

**Dry Matter Intake** (kg/day):
```python
DMI = (0.372 * fat_corrected_milk_kg + 0.0968 * body_weight_kg^0.75) * (
    1 - exp(-0.192 * (weeks_of_lactation + 3.67))
)

# Adjustments:
DMI *= temperature_factor      # Reduced in heat stress
DMI *= diet_quality_factor     # Reduced if low palatability
DMI *= health_factor           # Reduced if sick
DMI *= social_factor           # Reduced if overcrowded
```

**Fill Constraints**:
```python
# Physical fill limits based on NDF
max_NDF_intake_pct_bw = 1.2  # % of body weight

if diet_ndf_pct * DMI > body_weight_kg * 1.2:
    DMI = (body_weight_kg * 1.2) / (diet_ndf_pct / 100)
```

---

### Digestive System

**Location**: `RUFAS/biophysical/animal/digestive_system/`

#### Enteric Methane

**File**: `enteric_methane.py`

**Emission Models**:

1. **IPCC Tier 2** (Default)
```python
CH4_MJ_per_day = gross_energy_intake_MJ * 0.065  # 6.5% of GE

CH4_kg_per_day = (CH4_MJ_per_day / 55.65) * (16/1000)
# 55.65 MJ/kg CH4 energy content
# 16 g/mol molecular weight
```

2. **NASEM Model** (Advanced)
```python
CH4_g_per_day = 0.05 * DMI_kg * 1000 * (
    0.45 * NDF_pct -
    0.275 * starch_pct -
    0.36 * fat_pct +
    2.9
)
```

**Mitigation Strategies**:
- High-starch diets (-15% CH4)
- Fat supplementation (-20% CH4, max 6% of diet)
- Feed additives (3-NOP: -30%, nitrates: -20%)

#### Rumen Fermentation

**File**: `rumen_model.py`

**VFA Production**:
```python
# Volatile Fatty Acids (mol/day)
acetate = 0.60 * fermentable_carbs_mol
propionate = 0.25 * fermentable_carbs_mol
butyrate = 0.15 * fermentable_carbs_mol

# Acetate/Propionate ratio affects milk fat
# Low A:P (<2.0) → milk fat depression
# High A:P (>4.0) → ketosis risk
```

---

### Health

**Location**: `RUFAS/biophysical/animal/animal_health/`

#### Disease Models

**File**: `disease_incidence.py`

**Common Diseases**:

1. **Mastitis**
   - Incidence: 25-40% clinical cases/year
   - Risk factors: High SCC, poor hygiene, overcrowding
   - Impact: -5 to -15% milk yield, higher culling

2. **Lameness**
   - Incidence: 20-30% cases/year
   - Risk factors: Concrete floors, standing time, nutrition
   - Impact: -5% milk, reduced fertility, higher culling

3. **Metabolic Disorders**
   - Ketosis: 15-30% (early lactation)
   - Milk fever: 3-8% (around calving)
   - Displaced abomasum: 2-5% (early lactation)

**Health Status Tracking**:
```python
class HealthStatus(Enum):
    HEALTHY = "healthy"
    SUBCLINICAL_ILLNESS = "subclinical"  # No visible signs
    CLINICAL_ILLNESS = "clinical"         # Visible symptoms
    RECOVERING = "recovering"
    CHRONIC = "chronic"                   # Long-term issues
```

---

### Manure Excretion

**Location**: `RUFAS/biophysical/animal/digestive_system/`

#### Fecal Output

**File**: `manure_excretion.py`

**Fecal Dry Matter** (kg/day):
```python
fecal_DM = DMI_kg * (1 - diet_digestibility)

# Typical digestibilities:
# High-quality TMR: 65-70%
# Moderate TMR: 60-65%
# Low-quality forage: 50-60%
```

**Fecal Nutrients**:
```python
# Nitrogen
fecal_N_g = (total_N_intake_g - absorbed_N_g)
fecal_N_g = protein_intake_g * 0.16 * (1 - digestibility)

# Phosphorus
fecal_P_g = P_intake_g * (1 - 0.35)  # 35% absorbed

# Carbon
fecal_C_g = (DMI_kg - absorbed_nutrients_kg) * 0.45  # 45% C in OM
```

#### Urine Output

**Urine Volume** (L/day):
```python
urine_L = 0.8 + 1.5 * milk_kg + 0.01 * body_weight_kg

# Increased by:
# - High protein diet (+20%)
# - High water intake (+30%)
# - Heat stress (+40%)
```

**Urinary Nitrogen**:
```python
# Excess protein → urinary N
urinary_N_g = max(0, protein_intake_g * 0.16 - protein_requirements_g * 1.1)

# Forms:
# - Urea: 70-85%
# - Hippuric acid: 10-20%
# - Creatinine: 5-10%
```

---

## Ration Formulation

**Location**: `RUFAS/biophysical/animal/ration/`

### Ration Optimizer

**File**: `ration_optimizer.py`

**Objective**: Minimize cost while meeting nutritional constraints.

**Linear Programming Formulation**:
```python
# Minimize:
cost = Σ (feed_i_cost * feed_i_amount)

# Subject to:
# Energy constraint
Σ (feed_i_NE * feed_i_amount) >= NE_requirement

# Protein constraint
Σ (feed_i_MP * feed_i_amount) >= MP_requirement

# Fiber constraints
min_NDF <= Σ (feed_i_NDF * feed_i_amount) / DMI <= max_NDF

# Non-fiber carb constraints
min_NFC <= Σ (feed_i_NFC * feed_i_amount) / DMI <= max_NFC

# Physical fill
Σ (feed_i_amount) <= max_DMI

# Feed limits
min_inclusion_i <= feed_i_amount <= max_inclusion_i
```

**Solver**: Uses SciPy's linprog (simplex method).

### Ration Balancing

**File**: `ration_balancer.py`

**Nutrient Balancing**:
```python
# Ensure minerals and vitamins meet NRC requirements
Ca_req = 0.0043 * milk_kg + 0.031  # % of diet DM
P_req = 0.0030 * milk_kg + 0.016   # % of diet DM
Mg_req = 0.20                       # % of diet DM
K_req = 1.00                        # % of diet DM

# Vitamins (IU/kg DM)
vitamin_A = 5000
vitamin_D = 1000
vitamin_E = 20
```

---

## Genetics

**Location**: `RUFAS/biophysical/animal/animal_genetics/`

### Genetic Parameters

**File**: `genetic_traits.py`

**Heritable Traits**:
```python
# Heritability (h²) values
milk_yield_h2 = 0.30
fat_pct_h2 = 0.50
protein_pct_h2 = 0.50
somatic_cell_score_h2 = 0.15
fertility_h2 = 0.05
longevity_h2 = 0.10
```

**Breeding Values**:
```python
# Estimated Breeding Value (EBV)
EBV_milk = parent_avg_EBV + mendelian_sampling

# Predicted Transmitting Ability (PTA)
PTA_milk = EBV_milk / 2
```

### Breed Characteristics

**File**: `breeds.py`

**Breed Comparison**:

| Breed | Mature Weight (kg) | Milk (kg/day) | Fat % | Protein % | Feed Efficiency |
|-------|-------------------|---------------|-------|-----------|----------------|
| Holstein | 650 | 35-40 | 3.6 | 3.0 | Medium |
| Jersey | 450 | 25-30 | 4.8 | 3.8 | High |
| Brown Swiss | 600 | 30-35 | 4.0 | 3.4 | Medium |
| Crossbred | 550 | 30-35 | 4.2 | 3.3 | High |

---

## Bedding

**Location**: `RUFAS/biophysical/animal/bedding/`

### Bedding Types

**File**: `bedding_materials.py`

**Material Properties**:

1. **Sand**
   - Absorption: Low
   - Comfort: High
   - Organic matter: Low (<5%)
   - Bacterial growth: Very low
   - Cost: Medium-High

2. **Sawdust**
   - Absorption: Medium
   - Comfort: Medium
   - Organic matter: High (>90%)
   - Bacterial growth: Medium
   - Cost: Low-Medium

3. **Straw**
   - Absorption: Medium
   - Comfort: Medium
   - Organic matter: High (>95%)
   - Bacterial growth: High
   - Cost: Low

4. **Recycled Manure Solids (RMS)**
   - Absorption: High
   - Comfort: Medium
   - Organic matter: Medium (40-60%)
   - Bacterial growth: Medium
   - Cost: Very Low

**Bedding Usage** (kg/cow/day):
```python
freestall_sand = 1.5
freestall_sawdust = 2.5
freestall_rms = 3.0
bedded_pack = 5.0
```

---

## Performance Metrics

### Herd-Level KPIs

**Productivity**:
- Rolling herd average (RHA) milk: 10,000-12,000 kg/cow/year
- Milk/cow/day: 30-35 kg
- Peak milk: 40-50 kg
- Persistency: 80-90% (milk at 280 DIM / peak milk)

**Reproduction**:
- Calving interval: 12-13 months (optimal)
- Days to first service: 60-80 days
- Conception rate (1st service): 40-50%
- Pregnancy rate (21-day): 18-22%
- Cull rate: 30-35%/year

**Health**:
- Clinical mastitis: <30 cases/100 cows/year
- Lameness: <20 cases/100 cows/year
- Metabolic disorders: <10 cases/100 cows/year
- Mortality: <5%/year

**Efficiency**:
- Feed efficiency (milk/DMI): 1.3-1.6
- Income over feed cost (IOFC): $8-12/cow/day
- Milk urea nitrogen: 10-14 mg/dL

---

*For implementation details, see source code in `RUFAS/biophysical/animal/` and `RUFAS/routines/animal/`.*
