# In filters/filtering.py
import logging



import re
from pathlib import Path
from filters.gitignore import is_ignored_by_stack

def filter_ignored(entries: list[Path], use_gitignore: bool, gitignore_specs: list[tuple]) -> list[Path]:
    logging.debug(f"filter_ignored: Called with {len(entries)} entries.") # NEW
    if not use_gitignore:
        logging.debug(f"filter_ignored: Skipping .gitignore filtering (disabled).")
        return entries
    result = []
    for e in entries:
        import time
        start = time.perf_counter()
        ignored = is_ignored_by_stack(e, gitignore_specs)
        end = time.perf_counter()
        print(f"is_ignored_by_stack1: Execution time: {end - start:.6f} seconds")

        if not ignored:
            result.append(e)
            logging.debug(f"filter_ignored: KEPT '{e}'") # More precise
        else:
            logging.debug(f"filter_ignored: IGNORED '{e}'") # More precise
    logging.debug(f"filter_ignored: Returning {len(result)} entries.") # NEW
    return result

def matches_filters(path: Path, state) -> bool:
    if not state.include_dotfiles and any(p.startswith('.') for p in path.parts if p not in ('.', '..')):
        print(f"[DEBUG] Skipping dotfile: {path}")
        return False
    pattern = getattr(state, '_compiled_regex', None)
    if state.regex_mode and state.regex_pattern:
        if pattern is None:
            try:
                pattern = re.compile(state.regex_pattern)
            except re.error:
                print(f"[DEBUG] Invalid regex: {state.regex_pattern}")
                return True
            state._compiled_regex = pattern
        if not pattern.search(str(path)):
            print(f"[DEBUG] Regex does not match: {path}")
            return False
    return True

def filter_ignored(entries: list[Path], use_gitignore: bool, gitignore_specs: list[tuple]) -> list[Path]:
    if not use_gitignore:
        print(f"[DEBUG] Skipping .gitignore filtering")
        return entries
    result = []
    for e in entries:
        ignored = is_ignored_by_stack(e, gitignore_specs)
        print(f"[DEBUG] Checking gitignore: {e} -> {'IGNORED' if ignored else 'KEPT'}")
        if not ignored:
            result.append(e)
    return result

def filter_entries(entries: list[Path], state) -> list[Path]:
    logging.debug(f"filter_entries: Called with {len(entries)} entries.")
    filtered = []
    for e in entries:
        if state.search_dirs_only and not e.is_dir():
            print(f"[DEBUG] Skipping non-dir: {e}")
            continue
        if state.search_files_only and not e.is_file():
            print(f"[DEBUG] Skipping non-file: {e}")
            continue
        if not matches_filters(e, state):
            print(f"[DEBUG] Filtered out: {e}")
            continue
        filtered.append(e)
        logging.debug(f"filter_entries: INCLUDED (final list) '{e}'") # Most precise
    logging.debug(f"filter_entries: Returning {len(filtered)} entries.") # NEW
    return filtered
