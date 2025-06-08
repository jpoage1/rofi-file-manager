#!/usr/bin/env python
# main.py

import argparse

from utils.utils import get_input_paths
from menu.menu import MenuManager
from state.state import State
from pathlib import Path
from state.workspace import Workspace

def main(state):
    menu_manager = MenuManager(state)
    menu_manager.main_loop()


def get_args():
    parser = argparse.ArgumentParser(description="Manage workspace state")
    parser.add_argument("--workspace-file", default="workspace.json")
    parser.add_argument("--cwd", default=None)
    parser.add_argument("paths", nargs="*")
    return parser.parse_args()

if __name__ == "__main__":
    args = get_args()
    workspace = Workspace(
        json_file=args.workspace_file,
        paths=args.paths,
        cwd=args.cwd
    )
    state = State(workspace)
    main(state)
