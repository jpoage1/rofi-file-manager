# plugins/interface/fzf_interface.py
import subprocess

name = "fzf"

def run_fzf(entries, prompt, multi_select=False, text_input=True):
    cmd = ["fzf", "--prompt", prompt + ": "]
    if multi_select:
        cmd.append("--multi")
    if not text_input:
        cmd.append("--no-sort")
    proc = subprocess.run(cmd, input="\n".join(entries), text=True, capture_output=True)
    if proc.returncode != 0:
        return []
    result = proc.stdout.strip()
    return result.splitlines() if multi_select else [result] if result else []


def selector(entries, prompt, multi_select, text_input):
    return run_fzf(entries, prompt, multi_select, text_input)
