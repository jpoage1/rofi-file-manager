# plugins/interface/fzf_interface.py
import subprocess
import shutil
from core.plugin_base import SelectorPlugin

class FzfSelector(SelectorPlugin):
    name = "fzf"
    priority = 20

    @staticmethod
    def available():
        return shutil.which("fzf") is not None
    
    @staticmethod
    def selector(entries, prompt, multi_select=False, text_input=True):
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
