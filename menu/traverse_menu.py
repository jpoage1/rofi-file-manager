# menu_manager/traverse_menu.py

from filesystem.filesystem import list_directories
from pathlib import Path

def traverse_directory(state):
    current_dir = state.root_dir
    dirs = list_directories(current_dir)
    if not dirs:
        return
    choice = state.run_selector(dirs, prompt="Traverse to directory", multi_select=False)
    if not choice:
        return
    selected_path = Path(current_dir) / choice[0]
    if selected_path.is_dir():
        state.root_dir = str(selected_path.resolve())
