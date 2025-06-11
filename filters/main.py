# Path: filters/main.py
# Last Modified: 2025-06-11

# filters/main.py
from pathlib import Path
from filters.gitignore import update_gitignore_specs, is_ignored_by_stack, load_gitignore_spec
from filters.path_utils import resolve_path_and_inode, list_directory_children
from filters.filtering import filter_ignored, filter_entries
import logging
def resolve_root_path(path):
    try:
        canonical_root = path.resolve()
        stat_info = canonical_root.stat()
        return canonical_root, (stat_info.st_dev, stat_info.st_ino)
    except Exception:
        return None, None

def get_gitignore_specs(path: Path, use_gitignore: bool):
    if not use_gitignore:
        return []
    root_spec = load_gitignore_spec(path)
    return [(root_spec, path)] if root_spec else []

# # @functools.lru_cache(maxsize=None)
# def resolve_inode(path_str):
#     path = Path(path_str)
#     return resolve_path_and_inode(path)

def fast_list_children(entry):
    import os

    try:
        with os.scandir(entry) as it:
            return [Path(e.path) for e in it if e.name[0] != '.']
    except Exception:
        return []


def expand_directories(entries: list[Path], state, current_depth: int,
                       active_gitignore_specs: list[tuple],
                       visited_inodes_for_current_traversal: set) -> list[Path]:
    logging.debug(f"expand_directories: Called (depth {current_depth}) with {len(entries)} input entries.") # NEW
    expanded = []
    for entry in entries:
        
        # import time
        # start = time.perf_counter()
        canonical_path, inode_key = resolve_path_and_inode(entry) # This is faster
        # end = time.perf_counter()
        # print(f"canonical_path, inode_key = resolve_path_and_inode(entry): Execution time: {end - start:.6f} seconds")



        # import time
        # start = time.perf_counter()
        # canonical_path, inode_key = resolve_inode(str(entry))
        # end = time.perf_counter()
        # print(f"canonical_path, inode_key = resolve_inode(str(entry)): Execution time: {end - start:.6f} seconds")


        if not canonical_path or not inode_key:
            logging.debug(f"expand_directories: Skipping invalid path/inode {entry}") # NEW
            continue
        if inode_key in visited_inodes_for_current_traversal:
            logging.debug(f"expand_directories: Skipping already visited inode {entry}") # NEW
            continue
        visited_inodes_for_current_traversal.add(inode_key)

        is_current_entry_ignored = state.use_gitignore and is_ignored_by_stack(entry, active_gitignore_specs)
        if is_current_entry_ignored:
            logging.debug(f"expand_directories: IGNORED '{entry}' at current depth, skipping.") # More precise
            continue

        expanded.append(entry) # Add to list ONLY if not ignored at this point
        logging.debug(f"expand_directories: ADDED '{entry}' to expanded list.") # NEW

        if not (state.directory_expansion and entry.is_dir()):
            logging.debug(f"expand_directories: Not a directory for expansion or expansion off: {entry}") # NEW
            continue

        if state.expansion_depth is not None and current_depth >= state.expansion_depth:
            logging.debug(f"expand_directories: Max depth reached for {entry}") # NEW
            continue

        new_active_gitignore_specs = update_gitignore_specs(entry, active_gitignore_specs)
        # children = list_directory_children(entry, state.include_dotfiles)
        # logging.debug(f"expand_directories: Listing children for {entry}. Found {len(children)}.") # NEW

        # import time
        # start = time.perf_counter()
        # children = list_directory_children(entry, state.include_dotfiles)
        # end = time.perf_counter()
        # print(f"children1: Execution time: {end - start:.6f} seconds")


        # import time
        # start = time.perf_counter()
        # This is faster
        if state.include_dotfiles:
            children = list_directory_children(entry, True)
        else:
            children = fast_list_children(entry)
        # end = time.perf_counter()
        # print(f"children2: Execution time: {end - start:.6f} seconds")

        if state.expansion_recursion: 
            logging.debug(f"expand_directories: Recursing into children of {entry}") # NEW
            expanded.extend(expand_directories(
                children, state, current_depth + 1, new_active_gitignore_specs,
                visited_inodes_for_current_traversal
            ))
        else:
            logging.debug(f"expand_directories: Filtering children of {entry} (non-recursive)") # NEW
            filtered_children = filter_ignored(children, state.use_gitignore, new_active_gitignore_specs)
            expanded.extend(filtered_children)

    logging.debug(f"expand_directories: Returning {len(expanded)} entries (depth {current_depth}).") # NEW
    return expanded

def get_entries(state):
    logging.debug(f"get_entries: Starting entry discovery.")
    workspace_roots = list(state.workspace.list())
    logging.debug(f"get_entries: Workspace roots: {workspace_roots}")

    all_expanded_entries = []
    processed_root_inodes = set()

    # Determine the project root for .gitignore purposes.
    # This is where your primary .gitignore file lives.
    # Assuming your main .gitignore is always in the directory where editor.sh is run (Path.cwd()).
    # If your .gitignore is in a parent directory of CWD (e.g., in a monorepo setup),
    # this path would need to be determined differently (e.g., find_git_repo_root()).
    project_root_for_gitignore = Path.cwd() # Or a more robust way to find repo root

    # Load the global gitignore specs ONCE for the entire process
    global_gitignore_specs = get_gitignore_specs(project_root_for_gitignore, state.use_gitignore)
    logging.debug(f"get_entries: Loaded global gitignore specs from '{project_root_for_gitignore}': {len(global_gitignore_specs)} specs.")

    for initial_path_root in workspace_roots:
        logging.debug(f"get_entries: Processing root '{initial_path_root}'")

        canonical_path, inode_key = resolve_path_and_inode(initial_path_root)
        if not canonical_path or not inode_key:
            logging.debug(f"get_entries: Skipping invalid initial root path: {initial_path_root}")
            continue
        if inode_key in processed_root_inodes:
            logging.debug(f"get_entries: Skipping already processed root inode: {initial_path_root}")
            continue
        processed_root_inodes.add(inode_key)

        # Check if the initial_path_root itself is ignored by the global gitignore.
        # This is important for roots like '.venv' if they were in workspace.list()
        if state.use_gitignore and is_ignored_by_stack(initial_path_root, global_gitignore_specs):
            logging.debug(f"get_entries: Initial root '{initial_path_root}' ignored by global .gitignore, skipping its expansion.")
            continue

        visited_inodes_for_this_project = set() # Unique per traversal path
        current_root_entries = [initial_path_root]

        expanded_for_this_root = expand_directories(
            current_root_entries,
            state,
            current_depth=0,
            # Pass the global gitignore specs to ALL expansions, regardless of depth or origin
            active_gitignore_specs=global_gitignore_specs,
            visited_inodes_for_current_traversal=visited_inodes_for_this_project
        )
        logging.debug(f"get_entries: Expanded {len(expanded_for_this_root)} entries for root '{initial_path_root}'.")
        all_expanded_entries.extend(expanded_for_this_root)

    logging.debug(f"get_entries: All roots processed. Total {len(all_expanded_entries)} entries before final filter.")

    # This is the FINAL filter call
    filtered = filter_entries(all_expanded_entries, state)
    logging.debug(f"get_entries: Final list contains {len(filtered)} entries.")
    return filtered

def query_from_cache(cache, state):
    logging.debug(f"query_from_cache: Filtering {len(cache)} cached entries.")
    filtered = filter_entries(cache, state)
    logging.debug(f"query_from_cache: Filtered down to {len(filtered)} entries.")
    return filtered
