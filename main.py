# main.py
import sys
import os
from state import State
from core import main
from filesystem import resolve_path

def get_input_paths():
    paths = []
    if len(sys.argv) > 1:
        paths.extend(sys.argv[1:])
    if not sys.stdin.isatty():
        paths.extend(line.strip() for line in sys.stdin if line.strip())
    return paths

if __name__ == "__main__":
    input_paths = get_input_paths()
    state = State()
    if input_paths:
        abs_paths = [os.path.abspath(p) for p in input_paths]
        if len(abs_paths) == 1 and os.path.isdir(abs_paths[0]):
            state.root_dir = abs_paths[0]
            state.mode = "NORMAL"
        else:
            state.input_set = abs_paths
            state.mode = "MULTI"
    else:
        state.root_dir = os.getcwd()
        state.mode = "NORMAL"

    main(state)

