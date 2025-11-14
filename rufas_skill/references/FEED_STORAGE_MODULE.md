# Feed Storage Module Reference

Comprehensive reference for RuFaS feed storage and inventory management.

---

## Overview

The Feed Storage Module simulates:
- Feed inventory management
- Storage types (silage, hay, grain, baleage)
- Storage degradation and losses
- Nutritional composition changes
- Feed purchasing and planning
- Distribution to animals

**Location**: `RUFAS/biophysical/feed_storage/`

---

## Core Classes

### FeedManager

**File**: `feed_manager.py`

**Purpose**: Central management of all feed inventory and distribution.

**Key Attributes**:
```python
active_storages: dict[StorageType, Storage]      # Farm-grown feed storage
purchased_feed_storage: PurchasedFeedStorage     # Bought feeds
available_feeds: list[NASEMFeed | NRCFeed]       # Feed library
crop_to_rufas_id: dict[str, RUFAS_ID]            # Crop-to-feed mapping
planning_cycle_allowance: PlanningCycleAllowance # Purchase planning
runtime_purchase_allowance: RuntimePurchaseAllowance  # Emergency purchases
```

**Key Methods**:

#### Feed Reception
```python
def receive_crop(
    harvested_crop: HarvestedCrop,
    storage_type: StorageType,
    day: int
) -> None:
    """
    Receive harvested crop into appropriate storage.

    Parameters
    ----------
    harvested_crop : HarvestedCrop
        Crop with amount (kg DM), moisture, nutrients
    storage_type : StorageType
        Storage method (silage, hay, etc.)
    day : int
        Simulation day for tracking
    """
```

#### Feed Distribution
```python
def manage_daily_feed_request(
    requested_feed: dict[RUFAS_ID, float],
    time: RufasTime
) -> bool:
    """
    Fulfill daily feed request from inventory.

    Parameters
    ----------
    requested_feed : dict
        Feed amounts requested by animals (kg DM)
    time : RufasTime
        Current simulation time

    Returns
    -------
    bool
        True if all requests fulfilled, False if shortages
    """
```

#### Inventory Planning
```python
def get_total_projected_inventory(
    current_date: date,
    weather: Weather,
    time: RufasTime
) -> TotalInventory:
    """
    Project future feed availability for planning.

    Accounts for:
    - Current inventory
    - Expected harvests
    - Degradation losses
    - Planned purchases

    Returns
    -------
    TotalInventory
        Projected availability by feed type
    """
```

#### Feed Purchasing
```python
def manage_planning_cycle_purchases(
    ideal_feeds: IdealFeeds,
    time: RufasTime
) -> None:
    """
    Purchase feeds to meet projected shortages.

    Triggered during ration reformulation periods.
    """
```

---

## Storage Types

### Silage Storage

**File**: `silage.py`

**Purpose**: Fermented, high-moisture feed storage.

#### Storage Subclasses

**1. Bunker Silo**
```python
class Bunker(Silage):
    """
    Large horizontal silo, open face.

    Characteristics:
    - Capacity: 500-5000 tonnes
    - Density: 200-250 kg DM/m³
    - Face management critical
    - Aerobic spoilage risk at face
    """
```

**2. Pile**
```python
class Pile(Silage):
    """
    Ground pile, covered with plastic.

    Characteristics:
    - Capacity: 100-2000 tonnes
    - Density: 150-200 kg DM/m³
    - Higher losses than bunker (5-15%)
    - Lower cost
    """
```

**3. Bag**
```python
class Bag(Silage):
    """
    Plastic tube bags.

    Characteristics:
    - Capacity: 50-300 tonnes per bag
    - Density: 200-230 kg DM/m³
    - Low oxygen infiltration
    - Sequential feeding required
    """
```

#### Fermentation Process

**Phase 1: Aerobic Phase** (0-24 hours)
```python
# Oxygen consumption by plant respiration
O2_consumed_kg = initial_biomass_kg * 0.02  # 2% DM loss

# Temperature rise
temperature_C = ambient_temp + 5  # 5°C increase

# pH drop initiation
pH = 6.5  # Initial
```

