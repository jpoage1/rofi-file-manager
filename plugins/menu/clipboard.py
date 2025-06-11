# plugins/clipboard.py
from core.plugin_base import WorkspacePlugin, SubMenu, MenuEntry
import pyperclip
from pathlib import Path

class Clipboard(WorkspacePlugin):
    priority = 50
    
    def __init__(self, menu, state):
        super().__init__(menu, state)
        self.queue = []
    
    def _build_menu(self) -> SubMenu:
        return SubMenu(
            "Clipboard Queue",
            [
                MenuEntry("Commit clipboard queue to the clipboard", action=lambda: None),
                SubMenu("Add to workspace paths to clipboard queue", 
                    [MenuEntry(e, action=lambda e=e: self.add_file(e)) for e in self.state.workspace.list()]
                          ),
                SubMenu("Add CWD Files to clipboard queue", 
                    [MenuEntry(e.name, action=lambda e=e: self.add_file(e)) for e in self.list_files(self.state.get_root_dir())]
                ),
                SubMenu(
                    "Remove from clipboard queue",
                    [MenuEntry(p, action=lambda i=i: self.remove_file(i)) for i, p in enumerate(self.get_files())]
                )
            ]
        )

    @staticmethod
    def list_files(base_dir):
        base = Path(base_dir)
        try:
            return [p for p in base.iterdir() if p.is_file()]
        except Exception:
            return []

    def add_file(self, file):
        p = self.get_root_dir() / file if not isinstance(file, Path) else file
        if p.is_file() and p not in self.queue:
            self.queue.append(p)

    def remove_file(self, index):
        self.queue.remove(index)

    def clear(self):
        self.queue.clear()

    def commit(self):
        content = ''.join(read_file_safe(f) for f in self.queue)
        try:
            pyperclip.copy(content)
        except pyperclip.PyperclipException:
            pass  # Optionally log or handle failure
        self.clear()

    def snapshot(self):
        return list(self.queue)

    def restore(self, snapshot):
        self.queue = list(snapshot)

    def get_files(self):
        print(self.queue)
        return list(self.queue)
    
    def get_root_dir(self) -> Path:
        root = self.state.root_dir or Path(".")
        if isinstance(root, str):
            root = Path(root)
        self.state.root_dir = root.resolve()
        return self.state.root_dir
