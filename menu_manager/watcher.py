# watcher.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from pathlib import Path

class CacheUpdater(FileSystemEventHandler):
    def __init__(self, cache):
        self.cache = cache

    def on_created(self, event):
        path = Path(event.src_path).resolve()
        if path.is_file() or path.is_dir():
            self.cache.add(str(path))

    def on_deleted(self, event):
        path = Path(event.src_path).resolve()
        self.cache.discard(str(path))

    def on_moved(self, event):
        old_path = Path(event.src_path).resolve()
        new_path = Path(event.dest_path).resolve()
        self.cache.discard(str(old_path))
        self.cache.add(str(new_path))

