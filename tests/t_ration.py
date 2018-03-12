################################################################################
#
# RUFAS: Ruminant Farm Systems Model
#
# t_LP.py - Test bench for LP module
#
# Authors: Kass Chupongstimun
#          Jit Patil JITs
#
################################################################################

from RUFAS.routines.animal.ration import optimize_feed_ration

#-------------------------------------------------------------------------------
# Function: test_ration
#-------------------------------------------------------------------------------
def test_ration():
 
    #
    # HARD-CODED USER INPUTS!!!!!
    #
    parity = 1      # number of lactations
    WIM = 20        # week in milk, week
    AMF = 3.5       # average milk fat for the breed, %
    BWR = 1         # ratio of calving body weight to holstein calving weight
    base_NED = 1     # Baseline net energy density of the diet
    housing = "barn"

    feed = {
            'CG':       {
                            'FI': 0.056,    # FILL UNITS
                            'RV': -0.154,   # ROUGHAGE UNITS
                            'NE': 1.97,     # NE
                            'CP': 0.1,      # CP
                            'ICP': 0.41,    # INDIGESTIBLE CP
                            'RDP': 0.12,    # RUMEN DEGRADABLE
                            'conc': "conc", # CONCENTRATE
                            'price': 0.132, # PRICE
                            'limit': 20     # LIMIT
                        },
            'PROT':     {
                            'FI': 0.048,
                            'RV': -0.162,
                            'NE': 1.85,
                            'CP': 0.49,
                            'ICP': 0.33,
                            'RDP': 0.32,
                            'conc': "conc",
                            'price': 0.462,
                            'limit': 10
                        },
            'UPROT':    {
                            'FI': 0.048,
                            'RV': -0.162,
                            'NE': 5.67,
                            'CP': 0.62,
                            'ICP': 0.2,
                            'RDP': 0.4,
                            'conc': "conc",
                            'price': 0.46,
                            'limit': 2
                        },
            'FAT':      {
                            'FI': 0.0,
                            'RV': 0.0,
                            'NE': 10.92,
                            'CP': 0.0,
                            'ICP': 0.0,
                            'RDP': 0.0,
                            'conc': "conc",
                            'price': 1.06,
                            'limit': 100
                        }
           }

    ration = optimize_feed_ration(parity, WIM, AMF, BWR, base_NED, housing, feed)
    print(ration) 
    