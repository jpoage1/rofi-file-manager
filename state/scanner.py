# state/scanner.py
import os
from pathlib import Path
from typing import Dict, Set

def validate_cache_against_fs(cache: Set[str], dirs: Set[Path], files: Set[Path]) -> bool:
    changed = False
    current_entries = set()

    for directory in dirs:
        for dirpath, _, filenames in os.walk(directory):
            for name in filenames:
                full_path = str(Path(dirpath) / name)
                current_entries.add(full_path)

    for file_path in files:
        if file_path.is_file():
            current_entries.add(str(file_path))

    if current_entries != cache:
        cache.clear()
        sorted_entries = sorted(current_entries)
        cache.update(sorted_entries)
        changed = True

    return changed

