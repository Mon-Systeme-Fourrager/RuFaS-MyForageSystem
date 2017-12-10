
import sys
import json

from pathlib import Path
from MASM import util
from MASM.data import *
from MASM.outputs import OutputHandler

#-------------------------------------------------------------------------------
# Function: read_json_file
#           Sets up the parameters of the simulation
#           Reads and interprets the json file
#
# Parameters: fPath - Path to the MASM file for the simulation
#             c - Config object to be written to
#             w - Weather object to be written to
#             o - Output object to be written to
#-------------------------------------------------------------------------------
def read_json_file(fPath:Path, s:State, c:Config, w:Weather, o:OutputHandler):
    
    with fPath.open('r') as f:
        
        data = json.load(f)
        
        read_config(data['config'], c)
        read_farm(data['farm'], s, c)
        #read_weather(data['weather'], c, w)
        read_output_options(data['output'], o, c)
        
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

    if len(data) != len(o.outputObjects):
        pass
    
    for key, value in data.items():
        if not key in o.outputObjects:
            pass
        else:
            o.outputObjects[key].active = value['active']
            if not data[key]['file_name'] is None:
                o.outputObjects[key].fName = value['file_name']
            
    
#-------------------------------------------------------------------------------
# Function: read_weather
# 
#-------------------------------------------------------------------------------
def read_weather(wPath:Path, c:Config, w:Weather):
    
    
    with wPath.open('r') as f:
        pass
        
        #
        # Interpret weather file here
        #

#-------------------------------------------------------------------------------
# Function: read_farm
# 
#-------------------------------------------------------------------------------
def read_farm(fContents, s:State, c:Config):
    
    read_crops(fContents, s.crops, c)
    read_feed(fContents, s.feed, c)
    read_fieldOps(fContents, s.fieldOps, c)
    read_herd(fContents, s.herd, c)
    read_housing(fContents, s.housing, c)
    read_manure(fContents, s.manure, c)
    read_soil(fContents, s.soil, c)
    
#-------------------------------------------------------------------------------
# Function: read_crops
# 
#-------------------------------------------------------------------------------
def read_crops(f, cp:Crops, c:Config):
    pass

#-------------------------------------------------------------------------------
# Function: read_feed
# 
#-------------------------------------------------------------------------------
def read_feed(f, fd:Feed, c:Config):
    pass

#-------------------------------------------------------------------------------
# Function: read_fieldOps
# 
#-------------------------------------------------------------------------------
def read_fieldOps(f, fo:FieldOps, c:Config):
    pass

#-------------------------------------------------------------------------------
# Function: read_herd
# 
#-------------------------------------------------------------------------------
def read_herd(f, hd:Herd, c:Config):
    pass

#-------------------------------------------------------------------------------
# Function: read_housing
# 
#-------------------------------------------------------------------------------
def read_housing(f, hs:Housing, c:Config):
    pass

#-------------------------------------------------------------------------------
# Function: read_manure
# 
#-------------------------------------------------------------------------------
def read_manure(f, mn:Manure, c:Config):
    pass

#-------------------------------------------------------------------------------
# Function: read_soil
# 
#-------------------------------------------------------------------------------
def read_soil(f, so:Soil, c:Config):
    pass

    