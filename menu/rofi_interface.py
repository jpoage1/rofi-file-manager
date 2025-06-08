# rofi_interface.py
import subprocess

def run_rofi(entries, prompt, multi_select=False, text_input=True):
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



def toggle_option(state, option_name):
    current = getattr(state, option_name)
    setattr(state, option_name, not current)
