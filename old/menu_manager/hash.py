# menu_manager/hash.py
import hashlib

def hash_file(path):
    hasher = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (OSError, IOError):
        return None
import json
from pathlib import Path

class HashCache:
    def __init__(self, cache_file):
        self.cache_file = Path(cache_file)
        self.map = self._load()

    def _load(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def save(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.map, f, indent=2)

    def has_changed(self, path):
        h = hash_file(path)
        if h is None:
            return False
        old = self.map.get(path)
        if old == h:
            return False
        self.map[path] = h
        return True
