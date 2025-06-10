# core/menu.py
from pathlib import Path
from core.utils import edit_files
import logging

from core.plugins import load_menu_plugins

# logging.basicConfig(level=logging.DEBUG)

from core.plugin_base import SubMenu
# plugins/clipboard.py
from filesystem.filesystem import list_files
from core.plugin_base import WorkspacePlugin, SubMenu, FileEntry

class WorkspaceSearch(WorkspacePlugin):
    priority = 1
    
    def __init__(self, menu, state):
        super().__init__(menu, state)

    def _build_menu(self) -> SubMenu:
        entries = self.state.workspace.cache
        entries_str = sorted([str(e) for e in entries])
        choices = sorted(entries_str)

        return SubMenu(
            "Workspace Search",
            [FileEntry(entry) for entry in choices]
        )
