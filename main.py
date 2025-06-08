#!/usr/bin/env python
# main.py


from utils.utils import get_input_paths
from menu.menu import MenuManager
from state.state import State
from pathlib import Path
from state.workspace import Workspace

def main(state):
    menu_manager = MenuManager(state)
    menu_manager.main_loop()

if __name__ == "__main__":
    input_paths = get_input_paths()
    workspace = Workspace(json_file="workspace_state.json", paths=input_paths, cwd=None)
    state = State(workspace)
    main(state)
