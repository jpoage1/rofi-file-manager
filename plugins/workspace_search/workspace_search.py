# core/menu.py
from pathlib import Path
from core.utils import edit_files
import logging

# logging.basicConfig(level=logging.DEBUG)

from core.plugin_base import WorkspacePlugin, LazySubMenu, FileEntry

class WorkspaceSearch(WorkspacePlugin):
    priority = 1

    name = "workspace-search"
    
    def __init__(self, menu, state):
        super().__init__(menu, state)

    def _build_menu(self) -> LazySubMenu:
        def loader():
            print("Loading")
            entries = self.state.workspace.query_from_cache()
            choices = sorted(entries)
            return [FileEntry(entry) for entry in choices]

        return LazySubMenu("Workspace Search", loader)
