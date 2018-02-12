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
        # Take the parent base_dir/RUFAS_exe
        #                 parent = base_dir/
        return Path(sys.executable).resolve().parent
    
    # Unfrozen
    else:
        
        # Get path of current file (util.py)
        # Resolve to absolute path
        # Get the 2nd parent  base_dir/RUFAS/util.py
        #                     parent[0] = base_dir/RUFAS
        #                     parent[1] = base_dir/
        return Path(__file__).resolve().parents[1]