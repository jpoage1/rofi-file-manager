# rofi_interface.py
import subprocess

from filesystem import resolve_path

def run_rofi(entries, prompt, multi_select=False):
    cmd = ["rofi", "-dmenu", "-p", prompt]
    if multi_select:
        cmd.append("-multi-select")
    proc = subprocess.run(cmd, input="\n".join(entries), text=True, capture_output=True)
    if proc.returncode != 0:
        return []
    result = proc.stdout.strip()
    if multi_select:
        return result.splitlines() if result else []
    return [result] if result else []

def mode_menu(state):
    modes = ["Edit", "Traverse", "Execute", "Clipboard"]
    choice = run_rofi(modes, f"Change mode (current: {state.current_mode})", False)
    if choice:
        state.current_mode = choice[0]

def toggle_option(state, option_name):
    current = getattr(state, option_name)
    setattr(state, option_name, not current)
