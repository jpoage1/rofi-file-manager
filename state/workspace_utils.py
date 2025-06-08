# workspace_utils.py
from core.filters import matches_filters
from filesystem.tree_utils import expand_paths

def get_filtered_workspace_paths(state):
    raw_paths = state.workspace.list()
    filtered = [p for p in raw_paths if matches_filters(p, state)]
    expanded = expand_paths(filtered, state)
    return [p for p in expanded if matches_filters(p, state)]
