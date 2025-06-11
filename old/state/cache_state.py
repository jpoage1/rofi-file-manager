# state/cache_state.py
import json
import threading
from pathlib import Path
from typing import Dict, Set
from .watcher import start_file_watcher
from ...state.scanner import validate_cache_against_fs
from .serializer import load_cache_file, save_cache_file

class CacheState:
    def __init__(self, cache_file: Path):
        self.cache_file = cache_file
        self.entries = {}  ## type: Dict[str, Dict] (e.g., {'/some/file': {'inode': int, 'mtime': float}})
        self.lock = threading.RLock()
        self.watched_paths = set()  # type: Set[Path]

    def load(self):
        data = load_cache_file(self.cache_file)
        if data:
            self.entries = data

    def save(self):
        with self.lock:
            save_cache_file(self.cache_file, self.entries)

    def set_state(self, new_roots: Set[Path]):
        self.load()

        # Watchdog and background scan will mutate this
        self.watched_paths = new_roots

        for root in new_roots:
            start_file_watcher(self, root)

        thread = threading.Thread(target=self._background_validation, daemon=True)
        thread.start()

    def _background_validation(self):
        updated = validate_cache_against_fs(self.entries, self.watched_paths)
        if updated:
            self.save()
    def get_entries(self):
        from  filters.filtering import filter_entries
        with self.cache_lock:
            entries = [Path(p) for p in self.cache]
        return filter_entries(entries, self)
