'''
This module contains the necessary functions for calculating and updating the 
Leaf Area Index of the current day. The only function that is meant to be called 
outside of this file is calculate_LAI_actual().

The plant growth factor (aka crop.gamma_reg needs to be updated prior to this function being called.

CropType values updated by calling calculate_LAI_actual():
    prev_fr_LAI_max
    fr_LAI_max
    LAI_actual
    prev_LAI_actual
'''
from math import exp, log, floor, sqrt
from decimal import *

lai_test_file = "LAI_results.csv"

def calculate_LAI_actual(crop, time):
    l1, l2 = calculate_shape_coefficients(crop)

    crop.prev_fr_LAI_max = crop.fr_LAI_max
    inGrowingPeriod =  crop.planting_date <= time.day <= crop.harvest_date
    if not inGrowingPeriod:
        crop.fr_LAI_max = Decimal("0")
    else:
        crop.fr_LAI_max = crop.fr_PHU / (crop.fr_PHU + (l1 - l2*crop.fr_PHU).exp())

    if not inGrowingPeriod:
        dLAI_max = Decimal("0")
        dLAI_actual = Decimal("0")

    elif crop.fr_PHU < crop.fr_PHU_sen:
        exp_part = (5 * (crop.prev_LAI_actual - crop.LAI_max)).exp()
        dLAI_max = (crop.fr_LAI_max - crop.prev_fr_LAI_max) * crop.LAI_max * (1-exp_part)
        dLAI_actual = dLAI_max * Decimal(sqrt(crop.gamma_reg))
        crop.LAI_actual = crop.LAI_actual + dLAI_actual

    else:
        prev_LAI_actual = crop.LAI_actual
        result = crop.LAI_max * (1-crop.fr_PHU) / (1-crop.fr_PHU_sen)
        crop.LAI_actual = max(result, 0)
        dLAI_max = crop.LAI_actual - prev_LAI_actual
        dLAI_actual = dLAI_max * Decimal(sqrt(crop.gamma_reg))


    #
    # The following is for testing the LAI calculations
    #
    with open(lai_test_file, "a") as resultFile:
        result = "%i,%f,%f,%f,%f,%f,%f\n" %\
                 (time.day, crop.fr_PHU, crop.fr_LAI_max, dLAI_max, crop.gamma_reg,dLAI_actual, crop.LAI_actual)
        resultFile.write(result)
        crop.line += 1

    # crop.prev_LAI_actual = temp_for_LAI
    

def calculate_shape_coefficients(crop):
    l2_part1 = (crop.fr_PHU_1 / crop.fr_LAI_1) - crop.fr_PHU_1
    l2_part2 = (crop.fr_PHU_2 / crop.fr_LAI_2) - crop.fr_PHU_2

    
    l2 = ( Decimal(log(l2_part1) - log(l2_part2))
           / (crop.fr_PHU_2 - crop.fr_PHU_1) )
 
    
    l1_part1 = (crop.fr_PHU_1 / crop.fr_LAI_1) - crop.fr_PHU_1
    
    l1 = Decimal(log(l1_part1)) + l2 * crop.fr_PHU_1
    
    return l1, l2
    