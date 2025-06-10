# plugins/workspace_tree.py
from core.utils import edit_files
from filesystem.filesystem import list_directories
from pathlib import Path
# from filesystem.tree_utils import build_tree, flatten_tree

import logging
from core.plugin_base import WorkspacePlugin

# logging.basicConfig(level=logging.DEBUG)

class WorkspaceTree(WorkspacePlugin):
    priority = 20
    
    def __init__(self, menu, state):
        super().__init__(menu, state)
        self.state.update({
            # "workspace_files": set(),
        })
    
    def _main_menu_entry(self):
        return {
            "name": "Workspace Tree",
            "action": self._build_options,
        }
    
    def browse_workspace(self):
        while True:
            entries = sorted(str(p) for p in self.state.workspace.list())
            choice = self.run_selector(entries, prompt="Select Root")
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
            choice = self.run_selector(display, prompt=str(cur_path))
            if not choice:
                if stack:
                    cur_path = stack.pop()
                    continue
                return

            name = choice[0].rstrip("/")
            next_path = cur_path / name
            logging.info(next_path)
            if next_path.is_dir():
                stack.append(cur_path)
                cur_path = next_path
            else:
                edit_files([next_path])

    def get_root_dir(self) -> Path:
        root = self.state.root_dir or Path(".")
        if isinstance(root, str):
            root = Path(root)
        self.state.root_dir = root.resolve()
        return self.state.root_dir

    def traverse_directory(self):
        while True:
            dirs = list_directories(self.get_root_dir())
            selection = self.run_selector([str(d) for d in dirs], prompt="Select Directory")
            if not selection:
                return
            self.state.root_dir = dirs[[str(d) for d in dirs].index(selection[0])]

