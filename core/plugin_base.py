from typing import Callable, List, Optional, Union
import os
from pathlib import Path
import subprocess

class InterfacePlugin:
    name: str
    priority: int
    def interface(self): pass

class MenuPlugin:
    name: str
    priority: int
    def __init__(self, menu, state): pass

class SelectorPlugin:
    name: str
    priority: int
    def selector(self): pass


class MenuEntry:
    def __init__(self, label: str, action: Optional[Union[Callable[['MenuEntry'], None], str]] = None):
        self.label = label
        if action:
            self.action = action

    def to_dict(self):
        return {"name": self.label, "action": self._action}

    def action(self):
        pass
    
    def indexedLabel(self, i):
        return f"{i}: {self.label}"

class VoidEntry(MenuEntry):
    def __init__(self, label: str):
        self.label = label

    def action(self):
        return

class TextInputEntry(MenuEntry):
    pass

class BinaryToggleEntry(MenuEntry):
    def __init__(self, label: str, attr, state):
        self.base_label = label
        self.attr = attr
        self.state = state
        self.label = self.toggle_label()

    def toggle_status(self):
        return 'ON' if getattr(self.state, self.attr) else 'OFF'
    
    def toggle_label(self):
        return f"{self.base_label}: {self.toggle_status()}"

    def action(self):
        setattr(self.state, self.attr, not getattr(self.state, self.attr))
        self.label = self.toggle_label()

class MenuEntries(MenuEntry):
    def __init__(self, children):
        self.children = children
    def entries(self):
        return self.children
    def get(self, index):
        entry = self.children[index]
        if callable(entry):
            entry = entry()
            # Don't cache result or the menu won't get updated correctly
            # self.children[index] = entry  # cache result
        return entry
    def load(self):
        pass
    
class SubMenu(MenuEntries):
    def __init__(self, label: str, children: List[MenuEntry]):
        super().__init__(children)
        self.label = label

    def to_dict(self):
        return {"name": self.label, "action": [child.to_dict() for child in self.children]}
    
    def load(self):
        pass

class LazySubMenu(SubMenu):
    def __init__(self, label: str, children_or_loader):
        if callable(children_or_loader):
            self._children_loader = children_or_loader
            self._children = None
        else:
            self._children_loader = None
            self._children = children_or_loader
        super().__init__(label, self._children or [])

    def entries(self):
        if self._children is None and self._children_loader:
            self._children = self._children_loader()
            self.children = self._children
        return self.children

    def get(self, index):
        entries = self.entries()
        entry = entries[index]
        if callable(entry):
            entry = entry()
        return entry

    def to_dict(self):
        return {
            "name": self.label,
            "action": [child.to_dict() for child in self.entries()]
        }
    def load(self):
        self.entries()  # triggers population



class PathEntry(MenuEntry):
    def __init__(self, path: str, label: Optional[str] = None, action: Optional[Callable[['PathEntry'], None]] = None):
        self.path = Path(path)
        label = label or self.path.name
        super().__init__(label, action=self.action)

    def action(self):
        pass

    def get_path(self) -> Path:
        return self.path

    def get_absolute_path(self) -> Path:
        return self.path.resolve()

    def get_relative_path(self, start: Optional[str] = None) -> Path:
        return self.path.relative_to(Path(start or os.getcwd()))


class FileEntry(PathEntry):
    def __init__(self, path: str, label: Optional[str] = None, editor: str = None):
        super().__init__(path, label)
        self.editor = editor or os.environ.get("EDITOR", "vim")

    def action(self):
        cmd = ["xterm", "-fa", "DejaVu Sans Mono Book", "-fs", "12", "-e", self.editor, self.path]
        subprocess.run(cmd)



class ClipboardEntry(FileEntry):
    def __init__(self, path: str, label: Optional[str] = None):
        super().__init__(path, label)

    def action(self):
        pass  # implement actual clipboard interaction

class DirEntry(PathEntry):
    def __init__(self, path: str, label: Optional[str] = None):
        label = label or os.path.basename(path)

class TreeEntry(SubMenu):
    def __init__(self, path: str, label: str = None, show_dirs: bool = True, show_files: bool = True ):
        self.label = label or path
        self.show_files = show_files
        self.show_dirs = show_dirs
        self.path = Path(path)
        self.children = self.list_directories(path)

    def action(self):
        while True:
            dirs = self.list_directories(self.get_root_dir())
            # selection = self.menu.run_selector([str(d) for d in dirs], prompt="Select Directory")
            # if not selection:
            #     return
            # self.state.root_dir = dirs[[str(d) for d in dirs].index(selection[0])]

    def list_directories(self, base_dir):
        base = Path(base_dir)
        children = []
        try:
            for p in base.iterdir():
                if self.show_dirs and p.is_dir():
                    children.append(TreeEntry(p.name)) 
                elif self.show_files and p.is_file():
                    children.append(FileEntry(p.name)) 
            return children
        except Exception:
            return []
        

class ExecEntry(MenuEntry):
    def __init__(self, label: str, command: str):
        super().__init__(label, action=lambda self: os.system(command))


class WorkspacePlugin:
    priority = None

    def __init__(self, menu, state):
        self.menu = menu
        self.state = state

    def build_menu(self) -> List[dict]:
        return [entry.to_dict() for entry in self._build_menu()]

    def _build_menu(self) -> List[MenuEntry]:
        raise NotImplementedError

class ConfirmHelper:
    def __init__(self, run_selector):
        self.run_selector = run_selector

    def confirm(self, prompt: str, yes="Yes", no="No") -> bool:
        response = self.run_selector([yes, no], prompt=prompt)
        return bool(response) and response[0] == yes

class PathPromptHelper:
    def __init__(self, run_selector):
        self.run_selector = run_selector

    def prompt_for_path(self, prompt: str) -> Path | None:
        result = self.run_selector([], prompt=prompt)
        if not result or not result[0].strip():
            return None
        return Path(result[0].strip()).resolve()

class SelectorHelper:
    def __init__(self, run_selector):
        self.confirm = ConfirmHelper(run_selector).confirm
        self.prompt_for_path = PathPromptHelper(run_selector).prompt_for_path

class RegexPromptHelper:
    def __init__(self, run_selector):
        self.run_selector = run_selector

    def prompt(self, prompt="Enter regex pattern") -> str:
        result = self.run_selector([], prompt=prompt, multi_select=False)
        return result[0] if result else ""

class ExpansionDepthHelper:
    def __init__(self, run_selector):
        self.run_selector = run_selector

    def prompt(self, prompt="Enter max recursion depth (empty for unlimited)") -> int | None:
        result = self.run_selector([], prompt=prompt, multi_select=False)
        if not result:
            return None
        val = result[0].strip()
        if val == "" or val.lower() in ("none", "unlimited"):
            return None
        try:
            return max(0, int(val))
        except ValueError:
            return None
        