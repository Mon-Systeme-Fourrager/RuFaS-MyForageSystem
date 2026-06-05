# Graph Report - RuFaS-MyForageSystem  (2026-06-05)

## Corpus Check
- 205 files · ~245,469 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 4328 nodes · 28486 edges · 37 communities detected
- Extraction: 17% EXTRACTED · 83% INFERRED · 0% AMBIGUOUS · INFERRED: 23659 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 65|Community 65]]

## God Nodes (most connected - your core abstractions)
1. `OutputManager` - 1031 edges
2. `GeneralConstants` - 892 edges
3. `RufasTime` - 805 edges
4. `MeasurementUnits` - 704 edges
5. `Utility` - 583 edges
6. `InputManager` - 507 edges
7. `AnimalType` - 471 edges
8. `SoilData` - 400 edges
9. `AnimalModuleConstants` - 382 edges
10. `AnimalConfig` - 362 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `OutputManager`  [INFERRED]
  main.py → RUFAS/output_manager.py
- `CaseInsensitiveArgumentAction` --uses--> `OutputManager`  [INFERRED]
  main.py → RUFAS/output_manager.py
- `Parse command line options, if applicable` --uses--> `OutputManager`  [INFERRED]
  main.py → RUFAS/output_manager.py
- `main()` --calls--> `TaskManager`  [INFERRED]
  main.py → RUFAS/task_manager.py
- `main()` --calls--> `LogVerbosity`  [INFERRED]
  main.py → RUFAS/output_manager.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.01
Nodes (512): Initialize genetic attributes., Calculate EBV and ranking index values., Recalculate genetic values at lactation start., Calculate TBV values for an animal entering the herd., Calculate TBV values for a newborn calf., Calculate Permanent Environment Effect (E_permanent) values., Calculate Temporary Environment Effect (E_temporary) values., Calculate phenotype values. (+504 more)

### Community 1 - "Community 1"
Cohesion: 0.02
Nodes (372): BiomassAllocation, _determine_above_ground_biomass(), _determine_accumulated_biomass(), _determine_below_ground_biomass(), _determine_max_accumulation(), _intercept_radiation(), Partition the accumulated biomass into above ground and below ground portions., Calculate the amount of solar radiation intercepted for photosynthesis during th (+364 more)

