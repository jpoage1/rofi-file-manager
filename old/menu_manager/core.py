# Path: old/menu_manager/core.py
# Last Modified: 2025-06-11

# core/core.py

import subprocess
               
def filter_file_entries(selection):
    return [item for item in selection if not item.startswith("[") and item != "---"]

def edit_files(files, editor="nvim"):
    if not files:
        return
    cmd = ["xterm", "-fa", "DejaVu Sans Mono Book", "-fs", "12", "-e", editor] + files
    subprocess.run(cmd)

