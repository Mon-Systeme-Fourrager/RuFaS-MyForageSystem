################################################################################
#
# MASM: Modular Agricultural Systems Modeling Environment
#
# errors.py - Contains custom errors
#
# Authors: Kass Chupongstimun
#          Jit Patil
#
################################################################################

#-------------------------------------------------------------------------------
# Class: UserInputError
#
#-------------------------------------------------------------------------------     
class UserInputError(Exception):
    
    def __init__(self, msg):
        self.msg = "USER INPUT ERROR: " + msg

#-------------------------------------------------------------------------------
# Class: SectionError
#
#-------------------------------------------------------------------------------     
class InvalidJSONfileError(Exception):
    
    def __init__(self, fName):
        self.msg = "Skipping simulation for {}\n".format(fName)
        
#-------------------------------------------------------------------------------
# Class: ParsingError
#
#-------------------------------------------------------------------------------     
class ParsingError(Exception):
    
    def __init__(self, fName, section, line, kind):
        self.msg = ("MASM FILE PARSING ERROR: " + fName + "\n\t"
                    + section + " section at line " + str(line) + "\n\t"
                    + "Data on this line must be parsable as " + kind)
        
#-------------------------------------------------------------------------------
# Class: LengthMismatchError
#
#-------------------------------------------------------------------------------     
class LengthMismatchError(Exception):
    
    def __init__(self, fName, section, count):
        self.msg = ("JSON FILE LENGTH MISMATCH ERROR: " + fName + "\n\t"
                    + section + " section must contain " + str(count) + " values")
        
#-------------------------------------------------------------------------------
# Class: LengthMismatchError
#
#-------------------------------------------------------------------------------     
class JSONfileError(Exception):
    
    def __init__(self, fName, section, msg):
        self.msg = ("JSON FILE ERROR: " + fName + "\n\t"
                    + section + " section\n\t"
                    + msg + '\n')
        
        