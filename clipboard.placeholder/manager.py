# clipboard/manager.py
import os
import subprocess
from typing import List

class ClipboardManager:
    def __init__(self):
        self.clipboard_queue = []

    def add(self, path):
        abs_path = os.path.abspath(path)
        if abs_path not in self.clipboard_queue:
            self.clipboard_queue.append(abs_path)

    def remove(self, path):
        abs_path = os.path.abspath(path)
        if abs_path in self.clipboard_queue:
            self.clipboard_queue.remove(abs_path)

    def clear(self):
        self.clipboard_queue.clear()

    def get_all(self):
        return list(self.clipboard_queue)

    def commit(self):
        content = ''.join(self._read_file_safe(f) for f in self.clipboard_queue)
        if content:
            subprocess.run(["xclip", "-selection", "clipboard"], input=content, text=True)
        self.clear()

    def _read_file_safe(self, path):
        try:
            with open(path, "r") as f:
                return f.read()
        except Exception:
            return ""
