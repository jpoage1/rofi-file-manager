#!/usr/bin/env python
# main.py


from utils import get_input_paths
from menu import MenuManager
from state import State
from pathlib import Path

def main(state):
    menu_manager = MenuManager(state)
    menu_manager.main_loop()

if __name__ == "__main__":
    input_paths = get_input_paths()

    state = State()
    state = State.load_from_file("workspace_state.json")
    state.init_workspace()

    if input_paths:
        abs_paths = [Path(p).resolve() for p in input_paths]
        state.input_set = [str(p) for p in abs_paths]
    else:
        state.root_dir = str(Path.cwd())
    state.init_workspace()
    main(state)
