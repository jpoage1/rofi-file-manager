# plugins/clipboard.py
from filesystem.filesystem import list_files
from core.plugin_base import WorkspacePlugin, SubMenu, MenuEntry

class Clipboard(WorkspacePlugin):
    priority = 50
    
    def __init__(self, menu, state):
        super().__init__(menu, state)
    
    def _build_menu(self) -> SubMenu:
        return SubMenu(
            "Clipboard Queue",
            [
                MenuEntry("Commit clipboard queue to the clipboard", action=lambda: None),
                MenuEntry("Add to workspace paths to clipboard queue", action=self.add_workspace_to_clipboard),
                MenuEntry("Add cwd paths to clipboard queue", action=self.add_cwd_to_clipboard),
                MenuEntry("Remove from clipboard queue", action=self.remove_from_clipboard),
            ]
        )

    def add_workspace_to_clipboard(self):
        pass
        # entries = [
        #     if p.is_file() then ClipboardEntry(p) else DirEntry(p)
        #            for p in self.state.workspace.list()]
        # submenu = SubMenu("Select Workspace Paths", entries)
        

    def add_cwd_to_clipboard(self):
        entries = list_files(self.state.get_root_dir())
        selection = self.menu.run_selector([str(e) for e in entries], prompt="Select CWD Files", multi_select=True)
        if selection:
            self.state.clipboard.add_files([entries[[str(e) for e in entries].index(s)] for s in selection])

    def remove_from_clipboard(self):
        entries = self.state.clipboard.get_files()
        selection = self.menu.run_selector([str(p) for p in entries], prompt="Select Clipboard Paths to Remove", multi_select=True)
        if selection:
            self.state.clipboard.remove_files([entries[[str(e) for e in entries].index(s)] for s in selection])
