# workspace.py

from pathlib import Path
class Workspace:
    def __init__(self, paths):
        self.files = set()
        self.paths = [Path(p) if not isinstance(p, Path) else p for p in paths]

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

    def list(self):
        for path in self.paths:
            yield from path.glob("**/*")  # or customized logic
