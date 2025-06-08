#!/usr/bin/env python
# main.py

import argparse

from utils.utils import get_input_paths
from menu_manager import MenuManager
from state.state import State
from pathlib import Path
from state.workspace import Workspace
import logging

def main(state):
    pass

def get_args():
    parser = argparse.ArgumentParser(description="Manage workspace state")
    parser.add_argument("--workspace-file", default="workspace.json")
    parser.add_argument("--cwd", default=None)
    parser.add_argument("--interface", default=None)
    parser.add_argument("paths", nargs="*")
    return parser.parse_args()

if __name__ == "__main__":
    args = get_args()
    workspace = Workspace(
        json_file=args.workspace_file,
        paths=args.paths,
        cwd=args.cwd
    )
    state = State(workspace, interface=args.interface)
    workspace.setState(state)

    # Initial auto-save check happens after workspace.setState(state)
    # This also handles the case where auto-save was ON from a previous session AND we are dirty.
    if state.is_dirty and state.auto_save_enabled:
        logging.info("[INFO] Performing initial auto-save due to dirty state and auto-save being enabled.")
        state.autoSave(state.workspace.save) # This will save and clear is_dirty

    menu_manager = MenuManager(state, args.interface)
    menu_manager.main_loop()
