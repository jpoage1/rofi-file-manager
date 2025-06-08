# workspace.py
import json
import fcntl
from pathlib import Path

class Workspace:
    def __init__(self, json_file=None, paths=[], cwd=None):
        self.cwd = Path(cwd) if cwd else Path.cwd()
        self.json_file = Path(json_file if json_file else "workspaces.json")
        self.paths = set(Path(p) for p in paths if Path(p).exists())
        self.load()

    def load(self):
        if not self.json_file.exists():
            return
        with open(self.json_file, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            data = json.load(f)
            fcntl.flock(f, fcntl.LOCK_UN)
        self.paths.update(Path(p) for p in data.get("paths", []))
        
    def save(self):
        tmp_path = self.json_file.with_suffix(".tmp")
        with open(tmp_path, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            json.dump({"paths": [str(p) for p in self.paths]}, f, indent=2)
            f.flush()
            fcntl.flock(f, fcntl.LOCK_UN)
        tmp_path.rename(self.json_file)

    def add(self, entries, root_dir=None):
        root = Path(root_dir) if root_dir else self.cwd
        for entry in entries:
            full_path = root / entry
            if full_path.exists():
                self.paths.add(full_path)
        self.save()

    def remove(self, entries, root_dir=None):
        root = Path(root_dir) if root_dir else self.cwd
        for entry in entries:
            full_path = (root / entry).resolve()
            self.paths.discard(full_path)
        self.save()

    def list(self):
        return sorted(self.paths)

    def list_workspace_files(self):
        return sorted(p for p in self.paths if p.is_file())

    def list_directories(self):
        return sorted(p for p in self.paths if p.is_dir())
    
    def expand_directories():
        pass

    def reset(self):
        self.paths.clear()
        self.save() 
