# Path: old/menu_manager/menu_workspace.py
# Last Modified: 2025-06-11

# menu_manager/menu_workspace.py
from pathlib import Path
from filesystem.filesystem import list_files, list_directories

class WorkspaceActions:
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

    def add_files(self):
        root_dir = self.get_root_dir()
        entries = list_files(root_dir)
        selection = self.run_selector([str(e) for e in entries], prompt="Select Files to Add", multi_select=True)
        if selection:
            self.state.workspace.add([entries[[str(e) for e in entries].index(s)] for s in selection], root_dir=root_dir)
        self.update_file_watcher()

    def remove_files(self):
        entries = self.state.workspace.list()
        selection = self.run_selector([str(p) for p in entries], prompt="Select Files to Remove", multi_select=True)
        if selection:
            self.state.workspace.remove([entries[[str(e) for e in entries].index(s)] for s in selection])
        self.update_file_watcher()
