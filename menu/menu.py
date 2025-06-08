from pathlib import Path
from menu.rofi_interface import run_rofi
from filesystem.filesystem import list_files, list_directories
from core.core import edit_files
from state.search_options import SearchOptions
from state.workspace_utils import get_filtered_workspace_paths
from filesystem.tree_utils import build_tree, flatten_tree
from filters.main import get_entries


class MenuManager:
    def __init__(self, state):
        self.state = state
        self.search_options = SearchOptions(state)
        self.menu_structure = {
            'Workspace Tree': self.browse_workspace,
            'Search Workspace': self.search_workspace,
            'Filters': self.search_options.run_menu,
            'Workspace Management': {
                'Traverse to a new directory': self.traverse_directory,
                'Add files': self.add_files,
                'Remove files': self.remove_files,
            },
            'Clipboard Management': {
                'Commit clipboard queue to the clipboard': lambda: None,
                'Add to workspace paths to clipboard queue': self.add_workspace_to_clipboard,
                'Add cwd paths to clipboard queue': self.add_cwd_to_clipboard,
                'Remove from clipboard queue': self.remove_from_clipboard,
            },
        }

    def main_loop(self):
        self.navigate_menu(self.menu_structure)

    def navigate_menu(self, menu):
        while True:
            choice = run_rofi(list(menu.keys()), prompt="Select an option")
            if not choice:
                return
            action = menu[choice[0]]
            if callable(action):
                action()
            elif isinstance(action, dict):
                self.navigate_menu(action)

    def search_workspace(self):
        entries = get_entries(self.state)
        entries_str = [str(e) for e in entries]
        tree = build_tree(entries_str)
        choices = flatten_tree(tree)

        while True:
            selection = run_rofi(choices, prompt="Workspace Files")
            if not selection:
                return
            edit_files([Path(s) for s in selection])

    def get_root_dir(self) -> Path:
        root = self.state.root_dir
        if not root:
            root = Path(".")
        elif isinstance(root, str):
            root = Path(root)
        self.state.root_dir = root.resolve()
        return self.state.root_dir

    def traverse_directory(self):
        while True:
            root_dir = self.get_root_dir()
            dirs = list_directories(root_dir)
            selection = run_rofi([str(d) for d in dirs], prompt="Select Directory")
            if not selection:
                return
            self.state.root_dir = dirs[[str(d) for d in dirs].index(selection[0])]

    def add_files(self):
        while True:
            root_dir = self.get_root_dir()
            entries = list_files(root_dir)
            selection = run_rofi([str(e) for e in entries], prompt="Select Files to Add", multi_select=True)
            if not selection:
                return
            selected = [entries[[str(e) for e in entries].index(s)] for s in selection]
            self.state.workspace.add(selected, root_dir=root_dir)

    def remove_files(self):
        while True:
            entries = self.state.workspace.list()
            selection = run_rofi([str(p) for p in entries], prompt="Select Files to Remove", multi_select=True)
            if not selection:
                return
            selected = [entries[[str(e) for e in entries].index(s)] for s in selection]
            self.state.workspace.remove(selected)

    def add_workspace_to_clipboard(self):
        while True:
            entries = self.state.workspace.list()
            selection = run_rofi([str(p) for p in entries], prompt="Select Workspace Paths", multi_select=True)
            if not selection:
                return
            selected = [entries[[str(e) for e in entries].index(s)] for s in selection]
            self.state.clipboard.add_files(selected)

    def add_cwd_to_clipboard(self):
        while True:
            root_dir = self.get_root_dir()
            entries = list_files(root_dir)
            selection = run_rofi([str(e) for e in entries], prompt="Select CWD Files", multi_select=True)
            if not selection:
                return
            selected = [entries[[str(e) for e in entries].index(s)] for s in selection]
            self.state.clipboard.add_files(selected)

    def remove_from_clipboard(self):
        while True:
            entries = self.state.clipboard.get_files()
            selection = run_rofi([str(p) for p in entries], prompt="Select Clipboard Paths to Remove", multi_select=True)
            if not selection:
                return
            selected = [entries[[str(e) for e in entries].index(s)] for s in selection]
            self.state.clipboard.remove_files(selected)

    def browse_workspace(self):
        while True:
            entries = sorted(str(p) for p in self.state.workspace.list())
            choice = run_rofi(entries, prompt="Select Root")
            if not choice:
                return
            selected_path = Path(choice[0])
            if selected_path.is_file():
                edit_files([selected_path])
            else:
                self._browse_tree(choice[0])

    def _browse_tree(self, current_dir):
        cur_path = Path(current_dir).resolve()
        stack = []

        while True:
            try:
                entries = sorted(cur_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            except Exception:
                entries = []

            display = [f"{e.name}/" if e.is_dir() else e.name for e in entries]
            choice = run_rofi(display, prompt=str(cur_path))
            if not choice:
                if stack:
                    cur_path = stack.pop()
                    continue
                return

            name = choice[0].rstrip("/")
            next_path = cur_path / name
            print(next_path)
            if next_path.is_dir():
                stack.append(cur_path)
                cur_path = next_path
            else:
                edit_files([next_path])
