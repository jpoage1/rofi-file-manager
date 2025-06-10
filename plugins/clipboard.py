# plugins/clipboard.py
from filesystem.filesystem import list_files
from core.plugin_base import WorkspacePlugin

class Clipboard(WorkspacePlugin):
    priority = 50
    
    def __init__(self, menu, state):
        super().__init__(menu, state)
    
    def _main_menu_entry(self):
        return {
            "name": "Clipboard Queue",
            "action": self._build_options,
        }
    
    def _build_options(self):
        return [
            {
                "name": "Commit clipboard queue to the clipboard",
                "action": lambda: None,
            },
            {
                "name": "Add to workspace paths to clipboard queue",
                "action": self.add_workspace_to_clipboard,
            },
            {
                "name": "Add cwd paths to clipboard queue",
                "action": self.add_cwd_to_clipboard,
            },
            {
                "name": "Remove from clipboard queue",
                "action": self.remove_from_clipboard,
            },
        ]
   
    def add_workspace_to_clipboard(self):
        entries = self.state.workspace.list()
        selection = self.run_selector([str(p) for p in entries], prompt="Select Workspace Paths", multi_select=True)
        if selection:
            self.state.clipboard.add_files([entries[[str(e) for e in entries].index(s)] for s in selection])

    def add_cwd_to_clipboard(self):
        entries = list_files(self.get_root_dir())
        selection = self.run_selector([str(e) for e in entries], prompt="Select CWD Files", multi_select=True)
        if selection:
            self.state.clipboard.add_files([entries[[str(e) for e in entries].index(s)] for s in selection])

    def remove_from_clipboard(self):
        entries = self.state.clipboard.get_files()
        selection = self.run_selector([str(p) for p in entries], prompt="Select Clipboard Paths to Remove", multi_select=True)
        if selection:
            self.state.clipboard.remove_files([entries[[str(e) for e in entries].index(s)] for s in selection])
