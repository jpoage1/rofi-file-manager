# filesystem.py
import os
import re

def list_directories(base_dir):
    try:
        return [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    except Exception:
        return []

def list_files(base_dir):
    try:
        return [f for f in os.listdir(base_dir) if os.path.isfile(os.path.join(base_dir, f))]
    except Exception:
        return []

def list_dir_recursive(base_path):
    result = []
    for root, dirs, files in os.walk(base_path):
        for name in dirs + files:
            full = os.path.join(root, name)
            rel = os.path.relpath(full, base_path)
            result.append(rel)
    return result

def filter_entries(entries, state):
    if state.regex_mode and state.regex_pattern:
        try:
            regex = re.compile(state.regex_pattern)
            entries = [e for e in entries if regex.search(e)]
        except re.error:
            entries = []
    if not state.include_dotfiles:
        entries = [e for e in entries if not e.startswith(".")]
    return entries

def resolve_path(state, filename):
    if state.mode == "MULTI":
        path = next((p for p in state.input_set if os.path.basename(p) == filename), None)
        if path:
            return os.path.abspath(path)
        return None
    return os.path.abspath(os.path.join(state.root_dir, filename))

def list_directories(base_dir):
    try:
        return [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    except Exception:
        return []

def list_files(base_dir):
    try:
        return [f for f in os.listdir(base_dir) if os.path.isfile(os.path.join(base_dir, f))]
    except Exception:
        return []
