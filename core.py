# core.py

import subprocess
from rofi_interface import run_rofi
from rofi_interface import clipboard_mode_menu
from rofi_interface import mode_menu
from utils import get_input_paths
               
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

def edit_files(files, editor="nvim"):
    if not files:
        return
    cmd = ["xterm", "-fa", "DejaVu Sans Mono Book", "-fs", "12", "-e", editor] + files
    subprocess.run(cmd)

