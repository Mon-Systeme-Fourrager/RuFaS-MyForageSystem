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
class MASMfileError(Exception):
    
    def __init__(self, fName):
        self.msg = "Skipping simulation for " + fName

#-------------------------------------------------------------------------------
# Class: SectionError
#
#-------------------------------------------------------------------------------     
class SectionError(Exception):
    
    def __init__(self, fName, section):
        self.msg = ("MASM FILE SECTION ERROR: " + fName + "\n\t"
                    + section + " section contains no data")
        
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
    
    def __init__(self, fName, section, line, count):
        self.msg = ("MASM FILE LENGTH MISMATCH ERROR: " + fName + "\n\t"
                    + section + " section line " + str(line) + "\n\t"
                    + "This line must contain " + str(count) + " values")
        
        