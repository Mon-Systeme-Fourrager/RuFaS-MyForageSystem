################################################################################
#
# MASM: Modular Agricultural Systems Modeling Environment
#
# read_json.py - Contains routines to read and interpret json files
#
# Authors: Kass Chupongstimun
#          Jit Patil
#
################################################################################

import json
from pathlib import Path

from MASM.outputs import OutputHandler
from MASM.errors import LengthMismatchError, JSONfileError, InvalidJSONfileError
from MASM.classes import State, Config, Weather

#-------------------------------------------------------------------------------
# Function: read_json_file
#           Sets up the parameters of the simulation
#           Reads and interprets the json file
#
# Parameters: fPath - Path to the MASM file for the simulation
#             c - Config object to be written to
#             w - Weather object to be written to
#             o - Output object to be written to
#
# Raises: InvalidJSONfileError - when there is a problem with the json file
#-------------------------------------------------------------------------------
def read_json_file(fPath:Path, s:State, c:Config, w:Weather, o:OutputHandler):
    
    c.fName = fPath.name
    
    with fPath.open('r') as f:
        data = json.load(f)
        
        try:
            read_config(data['config'], c)
            read_weather(data['weather'], w, c)
            read_farm(data['farm'], s, c)
            read_output_options(data['output'], o, c)
            
        except (JSONfileError, LengthMismatchError) as e:
            print(e.msg)
            raise InvalidJSONfileError(c.fName)
        
        except Exception:
            print("Something wrong with {}".format(c.fName))
            raise InvalidJSONfileError(c.fName)
        
#-------------------------------------------------------------------------------
# Function: read_config
# 
#-------------------------------------------------------------------------------
def read_config(data, c:Config):
    
    c.iterations = data['iterations']
    c.iterate = data['iterations'] > 1
    c.years = data['years']

#-------------------------------------------------------------------------------
# Function: read_output_options
# 
#-------------------------------------------------------------------------------
def read_output_options(data, o:OutputHandler, c:Config):

    if len(data) != len(o.report_handlers):
        raise LengthMismatchError(c.fName, "OUTPUT", len(o.report_handlers))
    
    for key, value in data.items():
        if key not in o.report_handlers:
            raise JSONfileError(c.fName, "OUTPUT",
                                "Output Report Handler name mismatch")
        else:
            o.report_handlers[key].active = value['active']
            if data[key]['file_name'] is not None:
                o.report_handlers[key].fName = value['file_name']
            
    
#-------------------------------------------------------------------------------
# Function: read_weather
# 
#-------------------------------------------------------------------------------
def read_weather(wPath:Path, w:Weather, c:Config):
    
    return
    
    with wPath.open('r') as f:
        pass
        
        #
        # Interpret weather file here
        #

#-------------------------------------------------------------------------------
# Function: read_farm
# 
#-------------------------------------------------------------------------------
def read_farm(data, s:State, c:Config):
    
    read_crops(data, s.crops, c)
    read_feed(data, s.feed, c)
    read_fieldOps(data, s.fieldOps, c)
    read_herd(data, s.herd, c)
    read_housing(data, s.housing, c)
    read_manure(data, s.manure, c)
    read_soil(data, s.soil, c)
    
#-------------------------------------------------------------------------------
# Function: read_crops
# 
#-------------------------------------------------------------------------------
def read_crops(f, cp, c:Config):
    pass

#-------------------------------------------------------------------------------
# Function: read_feed
# 
#-------------------------------------------------------------------------------
def read_feed(f, fd, c:Config):
    pass

#-------------------------------------------------------------------------------
# Function: read_fieldOps
# 
#-------------------------------------------------------------------------------
def read_fieldOps(f, fo, c:Config):
    pass

#-------------------------------------------------------------------------------
# Function: read_herd
# 
#-------------------------------------------------------------------------------
def read_herd(f, hd, c:Config):
    pass

#-------------------------------------------------------------------------------
# Function: read_housing
# 
#-------------------------------------------------------------------------------
def read_housing(f, hs, c:Config):
    pass

#-------------------------------------------------------------------------------
# Function: read_manure
# 
#-------------------------------------------------------------------------------
def read_manure(f, mn, c:Config):
    pass

#-------------------------------------------------------------------------------
# Function: read_soil
# 
#-------------------------------------------------------------------------------
def read_soil(f, so, c:Config):
    pass

    