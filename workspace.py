# workspace.py
import json
import sys
import fcntl
from pathlib import Path

class Workspace:
    def __init__(self, source):
        if isinstance(source, (str, Path)):
            self.json_path = Path(source)
            self.files = set()
            self.paths = []
            self.load()
        elif isinstance(source, list):
            self.json_path = None
            self.paths = [Path(p) for p in source]
            self.files = set(Path(p).resolve() for p in source if Path(p).exists())
        else:
            raise TypeError("Expected str, Path, or list of paths.")

    def load(self):
        if not self.json_path.exists():
            self.paths = []
            self.files = set()
            return
        with open(self.json_path, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            data = json.load(f)
            fcntl.flock(f, fcntl.LOCK_UN)
        self.paths = [Path(p) for p in data.get("paths", [])]
        self.files = set(Path(f).resolve() for f in data.get("files", []))

    def save(self):
        if not self.json_path:
            return  # Skip save if no persistence
        data = {
            "paths": [str(p) for p in self.paths],
            "files": [str(f) for f in self.files],
        }
        tmp_path = self.json_path.with_suffix(".tmp")
        with open(tmp_path, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            json.dump(data, f, indent=2)
            f.flush()
            fcntl.flock(f, fcntl.LOCK_UN)
        tmp_path.rename(self.json_path)

    def add(self, root_dir, entries):
        root = Path(root_dir)
        for entry in entries:
            full_path = root / entry
            if full_path.exists():
                self.files.add(full_path.resolve())
        self.save()

    def remove(self, entries):
        for entry in entries:
            p = Path(entry) if not isinstance(entry, Path) else entry
            self.files.discard(p.resolve())
        self.save()

    def list(self):
        return sorted(self.files)

    def reset(self):
        self.files.clear()
        self.save()
