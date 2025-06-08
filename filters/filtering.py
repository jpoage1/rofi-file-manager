# In filters/filtering.py
import re
from pathlib import Path
from filters.gitignore import is_ignored_by_stack # Make sure this import is here
import logging

def matches_filters(path: Path, state) -> bool:
    # ... (no change needed here for now)
    pass

def filter_ignored(entries: list[Path], use_gitignore: bool, gitignore_specs: list[tuple]) -> list[Path]:
    logging.debug(f"filter_ignored: Called with {len(entries)} entries.") # NEW
    if not use_gitignore:
        logging.debug(f"filter_ignored: Skipping .gitignore filtering (disabled).")
        return entries
    result = []
    for e in entries:
        ignored = is_ignored_by_stack(e, gitignore_specs)
        if not ignored:
            result.append(e)
            logging.debug(f"filter_ignored: KEPT '{e}'") # More precise
        else:
            logging.debug(f"filter_ignored: IGNORED '{e}'") # More precise
    logging.debug(f"filter_ignored: Returning {len(result)} entries.") # NEW
    return result

def filter_entries(entries: list[Path], state) -> list[Path]:
    logging.debug(f"filter_entries: Called with {len(entries)} entries.") # NEW
    filtered = []
    for e in entries:
        # ... (your existing filtering logic)
        # Assuming you've already made this change:
        # if not matches_filters(e, state):
        #     logging.debug(f"Filtered out by other rules: {e}")
        #     continue
        filtered.append(e)
        logging.debug(f"filter_entries: INCLUDED (final list) '{e}'") # Most precise
    logging.debug(f"filter_entries: Returning {len(filtered)} entries.") # NEW
    return filtered
