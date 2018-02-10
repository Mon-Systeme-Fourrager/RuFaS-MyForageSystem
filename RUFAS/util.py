import sys
from pathlib import Path

#-------------------------------------------------------------------------------
# Function: get_base_dir
#           Gets the base directory as reference for all relative paths
#
#           Unfrozen appliaction - gets the project directory
#           Frozen application - gets the executable directory
#
# Returns: The reference directory for all paths in the program
#-------------------------------------------------------------------------------
def get_base_dir():
    
    # Frozen
    if getattr(sys, 'frozen', False):
        
        # Get the executable file path
        # Resolve to absolute path
        # Take the parent xxx/RUFAS_exe
        #                 parent = xxx/
        return Path(sys.executable).resolve().parent
    
    # Unfrozen
    else:
        
        # Get path of current file (util.py)
        # Resolve to absolute path
        # Get the 2nd parent  xxx/RUFAS/util.py
        #                     parent[1] = xxx/
        #                     parent[0] = xxx/RUFAS
        return Path(__file__).resolve().parents[1]