# Path: utils.py
# Last Modified: 2025-06-11

import sys from pathlib
import Path import os
import re
def get_input_paths():     
    paths = []     
    if len(sys.argv) > 1:         
        paths.extend(sys.argv[1:])     
    if not sys.stdin.isatty():         
        paths.extend(line.strip() 
    for line in sys.stdin 
        if line.strip())     
    return [Path(p).resolve() for p in paths]
