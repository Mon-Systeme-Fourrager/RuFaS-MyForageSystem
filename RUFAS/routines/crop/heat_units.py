'''
RUFAS: Ruminant Farm Systems Model

File name: heat_units.py

Author(s): Andy Achenreiner, achenreiner@wisc.edu

Description: This module contains the necessary functions for calculating and
             updating a CropType's fr_PHU (fraction of PHU accumulated by
             current day). Since this submodule does not depend on values
             calculated in other crop submodules, heat_units.update_all() should
             be the first function called in the daily_crop_routine.

Variable Definitions:

    * Note that all temperatures listed below are in degrees Celcius

    T_min = Minimum temperature on current day

    T_max = Maximum temperature on current day

    T_base_min = Crop-specific minimum temperature required for growth

    T_base_max = Crop-specific maximum temperature required to sustain growth.

    T_HU_min = Minimum heat unit temperature on current day

    T_HU_max = Maximum heat unit temperature on current day

    T_HU = Mean heat unit temperature on current day

    HU = Available heat units on current day

    prev_accumulated_HU = Accumulated_HU leading up to today

    accumulated_HU = Heat units accumulated up to and including today

    PHU = Crop-specific total heat units required for maturity

    prev_fr_PHU = Fraction of PHU accumulated up to today

    fr_PHU = Fraction of PHU accumulated including today

CropType values updated by calling calculate_frPHU():

    prev_accumulated_HU

    accumulated_HU

    prev_fr_PHU

    fr_PHU

'''
################################################################################

#
# This function calls the functions necessary to update the current heat unit
# information.
#
def update_all(crop, T_min, T_max, time):
    results = calculate_frPHU(crop, T_min, T_max, time)
    record_results(crop, time, results)


#
# This function calculates the fraction of PHU accumulated up to and including
# today. The equations used for this part can be found in
# "Pseudo code_SC_maxdeltabio_1.0.docx" section 1.B and 1.C
#
def calculate_frPHU(crop, T_min, T_max, time):
    #
    # Part 1B of Crop Biomass pseudocode
    #
    T_HU_min = calc_T_HU_min(crop, T_min)

    T_HU_max = calc_T_HU_max(crop, T_max)

    HU = calc_HU(crop, T_HU_min, T_HU_max)


    crop.prev_accumulated_HU = crop.accumulated_HU

    if time.day >= crop.planting_date:
        crop.accumulated_HU += HU

    # Calculate accumulated fraction of potential Heat Units

    crop.prev_fr_PHU = crop.fr_PHU

    crop.fr_PHU = crop.accumulated_HU / crop.PHU

    calc_info = (T_max, T_min, T_HU_min, T_HU_max, HU)

    return calc_info


def calc_T_HU_min(crop, T_min):
    if T_min < crop.T_base_min:
        return crop.T_base_min
    else:
        return T_min


def calc_T_HU_max(crop, T_max):
    if T_max > crop.T_base_max:
        return crop.T_base_max
    else:
        return T_max


def calc_HU(crop, T_HU_min, T_HU_max):
    T_HU = (T_HU_min + T_HU_max) / 2

    if T_HU < crop.T_base_min:
        return 0.0
    else:
        return T_HU - crop.T_base_min


#==============================================================================

''' The follow can be used for testing purposes '''

#
# The file that will record results of the heat unit calculations.
# This is for testing purposes.
#
heat_units_test_file = "heat_units_results.csv"

#
# The following will record the heat unit calculations into the
# test file.
#
def record_results(crop, time, results):
    T_max, T_min, T_HU_min, T_HU_max, HU = results
    with open(heat_units_test_file, "a") as resultFile:
        info = "%i,%f,%f,%f,%f,%f,%f,%f\n"%\
               (time.day,T_max,T_min,T_HU_max,T_HU_min,HU,crop.accumulated_HU,crop.fr_PHU)
        resultFile.write(info)