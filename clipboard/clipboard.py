import pyperclip
from pathlib import Path
def read_file_safe(path: Path) -> str:
    try:
        return path.read_text()
    except Exception:
        return ""
class Clipboard:
    def __init__(self):
        self.queue = []

    def add_files(self, files):
        for f in files:
            p = Path(f)
            if p.is_file() and p not in self.queue:
                self.queue.append(p)

    def remove_files(self, files):
        for f in files:
            p = Path(f)
            if p in self.queue:
                self.queue.remove(p)

    def clear(self):
        self.queue.clear()

    def commit(self):
        content = ''.join(read_file_safe(f) for f in self.queue)
        try:
            pyperclip.copy(content)
        except pyperclip.PyperclipException:
            pass  # Optionally log or handle failure
        self.clear()

    def snapshot(self):
        return list(self.queue)

    def restore(self, snapshot):
        self.queue = list(snapshot)

    def get_files(self):
        return list(self.queue)
