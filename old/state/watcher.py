# state/watcher.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from pathlib import Path

class CacheUpdater(FileSystemEventHandler):
    def __init__(self, state):
        self.state = state

    def on_modified(self, event):
        self._update(event.src_path)

    def on_created(self, event):
        with self.state.cache_lock:
            self.state.cache.add(event.src_path)
            self.state._save_cache()

    def on_deleted(self, event):
        with self.state.cache_lock:
            self.state.cache.discard(event.src_path)
            self.state._save_cache()

    def _update(self, path):
        try:
            stat = os.stat(path)
            with self.state.lock:
                self.state.entries[path] = {'inode': stat.st_ino, 'mtime': stat.st_mtime}
                self.state.save()
        except FileNotFoundError:
            pass
    def _save_cache(self):
        import json
        with self.cache_lock:
            Path(self.cache_file).write_text(json.dumps(sorted(self.cache)))
