# core/utils.py

import subprocess
               
def edit_files(files, editor="nvim"):
    if not files:
        return
    cmd = ["xterm", "-fa", "DejaVu Sans Mono Book", "-fs", "12", "-e", editor] + files
    subprocess.run(cmd)

