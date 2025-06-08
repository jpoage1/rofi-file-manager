# In filters/filtering.py
import re
from pathlib import Path
from filters.gitignore import is_ignored_by_stack # Make sure this import is here

def matches_filters(path: Path, state) -> bool:
    # ... (no change needed here for now)
    pass

def filter_ignored(entries: list[Path], use_gitignore: bool, gitignore_specs: list[tuple]) -> list[Path]:
    print(f"[DEBUG] filter_ignored: Called with {len(entries)} entries.") # NEW
    if not use_gitignore:
        print(f"[DEBUG] filter_ignored: Skipping .gitignore filtering (disabled).")
        return entries
    result = []
    for e in entries:
        ignored = is_ignored_by_stack(e, gitignore_specs)
        if not ignored:
            result.append(e)
            print(f"[DEBUG] filter_ignored: KEPT '{e}'") # More precise
        else:
            print(f"[DEBUG] filter_ignored: IGNORED '{e}'") # More precise
    print(f"[DEBUG] filter_ignored: Returning {len(result)} entries.") # NEW
    return result

def filter_entries(entries: list[Path], state) -> list[Path]:
    print(f"[DEBUG] filter_entries: Called with {len(entries)} entries.") # NEW
    filtered = []
    for e in entries:
        # ... (your existing filtering logic)
        # Assuming you've already made this change:
        # if not matches_filters(e, state):
        #     print(f"[DEBUG] Filtered out by other rules: {e}")
        #     continue
        filtered.append(e)
        print(f"[DEBUG] filter_entries: INCLUDED (final list) '{e}'") # Most precise
    print(f"[DEBUG] filter_entries: Returning {len(filtered)} entries.") # NEW
    return filtered
