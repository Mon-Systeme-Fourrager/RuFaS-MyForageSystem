'''
This module contains the necessary functions for calculating and updating the 
values in a CropType object. Currently the only function meant to be used 
outside of this file is the calculate_actual_Biomass() function. The other 
functions are meant to serve as helper functions within this file.

CropType values updated by calculate_actual_Biomass():
    dBiomass_max
    gamma_reg
    dBiomass_actual
    prev_biomass_actual
    biomass_actual
'''

from math import exp


gammareg_test_file = "gammareg_results.csv"
biomass_test_file = "biomass_results.csv"

def calculate_actual_Biomass(crop_type, time, weather):
    H_phosyn = calculate_intercepted_radiation(crop_type, time, weather)
    crop_type.dBiomass_max = crop_type.RUE * H_phosyn
    
    # calculate_gamma_reg(crop_type, time, weather)
    crop_type.dBiomass_actual = crop_type.dBiomass_max * crop_type.gamma_reg
    crop_type.prev_biomass_actual = crop_type.biomass_actual

    inGrowingPeriod = crop_type.planting_date <= time.day <= crop_type.harvest_date
    if inGrowingPeriod:
        crop_type.biomass_actual += crop_type.dBiomass_actual
    else:
        crop_type.biomass_actual = 0

    #
    # The following is used to test/record the biomass calculations
    #
    with open(biomass_test_file, "a") as testResults:
        results = "%i,%f,%f,%f,%f,%f,%f\n" % (
            time.day,
            weather.radiation[time.year - 1][time.day - 1],
            H_phosyn,
            crop_type.dBiomass_max,
            crop_type.gamma_reg,
            crop_type.dBiomass_actual,
            crop_type.biomass_actual
        )
        if time.day ==1 and time.year == 1:
            testResults.write("Day,H_day,Hphosyn,dbiomax,gamma reg, dbioactual,bioactual\n")
        testResults.write(results)


def calculate_intercepted_radiation(crop_type, time, weather):
    H_day = weather.radiation[time.year-1][time.day-1]
    return 0.5 * H_day * (1 - exp(-1*crop_type.kl*crop_type.LAI_actual))


#
# gamma_reg represents "plant growth factor"
#
def calculate_gamma_reg(crop_type, time, weather):
    wstrs = calculate_wstrs(crop_type)
    tstrs = calculate_tstrs(crop_type, time, weather)
    nstrs = calculate_nstrs(crop_type)
    pstrs = calculate_pstrs(crop_type)
    
    crop_type.gamma_reg = 1- max(wstrs, tstrs, nstrs, pstrs)

    #
    # The following code was used to test the gamma reg and growth constraint calculations
    #
    with open(gammareg_test_file, "a") as testResults:
        testResults.write("%i,%f,%f,%f,%f,%f\n"%\
                          (time.day, wstrs, tstrs, nstrs, pstrs, crop_type.gamma_reg))


    
    
'''
The following four functions comprise the "Growth Constraints".
This includes the water, temperature, nitrogen, and phosphorus stress
for a given day. These values are needed to calculate the gamma_reg value.
They do not modify the values of any State class.
'''

def calculate_wstrs(crop_type):
    if crop_type.Et == 0:
        return 0
    result = 1.0 - (crop_type.water_actual_up / crop_type.Et)
    if result < 0:
        return 0
    else:
        return min(0.99, result)
    
def calculate_tstrs(crop_type, time, weather):
    T_avg = weather.T_avg[time.year-1][time.day-1]
    T_opt = crop_type.T_opt
    T_base_min = crop_type.T_base_min
    MAX = 0.99
    result = 0
    if T_avg <= T_base_min:
        result = MAX
    
    elif T_base_min < T_avg  and T_avg <= T_opt:
        top_half_eq = -0.1054 * (T_opt - T_avg)**2
        bottom_half_eq = (T_avg - T_base_min)**2
        result = 1 - exp(top_half_eq / bottom_half_eq)
    
    elif T_opt < T_avg and T_avg <= (2 * T_opt - T_base_min):
        top_half_eq = -0.1054 * (T_opt - T_avg)**2
        bottom_half_eq = (2*T_opt - T_avg - T_base_min)**2
        result = 1 - exp(top_half_eq / bottom_half_eq)
    
    elif T_avg > (2*T_opt - T_base_min):
        result = MAX
    else:
        ''' Should have hit one of the preceding cases. Not sure if they cover
            all possible cases though.'''
        print("Error: Did not hit one of the cases for calculate_tstrs.")
        print("Check if T_opt and T_base_min input values are correct")
        print("Exiting program")
        exit()

    return min(result, MAX)
    
def calculate_nstrs(crop_type):
    if crop_type.bio_N_opt == 0:
        return 0
    phi_n = max(0, 200 * ((crop_type.bio_N/crop_type.bio_N_opt) - 0.5))
    result = 1 - phi_n / (phi_n + exp(3.535 - 0.02597*phi_n))
    return min(0.99, result)
    
def calculate_pstrs(crop_type):
    if crop_type.bio_P_opt == 0:
        return 0
    phi_p = 200 * ((crop_type.bio_P/crop_type.bio_P_opt) - 0.5)
    result = 1 - phi_p / (phi_p + exp(3.535 - 0.02597 * phi_p))
    return min(0.99, result)