**Phase 2: Anaerobic Fermentation** (1-21 days)
```python
# Lactic acid production
if moisture_pct in range(60, 70):  # Optimal
    lactic_acid_production = "HIGH"
    pH_final = 3.8  # Good preservation
elif moisture_pct < 60:
    lactic_acid_production = "LOW"
    pH_final = 4.5  # Marginal
elif moisture_pct > 70:
    lactic_acid_production = "MEDIUM"
    pH_final = 4.2
    # Risk of seepage loss

# Sugar consumption
water_soluble_carbs_initial = 0.20  # 20% of DM
water_soluble_carbs_final = 0.05    # 5% remaining

# Fermentation DM loss: 3-8%
fermentation_loss = initial_DM * 0.05
```

**Phase 3: Stable Storage** (21+ days)
```python
# Minimal changes if anaerobic
if oxygen_infiltration == False:
    daily_DM_loss = 0.001  # 0.1% per day

# Temperature stable
temperature_C = ambient_temp + 2
```

#### Feedout Degradation

**Aerobic Spoilage**:
```python
# When oxygen enters (face exposure)
spoilage_depth_cm = feedout_rate_cm_per_day

# Heating phase (24-72 hours)
if face_temp_C > ambient_temp + 5:
    aerobic_microbes_active = True
    DM_loss_per_day = 0.05  # 5% per day
    protein_degradation = True
    energy_loss = True

# Spoilage rate depends on:
# 1. Face advance rate (>10 cm/day target)
face_advance_rate = total_DM_removed_kg / (face_area_m2 * density_kg_m3)

if face_advance_rate < 0.10:  # <10 cm/day
    spoilage_loss_pct = 3.0
elif face_advance_rate < 0.15:
    spoilage_loss_pct = 1.5
else:
    spoilage_loss_pct = 0.5

# 2. Packing density
if packing_density < 180:
    spoilage_risk = "HIGH"
elif packing_density > 220:
    spoilage_risk = "LOW"

# 3. Temperature (summer > winter)
summer_spoilage_multiplier = 1.5
winter_spoilage_multiplier = 0.7
```

---

### Hay Storage

**File**: `hay.py`

**Purpose**: Dry forage storage (< 20% moisture).

#### Storage Subclasses

**1. Protected Indoors**
```python
class ProtectedIndoors(Hay):
    """
    Barn or covered storage.

    Characteristics:
    - Minimal losses (1-3%)
    - No weather exposure
    - High cost
    - Quality preservation excellent
    """
```

**2. Protected Wrapped**
```python
class ProtectedWrapped(Hay):
    """
    Individual bale wrapping (plastic).

    Characteristics:
    - Low losses (2-5%)
    - Weather protection
    - Medium-high cost
    - Good quality preservation
    """
```

**3. Protected Tarped**
```python
class ProtectedTarped(Hay):
    """
    Stack covered with tarp.

    Characteristics:
    - Moderate losses (5-10%)
    - Partial weather protection
    - Low-medium cost
    - Moderate quality preservation
    """
```

**4. Unprotected**
```python
class Unprotected(Hay):
    """
    Outdoor stack, uncovered.

    Characteristics:
    - High losses (10-30%)
    - Full weather exposure
    - Lowest cost
    - Quality degradation significant
    """
```

#### Hay Curing

**Field Drying**:
```python
# Moisture loss rate
if weather_condition == "sunny":
    drying_rate_pct_per_hr = 1.5  # Optimal
elif weather_condition == "partly_cloudy":
    drying_rate_pct_per_hr = 0.8
elif weather_condition == "cloudy":
    drying_rate_pct_per_hr = 0.3
elif weather_condition == "rain":
    drying_rate_pct_per_hr = -0.5  # Re-wetting

# Target moisture for baling
safe_moisture_pct = {
    "small_square_bales": 18,
    "large_square_bales": 16,
    "large_round_bales": 18
}

# Rain damage
if rain_on_cut_hay:
    # Sugar leaching
    sugar_loss_pct = 20
    # Protein loss
    protein_loss_pct = 10
    # Energy loss
    energy_loss_pct = 15
```

#### Storage Degradation

