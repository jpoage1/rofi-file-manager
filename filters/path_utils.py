# filters/path_utils
from pathlib import Path

def resolve_path_and_inode(path: Path):
    try:
        canonical = path.resolve()
        stat_info = canonical.stat()
        return canonical, (stat_info.st_dev, stat_info.st_ino)
    except Exception:
        return None, None

def list_directory_children(entry: Path, include_dotfiles: bool):
    try:
        children = list(entry.iterdir())
    except Exception:
        return []
    if not include_dotfiles:
        children = [c for c in children if not c.name.startswith(".")]
    return children
