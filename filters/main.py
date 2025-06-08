from pathlib import Path
from filters.gitignore import update_gitignore_specs, is_ignored_by_stack, load_gitignore_spec
from filters.path_utils import resolve_path_and_inode, list_directory_children
from filters.filtering import filter_ignored, filter_entries

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

def expand_directories(entries: list[Path], state, current_depth: int,
                       active_gitignore_specs: list[tuple],
                       visited_inodes_for_current_traversal: set) -> list[Path]:
    expanded = []
    for entry in entries:
        canonical_path, inode_key = resolve_path_and_inode(entry)
        if not canonical_path or not inode_key:
            continue
        if inode_key in visited_inodes_for_current_traversal:
            continue
        visited_inodes_for_current_traversal.add(inode_key)

        if state.use_gitignore and is_ignored_by_stack(entry, active_gitignore_specs):
            continue

        expanded.append(entry)

        if not (state.directory_expansion and entry.is_dir()):
            continue

        if state.expansion_depth is not None and current_depth >= state.expansion_depth:
            continue

        new_active_gitignore_specs = update_gitignore_specs(entry, active_gitignore_specs)
        children = list_directory_children(entry, state.include_dotfiles)

        if state.expansion_recursion:
            expanded.extend(expand_directories(
                children, state, current_depth + 1, new_active_gitignore_specs,
                visited_inodes_for_current_traversal
            ))
        else:
            filtered_children = filter_ignored(children, state.use_gitignore, new_active_gitignore_specs)
            expanded.extend(filtered_children)

    return expanded

def get_entries(state):
    all_expanded_entries = []
    processed_root_inodes = set()

    for initial_path_root in state.workspace.list():
        if not initial_path_root.exists():
            continue

        canonical_root, root_key = resolve_root_path(initial_path_root)
        if not canonical_root or not root_key:
            continue
        if root_key in processed_root_inodes:
            continue
        processed_root_inodes.add(root_key)

        initial_gitignore_specs = get_gitignore_specs(initial_path_root, state.use_gitignore)

        visited_inodes_for_this_project = set()

        current_root_entries = [initial_path_root]

        expanded_for_this_root = expand_directories(
            current_root_entries,
            state,
            current_depth=0,
            active_gitignore_specs=initial_gitignore_specs,
            visited_inodes_for_current_traversal=visited_inodes_for_this_project
        )
        all_expanded_entries.extend(expanded_for_this_root)

    filtered = filter_entries(all_expanded_entries, state)
    return filtered