**Dry Matter Loss**:
```python
# Indoor storage
DM_loss_pct_per_year = 2

# Wrapped
DM_loss_pct_per_year = 4

# Tarped (bottom layer damage)
DM_loss_pct_per_year = 8

# Unprotected
if precipitation_annual_mm < 500:
    DM_loss_pct_per_year = 15  # Dry climate
elif precipitation_annual_mm < 1000:
    DM_loss_pct_per_year = 20  # Moderate
else:
    DM_loss_pct_per_year = 30  # Wet climate
```

**Quality Changes**:
```python
# Unprotected hay (weathering)
# Month 1-3
protein_pct *= 0.95  # 5% loss
energy_Mcal_kg *= 0.90  # 10% loss

# Month 4-6
protein_pct *= 0.85  # 15% loss total
energy_Mcal_kg *= 0.80  # 20% loss total

# Mold growth
if moisture_pct > 20:
    mold_risk = "HIGH"
    palatability *= 0.70
    health_risk = True
```

---

### Baleage

**File**: `baleage.py`

**Purpose**: Wrapped high-moisture bales (40-60% moisture).

```python
class Baleage(Storage):
    """
    Individually wrapped high-moisture hay.

    Characteristics:
    - Moisture: 40-60% (DM: 40-60%)
    - Fermentation: Limited (higher DM than silage)
    - pH: 4.5-5.5
    - Storage losses: 5-10%
    - Quality: Between hay and silage
    """
```

**Fermentation**:
```python
# Less intense than silage
if moisture_pct in range(45, 55):  # Optimal
    fermentation_quality = "GOOD"
    pH_final = 5.0
    DM_loss = 0.05  # 5%
elif moisture_pct < 45:
    fermentation_quality = "POOR"
    pH_final = 5.8
    heating_risk = "HIGH"
elif moisture_pct > 55:
    fermentation_quality = "MEDIUM"
    pH_final = 4.7
    seepage_risk = "HIGH"
```

**Wrap Integrity**:
```python
# Oxygen infiltration through holes
holes_per_bale = {
    "birds": 5,        # Bird damage
    "rodents": 2,      # Mice, rats
    "handling": 3      # Forklifts
}

# Each hole increases losses
DM_loss_per_hole_pct = 0.5
total_loss_pct = base_loss + (n_holes * DM_loss_per_hole_pct)
```

---

### Grain Storage

**File**: `grain.py`

**Purpose**: High-energy concentrate storage.

#### Storage Subclasses

**1. Dry Grain**
```python
class Dry(Grain):
    """
    Traditional dry grain storage (<14% moisture).

    Characteristics:
    - Moisture: 12-14%
    - Long-term storage (1+ years)
    - Minimal losses (<1% per year)
    - Insect/rodent management critical
    """
```

**2. High-Moisture Grain**
```python
class HighMoisture(Grain):
    """
    Anaerobic grain storage (20-30% moisture).

    Characteristics:
    - Moisture: 22-28%
    - Must be kept anaerobic
    - Higher energy value (no drying loss)
    - Storage losses: 3-5%
    - Feeding challenges (flow, mixing)
    """
```

#### Dry Grain Storage

**Drying**:
```python
# Artificial drying (energy cost)
drying_cost_per_pct_point = 0.02  # $/bu per % moisture

# From 25% to 14% moisture
initial_moisture = 0.25
target_moisture = 0.14
drying_needed = initial_moisture - target_moisture

# Energy for drying (propane)
propane_BTU_per_lb_water = 1800
propane_cost = drying_needed * propane_BTU_per_lb_water * propane_price

# Shrinkage (weight loss)
shrinkage_pct = (1 - (1 - target_moisture) / (1 - initial_moisture)) * 100
# 25% → 14% moisture: 13% weight loss
```

**Storage Degradation**:
```python
# Respiration losses (grain and microbes)
if moisture_pct < 14 and temp_C < 15:
    DM_loss_pct_per_year = 0.5  # Minimal
elif moisture_pct < 16 and temp_C < 25:
    DM_loss_pct_per_year = 1.0
else:
    DM_loss_pct_per_year = 3.0  # High risk

# Insect damage
if temp_C > 20 and moisture_pct > 13:
    insect_activity = "HIGH"
    additional_loss_pct = 2.0
```

