# filters.py
import re
from pathlib import Path
import os
import pathspec # Make sure this is installed: pip install pathspec

# --- Helper functions ---

def matches_filters(path: Path, state) -> bool:
    """
    Checks if a path matches the general filters (dotfiles, regex).
    Note: gitignore filtering is now handled separately before calling this.
    """
    # Exclude '.' and '..' from dotfile check as they are special directory entries
    if not state.include_dotfiles and any(p.startswith('.') for p in path.parts if p != '.' and p != '..'):
        return False
    if state.regex_mode and state.regex_pattern:
        try:
            pattern = re.compile(state.regex_pattern)
            if not pattern.search(str(path)):
                return False
        except re.error:
            # If regex is invalid, we might want to return True (don't filter by regex)
            # or False (always filter out). For now, if invalid, don't filter by regex.
            return True
    return True

def load_gitignore_spec(directory_path: Path):
    """
    Loads a PathSpec object from a .gitignore file in the given directory, if it exists.
    Returns None if no .gitignore file is found.
    """
    gitignore_path = directory_path / '.gitignore'
    # print(f"DEBUG: load_gitignore_spec: Checking for .gitignore at {gitignore_path}") # Debug print
    if gitignore_path.exists():
        # print(f"DEBUG: load_gitignore_spec: .gitignore exists at {gitignore_path}") # Debug print
        with gitignore_path.open('r') as f:
            lines = f.read().splitlines()
        return pathspec.PathSpec.from_lines('gitwildmatch', lines)
    return None

def is_ignored_by_stack(path: Path, active_gitignore_specs: list[tuple[pathspec.PathSpec, Path]]):
    """
    Checks if a path is ignored by any of the provided gitignore specifications in the stack.
    The `active_gitignore_specs` list should contain (PathSpec, base_path) tuples,
    ordered from the outermost directory to the innermost.

    Rules from deeper `.gitignore` files take precedence over shallower ones.
    This is achieved by iterating through the specs from deepest to shallowest.
    """
    if not active_gitignore_specs:
        return False

    # Iterate through specs from deepest to shallowest (reverse order of the list)
    # The first `.gitignore` that provides a definitive match (either ignore or unignore) for the `rel_path` wins.
    for spec, base_path in reversed(active_gitignore_specs):
        if spec is None:
            continue

        try:
            # The path needs to be relative to the base_path of this specific .gitignore file
            rel_path = path.relative_to(base_path)
            if spec.match_file(str(rel_path)):
                return True
        except ValueError:
            # `path` is not under `base_path` for this specific gitignore spec, so it doesn't apply.
            continue
    return False

# --- Main functions with refactored gitignore logic ---
def expand_directories(entries: list[Path], state, current_depth: int,
                       active_gitignore_specs: list[tuple[pathspec.PathSpec, Path]],
                       visited_inodes_for_current_traversal: set) -> list[Path]:
    expanded = []

    for entry in entries:
        try:
            canonical_path = entry.resolve()
            stat_info = canonical_path.stat()
            inode_key = (stat_info.st_dev, stat_info.st_ino)
            if inode_key in visited_inodes_for_current_traversal:
                continue
            visited_inodes_for_current_traversal.add(inode_key)
        except Exception:
            pass

        if state.use_gitignore and is_ignored_by_stack(entry, active_gitignore_specs):
            continue

        expanded.append(entry)

        if state.directory_expansion and entry.is_dir():
            if state.expansion_depth is None or current_depth < state.expansion_depth:
                new_active_gitignore_specs = list(active_gitignore_specs)
                local_gitignore_spec = load_gitignore_spec(entry)
                if local_gitignore_spec:
                    new_active_gitignore_specs.append((local_gitignore_spec, entry))

                try:
                    children = list(entry.iterdir())
                except Exception:
                    children = []

                if not state.include_dotfiles:
                    children = [c for c in children if not c.name.startswith(".")]

                if state.expansion_recursion:
                    expanded.extend(expand_directories(
                        children, state, current_depth + 1, new_active_gitignore_specs,
                        visited_inodes_for_current_traversal
                    ))
                else:
                    filtered_children = []
                    for child in children:
                        if state.use_gitignore and is_ignored_by_stack(child, new_active_gitignore_specs):
                            continue
                        filtered_children.append(child)
                    expanded.extend(filtered_children)

    return expanded

def get_entries(state):
    all_expanded_entries = []
    processed_root_inodes = set()

    for initial_path_root in state.workspace.list():
        if not initial_path_root.exists():
            continue

        try:
            canonical_root = initial_path_root.resolve()
            stat_info = canonical_root.stat()
            root_key = (stat_info.st_dev, stat_info.st_ino)  # Use device + inode
            if root_key in processed_root_inodes:
                print(f"DEBUG: Skipping initial path as its canonical root was already processed: {initial_path_root}")
                continue
            processed_root_inodes.add(root_key)
        except Exception:
            continue

        initial_gitignore_specs = []
        if state.use_gitignore:
            root_spec = load_gitignore_spec(initial_path_root)
            if root_spec:
                initial_gitignore_specs.append((root_spec, initial_path_root))

        visited_inodes_for_this_project = set()  # Start empty, do not pre-add root inode

        current_root_entries = [initial_path_root]

        expanded_for_this_root = expand_directories(
            current_root_entries,
            state,
            current_depth=0,
            active_gitignore_specs=initial_gitignore_specs,
            visited_inodes_for_current_traversal=visited_inodes_for_this_project
        )
        all_expanded_entries.extend(expanded_for_this_root)

    filtered = []
    for e in all_expanded_entries:
        if state.search_dirs_only and not e.is_dir():
            continue
        if state.search_files_only and not e.is_file():
            continue
        if not matches_filters(e, state):
            continue
        filtered.append(e)

    print(f"DEBUG: get_entries: Total filtered entries: {len(filtered)}")
    return filtered
