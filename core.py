# core.py

import subprocess
               
def filter_file_entries(selection):
    return [item for item in selection if not item.startswith("[") and item != "---"]

def edit_files(files, editor="nvim"):
    if not files:
        return
    cmd = ["xterm", "-fa", "DejaVu Sans Mono Book", "-fs", "12", "-e", editor] + files
    subprocess.run(cmd)