#### High-Moisture Grain

**Ensiling Process**:
```python
# Similar to silage
fermentation_DM_loss = 0.03  # 3%

# Must exclude oxygen
if storage_type == "upright_silo":
    oxygen_exclusion = "EXCELLENT"
    spoilage_risk = "LOW"
elif storage_type == "bunker":
    oxygen_exclusion = "GOOD"
    spoilage_risk = "MEDIUM"
    face_management_critical = True
```

**Feedout**:
```python
# Aerobic stability poor
if exposed_to_air_hours > 24:
    heating = True
    DM_loss_per_day = 0.05
    palatability_reduction = 0.30
```

---

## Purchased Feed Storage

**File**: `purchased_feed_storage.py`

**Purpose**: Track commercially purchased feeds.

```python
class PurchasedFeedStorage:
    """
    Manages inventory of purchased feeds.

    Feeds:
    - Protein supplements (soybean meal, canola meal)
    - Energy supplements (corn gluten feed, distillers grains)
    - Minerals and vitamins
    - Specialty feeds (bypass protein, fat supplements)
    """
```

**Purchasing Decision**:
```python
# Cost comparison
on_farm_cost = (
    production_cost +
    storage_loss_cost +
    quality_degradation_cost
)

purchased_cost = (
    market_price +
    delivery_cost
)

if purchased_cost < on_farm_cost:
    decision = "BUY"
```

**Common Purchased Feeds**:
```python
PURCHASED_FEEDS = {
    "soybean_meal": {
        "CP_pct": 48,
        "cost_per_tonne": 450,
        "typical_inclusion": 0.05  # 5% of ration DM
    },
    "corn_gluten_feed": {
        "CP_pct": 22,
        "NDF_pct": 40,
        "cost_per_tonne": 200,
        "typical_inclusion": 0.10
    },
    "distillers_grains": {
        "CP_pct": 30,
        "fat_pct": 10,
        "cost_per_tonne": 250,
        "typical_inclusion": 0.15
    },
    "mineral_supplement": {
        "Ca_pct": 15,
        "P_pct": 8,
        "cost_per_tonne": 800,
        "typical_inclusion": 0.01
    }
}
```

---

## Feed Quality Changes

### Nutritional Degradation

**Protein**:
```python
# Heat damage (Maillard reaction)
if storage_temp_C > 50:
    # Lysine binding
    available_protein_fraction = 0.85  # 15% unavailable
    ADIN_pct_CP += 5  # Acid detergent insoluble N

# Oxidation (unprotected hay)
if UV_exposure_high:
    vitamin_A_IU_kg *= 0.50  # 50% loss in 3 months
    vitamin_E_IU_kg *= 0.70  # 30% loss
```

**Energy**:
```python
# Aerobic spoilage
if aerobic_microbes_active:
    # Sugar consumption
    sugar_loss = WSC_kg * 0.80  # 80% degraded
    # VFA production (less energy)
    VFA_energy_loss = sugar_loss * 0.30
    # Net energy reduction
    NE_Mcal_kg *= 0.85  # 15% reduction
```

**Fiber**:
```python
# Lignification (over-mature crop)
if days_past_optimal_harvest > 10:
    lignin_pct += 0.3  # per 10 days
    NDF_digestibility_pct -= 3  # per 10 days

# Example: Alfalfa
# Optimal (10% bloom): 38% NDF, 50% NDF digestibility
# Late (50% bloom): 45% NDF, 42% NDF digestibility
```

---

## Inventory Management

### Feed Budgeting

**Annual Feed Requirements**:
```python
def calculate_annual_feed_needs(herd_size: int) -> dict:
    """
    Estimate annual feed needs.

    Assumptions:
    - Average cow: 25 kg DMI/day
    - 10% safety margin
    """
    cow_days = herd_size * 365
    total_DMI_kg = cow_days * 25
    with_safety_margin = total_DMI_kg * 1.10

    # Ration composition
    forage_fraction = 0.55
    concentrate_fraction = 0.45

    return {
        "total_DM_kg": with_safety_margin,
        "forage_needed_kg": with_safety_margin * forage_fraction,
        "concentrate_needed_kg": with_safety_margin * concentrate_fraction
    }
```

