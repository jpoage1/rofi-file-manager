# workspace.py
import os
class Workspace:
    def __init__(self, label="Workspace"):
        self.label = label
        self.files = set()

    def add(self, root_dir, entries):
        for entry in entries:
            full_path = os.path.join(root_dir, entry)
            if os.path.exists(full_path):
                self.files.add(full_path)

    def remove(self, entries):
        for entry in entries:
            self.files.discard(entry)

    def list(self):
        return sorted(self.files)

    def reset(self):
        self.files.clear()
