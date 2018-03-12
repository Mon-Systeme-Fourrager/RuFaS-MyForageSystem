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

#!/usr/bin/env python3

import tests

def test():

    #
    # TEST LP ROUTINE
    #
    #tests.test_LP()

    #
    # TEST RATION FORMULATION ROUTINE
    #
	tests.test_ration()

#-------------------------------------------------------------------------------
#
# PROGRAM ENTRY POINT
#
#------------------------------------------------------------------------------- 
if __name__ == '__main__': test()
        
    