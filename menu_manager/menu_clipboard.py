# menu_manager/menu_clipboard.py
from pathlib import Path
from filesystem.filesystem import list_files

class ClipboardActions:
    def add_workspace_to_clipboard(self):
        entries = self.state.workspace.list()
        selection = self.run_selector([str(p) for p in entries], prompt="Select Workspace Paths", multi_select=True)
        if selection:
            self.state.clipboard.add_files([entries[[str(e) for e in entries].index(s)] for s in selection])

    def add_cwd_to_clipboard(self):
        entries = list_files(self.state.get_root_dir())
        selection = self.run_selector([str(e) for e in entries], prompt="Select CWD Files", multi_select=True)
        if selection:
            self.state.clipboard.add_files([entries[[str(e) for e in entries].index(s)] for s in selection])

    def remove_from_clipboard(self):
        entries = self.state.clipboard.get_files()
        selection = self.run_selector([str(p) for p in entries], prompt="Select Clipboard Paths to Remove", multi_select=True)
        if selection:
            self.state.clipboard.remove_files([entries[[str(e) for e in entries].index(s)] for s in selection])
