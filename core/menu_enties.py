from typing import Callable, List, Optional, Union
import os

class MenuEntry:
    def __init__(self, label: str, action: Optional[Union[Callable, str]] = None):
        self.label = label
        self.action = action

    def to_dict(self):
        return {"name": self.label, "action": self.action}

class SubMenu(MenuEntry):
    def __init__(self, label: str, children: List[MenuEntry]):
        super().__init__(label)
        self.children = children

    def to_dict(self):
        return {"name": self.label, "action": [child.to_dict() for child in self.children]}

class FileEntry(MenuEntry):
    def __init__(self, path: str, label: Optional[str] = None):
        label = label or os.path.basename(path)
        super().__init__(label, action=lambda: os.system(f"${{EDITOR:-vim}} '{path}'"))

class DirEntry(MenuEntry):
    def __init__(self, path: str, label: Optional[str] = None):
        label = label or os.path.basename(path)
        children = []
        for entry in sorted(os.listdir(path)):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                children.append(DirEntry(full_path))
            elif os.path.isfile(full_path):
                children.append(FileEntry(full_path))
        super().__init__(label, action=[child.to_dict() for child in children])

class ExecEntry(MenuEntry):
    def __init__(self, label: str, command: str):
        super().__init__(label, action=lambda: os.system(command))
