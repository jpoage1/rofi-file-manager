# plugins/interface/fzf_interface.py
import subprocess

name = "rofi"

def run_rofi(entries, prompt, multi_select=False, text_input=True):
    cmd = ["rofi", "-dmenu", "-p", prompt]
    if multi_select:
        cmd.append("-multi-select")
    proc = subprocess.run(cmd, input="\n".join(entries), text=True, capture_output=True)
    if proc.returncode != 0:
        return []
    result = proc.stdout.strip()
    return result.splitlines() if multi_select else [result] if result else []

def selector(entries, prompt, multi_select, text_input):
    return run_rofi(entries, prompt, multi_select, text_input)
