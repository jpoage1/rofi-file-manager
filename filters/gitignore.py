# gitignore.py
import pathspec
from pathlib import Path

def load_gitignore_spec(directory_path: Path):
    gitignore_path = directory_path / '.gitignore'
    if gitignore_path.exists():
        with gitignore_path.open('r') as f:
            lines = f.read().splitlines()
        return pathspec.PathSpec.from_lines('gitwildmatch', lines)
    return None

def is_ignored_by_stack(path: Path, active_gitignore_specs: list[tuple[pathspec.PathSpec, Path]]):
    if not active_gitignore_specs:
        return False
    for spec, base_path in reversed(active_gitignore_specs):
        if spec is None:
            continue
        try:
            rel_path = path.relative_to(base_path)
            if spec.match_file(str(rel_path)):
                return True
        except ValueError:
            continue
    return False

def update_gitignore_specs(entry: Path, active_gitignore_specs: list[tuple[pathspec.PathSpec, Path]]):
    local_spec = load_gitignore_spec(entry)
    if local_spec:
        return active_gitignore_specs + [(local_spec, entry)]
    return active_gitignore_specs