### Community 2 - "Community 2"
Cohesion: 0.01
Nodes (437): CarbonCycling, _determine_soil_active_carbon_fraction(), _determine_soil_mass(), _determine_soil_overall_carbon_fraction(), _determine_soil_passive_carbon_fraction(), _determine_soil_slow_carbon_fraction(), _determine_soil_volume(), _determine_total_carbon_CO2_lost() (+429 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (362): AnimalConfig, initialize_animal_config(), AnimalConfig class that holds all the animal configuration parameters from user, Initialize the animal config from the input manager user input data., Retrieve the CowTAISubProtocol associated with the cow's ovsynch program if the, Setter method for the cow_ovsynch_program property.          Parameters, Returns the cow ReSynch program specific to the cow species.          Returns, Sets the cow ReSynch program for the object. This method ensures         that th (+354 more)

### Community 4 - "Community 4"
Cohesion: 0.04
Nodes (348): Animal, AnimalGroupingScenario, The different scenarios for grouping animals on a farm.     Each scenario is a d, Get the animal subtype of the given heiferIII.          Parameters         -----, Get the animal subtype of the given cow.          Parameters         ----------, Get the animal type of the given animal.          Parameters         ----------, # TODO: Probably change the names of these scenarios to be more concise/descript, Find the animal combination that the given animal belongs to.          Parameter (+340 more)

### Community 5 - "Community 5"
Cohesion: 0.02
Nodes (243): Calculates the fresh matter mass of this crop in kg., Checks if the crop is alfalfa based on its configuration name.          Returns, ManureNutrients, A class to store the relevant manure nutrient information to be passed to the cr, Return a new ManureNutrients with all numeric nutrient/mass         fields zeroe, Add two ManureNutrients objects together.          Parameters         ----------, Multiply a ManureNutrients object by a scalar (left multiplication, i.e. ManureN, Subtract two ManureNutrients objects.          Parameters         ---------- (+235 more)

### Community 6 - "Community 6"
Cohesion: 0.02
Nodes (140): DiseaseOutcomes, Returns the value of the enum member as its string representation., A list of possible outcomes for animals that have developed a disease.      HEAL, HerdManager, set_animal_grouping_scenario(), AvailableFeedsBuilder, FeedFulfillmentResults, Builds the list of feeds available for use in the simulation.      This class is (+132 more)

### Community 7 - "Community 7"
Cohesion: 0.01
Nodes (119): ABC, _record_animal_events(), _record_cows_conception_rate(), _record_heiferIIs_conception_rate(), _report_all_animals_genetic_history(), report_end_of_simulation(), report_sold_animal_information(), report_sold_animal_information_sort_by_sell_day() (+111 more)

### Community 8 - "Community 8"
Cohesion: 0.02
Nodes (112): CrossValidator, DataValidator, ElementsCounter, ElementState, get_required_during_initialization(), Modifiability, Validates a data element of type array.          Parameters         ----------, Returns the total number of elements by adding the counts of valid, invalid, and (+104 more)

### Community 9 - "Community 9"
Cohesion: 0.07
Nodes (1): milk_statistics()

### Community 10 - "Community 10"
Cohesion: 0.09
Nodes (3): _add_phosphorus_to_pool(), calculate_phosphorus_sorption_parameter(), determine_soil_nutrient_area_density()

### Community 11 - "Community 11"
Cohesion: 0.16
Nodes (18): _calculate_activity_energy_requirements(), _calculate_calcium_requirement(), _calculate_dry_matter_intake(), _calculate_growth_energy_requirements(), _calculate_maintenance_energy_requirements(), _calculate_phosphorus_requirement(), _calculate_pregnancy_energy_requirements(), _calculate_protein_requirement() (+10 more)

### Community 12 - "Community 12"
Cohesion: 0.18
Nodes (19): _determine_adjusted_sediment_yield(), _determine_carbon_content_factor(), _determine_clay_silt_ratio_factor(), _determine_coarse_fragment_factor(), _determine_coarse_sand_factor(), _determine_cover_management_factor(), _determine_exponential_term(), _determine_fraction_rainfall_during_time_of_concentration() (+11 more)

### Community 13 - "Community 13"
Cohesion: 0.11
Nodes (3): make_empty_evaluation_results(), make_empty_nutrition_requirements(), make_empty_nutrition_supply()

### Community 14 - "Community 14"
Cohesion: 0.15
Nodes (1): evaluate_nutrition_supply()

### Community 15 - "Community 15"
Cohesion: 0.33
Nodes (11): compare_actual_and_expected_test_results(), _convert_expected_result_variable_names(), _duplicate_mappings_exist(), filter_insignificant_changes(), filter_nested(), _find_duplicate_mappings(), _get_matching_path(), _get_test_result_paths() (+3 more)

### Community 16 - "Community 16"
Cohesion: 0.27
Nodes (7): calculate_anaerobic_coefficient(), calculate_carbon_decomposition(), calculate_carbon_decomposition_rate(), calculate_ifsm_methane_emission(), calculate_max_microbial_decomposition_rate(), calculate_methane_conversion_factor(), calculate_slow_fraction_decomposition_rate()

### Community 17 - "Community 17"
Cohesion: 0.22
Nodes (6): Generic method to generate application events.          Parameters         -----, Prepares the attributes to pass into the event classes constructor.          Par, repeat_pattern(), _validate_days(), _validate_parameters(), _validate_years()

### Community 20 - "Community 20"
Cohesion: 0.5
Nodes (6): calculate_cow_methane(), _calculate_cow_mills_methane(), _calculate_dry_cow_enteric_methane(), calculate_heifer_methane(), _calculate_IPCC_methane(), _calculate_lactating_cow_enteric_methane()

### Community 21 - "Community 21"
Cohesion: 0.4
Nodes (3): Initialize the RationConfig class with the provided feed information. If the inp, RationConfig provides a structured way to represent the collection of animal req, RationConfig

### Community 22 - "Community 22"
Cohesion: 0.5
Nodes (2): Initialize event from a string          Args:                 events_str: string, Add a cow life event          Args:                 animal_age: the date counter

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (2): get_adjusted_schedule(), get_schedule()

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (1): Parses a unit string to handle units with exponents.          Parameters

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (1): Extracts the units from a key.          Parameters         ----------         ke

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (1): Combines two unit dictionaries by adding or subtracting their exponents.

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (1): Simplify the units by cancelling out common units in the numerator and denominat

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (1): Converts two dictionaries of units (numerator and denominator) back to a single

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (1): Checks if maturity has been reached based on the fraction of potential heat unit

### Community 42 - "Community 42"
Cohesion: 1.0
Nodes (1): Indicates if the plant is in its growing season.          Returns         ------

### Community 43 - "Community 43"
Cohesion: 1.0
Nodes (1): Checks if a user-defined harvest index is given, which triggers a harvest index

### Community 44 - "Community 44"
Cohesion: 1.0
Nodes (1): Check if the plant is in senescence.          Returns         -------         bo

### Community 45 - "Community 45"
Cohesion: 1.0
Nodes (1): Calculate the maximum amount of water that can be held in the canopy.          R

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (1): Calculate the fraction of potential heat units accumulated by the plant.

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (1): Calculate the amount of water in the soil profile when completely saturated (mm)

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (1): True if the animal is a heifer, False otherwise

### Community 58 - "Community 58"
Cohesion: 1.0
Nodes (1): True if the animal is a cow, False otherwise

### Community 65 - "Community 65"
Cohesion: 1.0
Nodes (1): Calculates reduction in methane yield (%) due to addition of certain methane mit

## Knowledge Gaps
- **226 isolated node(s):** `A list of acceptable units used within the RuFaS model.`, `Returns the value of the enum member as its string representation.`, `Parses a unit string to handle units with exponents.          Parameters`, `Extracts the units from a key.          Parameters         ----------         ke`, `Combines two unit dictionaries by adding or subtracting their exponents.` (+221 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 9`** (28 nodes): `calf_birth_weight()`, `calves()`, `calving_interval()`, `calving_interval_history()`, `conceptus_weight()`, `cow_ovsynch_program()`, `cow_presynch_program()`, `cow_reproduction_program()`, `cow_resynch_program()`, `daily_distance()`, `daily_horizontal_distance()`, `daily_vertical_distance()`, `days_in_milk()`, `days_in_pregnancy()`, `dead()`, `future_cull_date()`, `future_death_date()`, `gestation_length()`, `heifer_reproduction_program()`, `heifer_reproduction_sub_program()`, `is_milking()`, `is_pregnant()`, `milk_statistics()`, `set_nutrient_standard()`, `setup_lactation_curve_parameters()`, `sold()`, `stillborn()`, `animal.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 14`** (13 nodes): `_calculate_activity_maintenance_energy_supplied()`, `_calculate_calcium_supplied()`, `_calculate_dry_matter_intake()`, `_calculate_fat_supplied()`, `_calculate_forage_neutral_detergent_fiber_supplied()`, `_calculate_growth_energy_supplied()`, `_calculate_lactation_energy_supplied()`, `_calculate_neutral_detergent_fiber_supplied()`, `_calculate_phosphorus_supplied()`, `_calculate_protein_supplied()`, `_calculate_total_energy_supplied()`, `evaluate_nutrition_supply()`, `nutrition_evaluator.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (4 nodes): `.add_event()`, `.init_from_string()`, `Initialize event from a string          Args:                 events_str: string`, `Add a cow life event          Args:                 animal_age: the date counter`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (3 nodes): `get_adjusted_schedule()`, `get_schedule()`, `hormone_delivery_schedule.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (1 nodes): `Parses a unit string to handle units with exponents.          Parameters`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (1 nodes): `Extracts the units from a key.          Parameters         ----------         ke`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (1 nodes): `Combines two unit dictionaries by adding or subtracting their exponents.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (1 nodes): `Simplify the units by cancelling out common units in the numerator and denominat`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (1 nodes): `Converts two dictionaries of units (numerator and denominator) back to a single`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (1 nodes): `Checks if maturity has been reached based on the fraction of potential heat unit`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (1 nodes): `Indicates if the plant is in its growing season.          Returns         ------`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (1 nodes): `Checks if a user-defined harvest index is given, which triggers a harvest index`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (1 nodes): `Check if the plant is in senescence.          Returns         -------         bo`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (1 nodes): `Calculate the maximum amount of water that can be held in the canopy.          R`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (1 nodes): `Calculate the fraction of potential heat units accumulated by the plant.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (1 nodes): `Calculate the amount of water in the soil profile when completely saturated (mm)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `True if the animal is a heifer, False otherwise`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (1 nodes): `True if the animal is a cow, False otherwise`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (1 nodes): `Calculates reduction in methane yield (%) due to addition of certain methane mit`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GeneralConstants` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 6`, `Community 8`, `Community 12`?**
  _High betweenness centrality (0.249) - this node is a cross-community bridge._
- **Why does `OutputManager` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 6`, `Community 7`, `Community 8`, `Community 15`?**
  _High betweenness centrality (0.212) - this node is a cross-community bridge._
- **Why does `SoilData` connect `Community 2` to `Community 0`, `Community 1`, `Community 6`, `Community 7`, `Community 12`?**
  _High betweenness centrality (0.125) - this node is a cross-community bridge._
- **Are the 952 inferred relationships involving `OutputManager` (e.g. with `CaseInsensitiveArgumentAction` and `Parse command line options, if applicable`) actually correct?**
  _`OutputManager` has 952 INFERRED edges - model-reasoned connections that need verification._
- **Are the 890 inferred relationships involving `GeneralConstants` (e.g. with `LogVerbosity` and `OriginLabel`) actually correct?**
  _`GeneralConstants` has 890 INFERRED edges - model-reasoned connections that need verification._
- **Are the 798 inferred relationships involving `RufasTime` (e.g. with `Weather` and `The `Weather` class manages all weather data used to run a single simulation.`) actually correct?**
  _`RufasTime` has 798 INFERRED edges - model-reasoned connections that need verification._
- **Are the 700 inferred relationships involving `MeasurementUnits` (e.g. with `LogVerbosity` and `OriginLabel`) actually correct?**
  _`MeasurementUnits` has 700 INFERRED edges - model-reasoned connections that need verification._