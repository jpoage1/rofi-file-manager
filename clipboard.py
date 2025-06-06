import subprocess
import pyperclip
def read_file_safe(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception:
        return ""

class Clipboard:
    def __init__(self):
        self.queue = []

    def add_files(self, files):
        for f in files:
            if f and f not in self.queue:
                self.queue.append(f)

    def remove_files(self, files):
        for f in files:
            if f in self.queue:
                self.queue.remove(f)

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
