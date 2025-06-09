import os
from pathlib import Path
from typing import Dict, Set

def validate_cache_against_fs(cache: Set[str], roots: Set[Path]) -> bool:
    changed = False
    current_entries = set()

    for root in roots:
        for dirpath, _, filenames in os.walk(root):
            for name in filenames:
                full_path = str(Path(dirpath) / name)
                current_entries.add(full_path)

    if current_entries != cache:
        cache.clear()
        cache.update(current_entries)
        changed = True

    return changed
