import sys
def get_input_paths():
    paths = []
    if len(sys.argv) > 1:
        paths.extend(sys.argv[1:])
    if not sys.stdin.isatty():
        paths.extend(line.strip() for line in sys.stdin if line.strip())
    return paths
