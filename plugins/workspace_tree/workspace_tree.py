# plugins/workspace_tree.py
from core.utils import edit_files
from core.filesystem import list_directories
from pathlib import Path
# from filesystem.tree_utils import build_tree, flatten_tree

import logging
from core.plugin_base import WorkspacePlugin, SubMenu, TreeEntry, FileEntry

# logging.basicConfig(level=logging.DEBUG)

from core.plugin_base import SubMenu

class WorkspaceTree(WorkspacePlugin):
    priority = 20
    
    def __init__(self, menu, state):
        super().__init__(menu, state)
        self.state.update({
            # "workspace_files": set(),
        })

    def _build_menu(self) -> SubMenu:
        entries = sorted(Path(p) for p in self.state.workspace.list())
        children = []
        for entry in entries:
            if entry.is_dir():
                children.append(TreeEntry(entry))
            elif entry.is_file():
                children.append(FileEntry(entry))
        return SubMenu("Workspace Tree", children)
