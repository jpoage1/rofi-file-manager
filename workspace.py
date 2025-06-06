# workspace.py

from pathlib import Path
class Workspace:
    def __init__(self, label="⟪Workspace⟫"):
        self.label = label
        self.files = set()

    def add(self, root_dir, entries):
        root = Path(root_dir)
        for entry in entries:
            full_path = root / entry
            if full_path.exists():
                self.files.add(full_path)

    def remove(self, entries):
        for entry in entries:
            self.files.discard(entry)

    def list(self):
        return sorted(self.files)

    def reset(self):
        self.files.clear()
