################################################################################
#
# RUFAS: Ruminant Farm Systems Model
#
# errors.py - Contains custom errors
#
# Authors: Kass Chupongstimun
#          Jit Patil
#
################################################################################

#-------------------------------------------------------------------------------
# Class: UserInput
#
#-------------------------------------------------------------------------------     
class UserInput(Exception):
    
    def __init__(self, msg):
        self.msg = "USER INPUT ERROR: " + msg

#-------------------------------------------------------------------------------
# Class: 
#
#-------------------------------------------------------------------------------     
class InvalidJSONfile(Exception):
    
    def __init__(self, fName):
        self.msg = "Skipping simulation for {}\n".format(fName)
        
#-------------------------------------------------------------------------------
# Class: LengthMismatchError
#
#-------------------------------------------------------------------------------     
class JSONfileData(Exception):
    
    def __init__(self, section, msg):
        self.section = section
        self.msg = msg
        
        