# filters/gitignore.py
import pathspec
from pathlib import Path
import logging
def load_gitignore_spec(directory_path: Path):
    gitignore_path = directory_path / '.gitignore'
    if gitignore_path.exists():
        with gitignore_path.open('r') as f:
            lines = f.read().splitlines()
        return pathspec.PathSpec.from_lines('gitwildmatch', lines)
    return None

def is_ignored_by_stack(path: Path, gitignore_specs: list[tuple]) -> bool:
    """
    Checks if a given path is ignored by any of the gitignore specifications in the stack.
    Each spec in the stack is a tuple (PathSpec object, base_directory_Path object).
    """
    
    # Use canonical_path for consistent matching
    canonical_path = path.resolve(strict=False) # strict = False because the paths have already been verified
    logging.debug(f"is_ignored_by_stack: Checking CANONICAL '{canonical_path}' against {len(gitignore_specs)} specs.")

    for spec_obj, base_path in gitignore_specs:
        try:
            # Calculate the path relative to the base_path of this specific gitignore spec
            rel_path = canonical_path.relative_to(base_path)
            rel_path_str = str(rel_path)

            # Git's .gitignore matching treats directories specially:
            # A pattern 'foo/' matches 'foo' (if it's a directory) and 'foo/bar'.
            # pathspec's gitwildmatch should handle this automatically.
            # However, for explicit debugging, let's see what it does.
            
            # Match as is
            matched_as_is = spec_obj.match_file(rel_path_str)
            logging.debug(f"is_ignored_by_stack:   - For spec from '{base_path}', testing '{rel_path_str}': Matched={matched_as_is}")
            if matched_as_is:
                return True

            # If it's a directory, also try matching with a trailing slash, just in case
            # (pathspec usually does this internally for patterns ending with /)
            if canonical_path.is_dir() and not rel_path_str.endswith('/'):
                matched_with_slash = spec_obj.match_file(rel_path_str + '/')
                logging.debug(f"is_ignored_by_stack:   - For spec from '{base_path}', testing '{rel_path_str}/': Matched={matched_with_slash} (as directory)")
                if matched_with_slash:
                    return True

        except ValueError:
            # This path is not a child of this base_path, so this spec doesn't apply to it.
            # This is expected in multi-repo scenarios where paths aren't hierarchical to all specs.
            logging.debug(f"is_ignored_by_stack:   - '{canonical_path}' not relative to spec base '{base_path}', skipping this spec.")
            continue
        except Exception as e:
            print(f"[ERROR] is_ignored_by_stack: An unexpected error occurred: {e}")
            continue

    logging.debug(f"is_ignored_by_stack: '{canonical_path}' NOT ignored by any active specs.") # NEW
    return False
def is_ignored_by_stack2(path: Path, gitignore_specs: list[tuple]) -> bool:
    """
    Checks if a given path is ignored by any of the gitignore specifications in the stack.
    Each spec in the stack is a tuple (PathSpec object, base_directory_Path object).
    """
    try:
        canonical_path = path.resolve(strict=False)
    except Exception as e:
        logging.debug(f"Failed to resolve path '{path}': {e}")
        return False

    logging.debug(f"is_ignored_by_stack: Checking CANONICAL '{canonical_path}' against {len(gitignore_specs)} specs.")

    # Pre-filter applicable specs using is_relative_to (Python 3.9+)
    applicable_specs = [
        (spec_obj, base_path)
        for spec_obj, base_path in gitignore_specs
        if canonical_path.is_relative_to(base_path)
    ]

    for spec_obj, base_path in applicable_specs:
        rel_path = canonical_path.relative_to(base_path)
        rel_path_str = str(rel_path)

        matched_as_is = spec_obj.match_file(rel_path_str)
        logging.debug(f"is_ignored_by_stack:   - For spec from '{base_path}', testing '{rel_path_str}': Matched={matched_as_is}")
        if matched_as_is:
            return True

        if canonical_path.is_dir() and not rel_path_str.endswith('/'):
            matched_with_slash = spec_obj.match_file(rel_path_str + '/')
            logging.debug(f"is_ignored_by_stack:   - For spec from '{base_path}', testing '{rel_path_str}/': Matched={matched_with_slash} (as directory)")
            if matched_with_slash:
                return True

    logging.debug(f"is_ignored_by_stack: '{canonical_path}' NOT ignored by any active specs.")
    return False

def update_gitignore_specs(entry: Path, active_gitignore_specs: list[tuple[pathspec.PathSpec, Path]]):
    local_spec = load_gitignore_spec(entry)
    if local_spec:
        return active_gitignore_specs + [(local_spec, entry)]
    return active_gitignore_specs
