# filesystem/filesystem.py
from pathlib import Path
# def list_directories(self) -> Set[Path]:
#         return {p for p in self.list() if p.is_dir()}

def list_directories(base_dir):
    base = Path(base_dir)
    try:
        return [p.name for p in base.iterdir() if p.is_dir()]
    except Exception:
        return []

def list_files(base_dir):
    base = Path(base_dir)
    try:
        return [p.name for p in base.iterdir() if p.is_file()]
    except Exception:
        return []

def list_dir_recursive(base_path):
    base = Path(base_path)
    result = []
    for p in base.rglob('*'):
        rel = p.relative_to(base)
        result.append(str(rel))
    return result

