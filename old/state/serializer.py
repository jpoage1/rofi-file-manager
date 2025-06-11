# state/serializer.py
import json
from pathlib import Path
from typing import Dict

def load_cache_file(path: Path) -> Dict:
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_cache_file(path: Path, data: Dict):
    tmp = path.with_suffix('.tmp')
    with open(tmp, 'w') as f:
        json.dump(data, f)
    tmp.replace(path)
