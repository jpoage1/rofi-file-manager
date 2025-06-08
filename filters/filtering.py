import re
from pathlib import Path
from filters.gitignore import is_ignored_by_stack

def matches_filters(path: Path, state) -> bool:
    if not state.include_dotfiles and any(p.startswith('.') for p in path.parts if p not in ('.', '..')):
        return False
    pattern = getattr(state, '_compiled_regex', None)
    if state.regex_mode and state.regex_pattern:
        if pattern is None:
            try:
                pattern = re.compile(state.regex_pattern)
            except re.error:
                return True
            state._compiled_regex = pattern
        if not pattern.search(str(path)):
            return False
    return True

def filter_ignored(entries: list[Path], use_gitignore: bool, gitignore_specs: list[tuple]) -> list[Path]:
    if not use_gitignore:
        return entries
    return [e for e in entries if not is_ignored_by_stack(e, gitignore_specs)]

def filter_entries(entries: list[Path], state) -> list[Path]:
    filtered = []
    for e in entries:
        if state.search_dirs_only and not e.is_dir():
            continue
        if state.search_files_only and not e.is_file():
            continue
        if not matches_filters(e, state):
            continue
        filtered.append(e)
    return filtered
