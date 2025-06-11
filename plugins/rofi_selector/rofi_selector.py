# plugins/interface/fzf_interface.py
import subprocess
import shutil
from core.plugin_base import SelectorPlugin

class RofiSelector(SelectorPlugin):
    name = "rofi"

    priority = 10

    @staticmethod
    def available():
        return shutil.which("rofi") is not None

    @staticmethod
    def selector(entries, prompt, multi_select=False, text_input=True):
        cmd = ["rofi", "-dmenu", "-p", prompt]
        if multi_select:
            cmd.append("-multi-select")
        proc = subprocess.run(cmd, input="\n".join(entries), text=True, capture_output=True)
        if proc.returncode != 0:
            return []
        result = proc.stdout.strip()
        return result.splitlines() if multi_select else [result] if result else []
