from pathlib import Path

def expand_paths(paths, state):
    max_depth = state.expansion_depth
    expanded = []

    def walk(p: Path, depth: int = 0):
        if max_depth is not None and depth > max_depth:
            return
        if p.is_dir():
            if state.directory_expansion:
                expanded.append(p)
                if state.expansion_recursion:
                    try:
                        for child in p.iterdir():
                            walk(child, depth + 1)
                    except Exception:
                        pass
            else:
                expanded.append(p)
        else:
            expanded.append(p)

    for p in paths:
        walk(p)
    return expanded

def build_tree(paths):
    tree = {}

    for path_str in paths:
        parts = path_str.split('/')
        d = tree
        for part in parts[:-1]:
            if part not in d or not isinstance(d[part], dict):
                d[part] = {}
            d = d[part]
        if parts[-1] not in d:
            d[parts[-1]] = path_str
    return tree


def flatten_tree(node, prefix=""):
    output = []
    for name, val in sorted(node.items()):
        full = f"{prefix}{name}"
        if isinstance(val, dict):
            output.extend(flatten_tree(val, f"{full}/"))
        else:
            output.append(full)
    return output
