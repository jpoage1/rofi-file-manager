#!/usr/bin/env python
# main.py


from utils import get_input_paths
from menu import MenuManager
from state import State
from pathlib import Path
from workspace import Workspace

def main(state):
    menu_manager = MenuManager(state)
    menu_manager.main_loop()

if __name__ == "__main__":
    input_paths = get_input_paths()
    workspace = Workspace(json_file="workspace_state.json", paths=input_paths, cwd=None)
    state = State(workspace)
    main(state)
