################################################################################
#
# MASM: Modular Agricultural Systems Modeling Environment
#
# Util.py - Contains various utility and helper functions
#
# Authors: Kass Chupongstimun
#          Jit Patil
#
################################################################################

#-------------------------------------------------------------------------------
# Function: to_ints
#           Parses all elements of a list of strings to integers
#-------------------------------------------------------------------------------
def to_ints(l:list):
    try:
        return [int(_) for _ in l]
    except Exception:
        return None

#-------------------------------------------------------------------------------
# Function: to_floats
#           Parses all elements of a list of strings to floating points
#-------------------------------------------------------------------------------
def to_floats(l:list):
    try:
        return [float(_) for _ in l]
    except Exception:
        return None

#-------------------------------------------------------------------------------
# Function: to_bools
#           Parses all elements of a list of strings to booleans
#-------------------------------------------------------------------------------
def to_bools(l:list):
    for i in l:
        if (i != '0' and i != '1'):
            return None
    
    return [int(_) == 1 for _ in l]

#-------------------------------------------------------------------------------
# Function: toString2Dlist
#           
#-------------------------------------------------------------------------------
def to_str_2Dlist(l:list):
    s = ""
    for row in l:
        for e in row:
            s += e + '\t'
        s = s.rstrip() + '\n'
    return s.rstrip()
        
