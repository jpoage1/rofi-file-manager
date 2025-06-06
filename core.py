# core.py
#!/usr/bin/env python3

import os
import re
import subprocess
from filesystem import list_directories
from filesystem import list_files
from rofi_interface import run_rofi
from filesystem import resolve_path
from rofi_interface import clipboard_mode_menu
from rofi_interface import mode_menu
from utils import get_input_paths
from menu import MenuManager
from state import State


def get_entries(state):
    if state.mode == "MULTI":
        entries = [os.path.basename(p) for p in state.input_set]
        if not state.include_dotfiles:
            entries = [e for e in entries if not e.startswith(".")]
        if state.regex_mode and state.regex_pattern:
            regex = re.compile(state.regex_pattern)
            entries = [e for e in entries if regex.search(e)]
        return entries

    base = state.root_dir
    if not base:
        return []

    if state.search_dirs_only:
        entries = list_directories(base)
    elif state.search_files_only:
        entries = list_files(base)
    else:
        entries = os.listdir(base)

    entries = filter_entries(entries, state)

    return entries

def filter_entries(entries, state):
    if state.regex_mode and state.regex_pattern:
        try:
            regex = re.compile(state.regex_pattern)
            entries = [e for e in entries if regex.search(e)]
        except re.error:
            entries = []
    if not state.include_dotfiles:
        entries = [e for e in entries if not e.startswith(".")]
    return entries

def handle_special_options(state, selection):
    from rofi_interface import toggle_menu
    for item in selection:
        if item == "[Exit]":
            exit(0)
        elif item == "[Toggle Search Options]":
            toggle_menu(state)
            return True
        elif item == "[Change CWD]":
            cwd_menu(state)
            return True
        elif item.startswith("[Change Mode:"):
            mode_menu(state)
            return True
        elif item == "[Reset Workspace]":
            reset_to_files(state)
            return True
    return False



def filter_file_entries(selection):
    return [item for item in selection if not item.startswith("[") and item != "---"]


def dispatch_mode_action(state, resolved):
    if state.current_mode == "Edit":
        edit_files(resolved)
    elif state.current_mode == "Execute":
        for path in resolved:
            subprocess.run(["bash", path])
    elif state.current_mode == "Clipboard":
        state.clipboard.add_files(resolved)
        clipboard_mode_menu(state)
    elif state.current_mode == "Traverse":
        pass  # Placeholder for traversal logic

def reset_to_files(state):
    input_paths = get_input_paths()
    abs_paths = [os.path.abspath(p) for p in input_paths] if input_paths else []
    if len(abs_paths) == 1 and os.path.isdir(abs_paths[0]):
        state.root_dir = abs_paths[0]
        state.mode = "NORMAL"
    elif abs_paths:
        state.input_set = abs_paths
        state.mode = "MULTI"
    else:
        state.root_dir = os.getcwd()
        state.mode = "NORMAL"

def interpret_main_menu(paths, state):
    for path in paths:
        if os.path.isdir(path):
            entries = [os.path.join(path, e) for e in os.listdir(path)]
        else:
            entries = [path]

        selection = run_rofi(entries, "Select file to edit", True)
        if not selection:
            continue

        if state.current_mode == "Edit":
            edit_files(selection)
        elif state.current_mode == "Execute":
            for f in selection:
                subprocess.run(["bash", f])
        elif state.current_mode == "Clipboard":
            state.clipboard.add_files(selection)
            clipboard_mode_menu(state)

def edit_files(files, editor="nvim"):
    if not files:
        return
    cmd = ["xterm", "-fa", "DejaVu Sans Mono Book", "-fs", "12", "-e", editor] + files
    subprocess.run(cmd)

def cwd_menu(state):
    dirs = ["/", os.path.expandvars("$HOME"), "/some/custom/dir"]
    if state.mode == "MULTI":
        dirs.insert(0, f"[{state.workspace.label}]")
    selected = run_rofi(dirs, "Change working directory", False)
    if selected:
        choice = selected[0]
        if state.mode == "MULTI" and choice == f"[{state.workspace.label}]":
            state.workspace.reset()
        else:
            new_dir = os.path.expandvars(choice)
            if os.path.isdir(new_dir):
                state.root_dir = new_dir
                state.mode = "NORMAL"

def main(state):
    menu_manager = MenuManager(state)
    menu_manager.main_loop()

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