**Storage Capacity Planning**:
```python
# Rule of thumb: 6 months storage
months_storage = 6

# Silage bunker sizing
annual_silage_tonnes_DM = 1000
silage_density_kg_DM_m3 = 220
bunker_volume_m3 = annual_silage_tonnes_DM * 1000 / silage_density_kg_DM_m3

# With losses
design_volume_m3 = bunker_volume_m3 * 1.15  # 15% safety factor
```

### Feed Allocation

**Priority System**:
```python
# During shortages, allocate by priority
PRIORITY_ORDER = [
    "lactating_cows",      # Priority 1: Income producers
    "fresh_cows",          # Priority 2: Transition health
    "dry_cows",            # Priority 3: Pregnancy maintenance
    "heifer_II",           # Priority 4: Breeding animals
    "heifer_I",            # Priority 5: Growing animals
    "calves"               # Priority 6: Smallest need
]

if feed_shortage:
    for group in PRIORITY_ORDER:
        if remaining_feed > 0:
            allocate_feed(group, min(requested, remaining_feed))
            remaining_feed -= allocated
```

---

## Feed Purchase Strategies

### Planning Cycle Purchase

**Triggered During Ration Reformulation**:
```python
# Every 30-90 days
planning_interval_days = 60

# Project needs until next reformulation
days_until_next = planning_interval_days
projected_DMI_kg = herd_DMI_per_day * days_until_next

# Current inventory
current_inventory_kg = sum(storage.get_amount() for storage in storages)

# Expected harvests
expected_harvests_kg = sum(projected_yields)

# Shortfall
shortfall_kg = projected_DMI_kg - current_inventory_kg - expected_harvests_kg

if shortfall_kg > 0:
    purchase_feeds(shortfall_kg)
```

### Runtime Purchase

**Emergency Purchases During Shortage**:
```python
# Triggered daily if shortage
if feed_request > available_inventory:
    shortage_kg = feed_request - available_inventory

    # Economic penalty for emergency purchase
    emergency_price_multiplier = 1.20  # 20% premium

    if runtime_purchase_enabled:
        purchase_feed(shortage_kg, emergency_price_multiplier)
    else:
        # Ration animals proportionally
        reduction_factor = available_inventory / feed_request
        for animal in animals:
            animal.actual_intake = animal.target_intake * reduction_factor
```

---

## Performance Metrics

### Storage Efficiency

**Target Losses**:
```python
ACCEPTABLE_STORAGE_LOSSES = {
    "bunker_silage": 0.10,       # 10%
    "pile_silage": 0.15,         # 15%
    "bag_silage": 0.08,          # 8%
    "hay_indoors": 0.02,         # 2%
    "hay_wrapped": 0.05,         # 5%
    "hay_tarped": 0.08,          # 8%
    "hay_unprotected": 0.20,     # 20%
    "baleage": 0.08,             # 8%
    "dry_grain": 0.01,           # 1%
    "high_moisture_grain": 0.04  # 4%
}
```

### Feed Costs

**Cost Components**:
```python
# Per tonne DM
production_cost = (
    seed_cost +
    fertilizer_cost +
    herbicide_cost +
    fuel_machinery_cost +
    labor_cost
)  # $150-250 typical

storage_cost = (
    infrastructure_depreciation +
    plastic_covers +
    electricity_fans
)  # $20-50 typical

loss_cost = (
    DM_lost_tonnes * production_cost
)  # $15-75 depending on loss rate

total_cost_per_tonne_DM = (
    production_cost +
    storage_cost +
    loss_cost
)  # $185-375 typical range
```

### Inventory Turnover

```python
# Days of feed on hand
days_supply = (
    current_inventory_kg_DM /
    daily_herd_DMI_kg
)

# Target: 60-180 days (2-6 months)
if days_supply < 60:
    status = "CRITICAL"
elif days_supply < 90:
    status = "LOW"
elif days_supply < 180:
    status = "ADEQUATE"
else:
    status = "EXCESS"
```

---

*For implementation details, see source code in `RUFAS/biophysical/feed_storage/` and related modules.*
