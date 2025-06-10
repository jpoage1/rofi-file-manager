from typing import Callable, List, Optional, Union
import os
from pathlib import Path

class MenuEntry:
    def __init__(self, label: str, action: Optional[Union[Callable[['MenuEntry'], None], str]] = None):
        self.label = label
        self._action = action

    def to_dict(self):
        return {"name": self.label, "action": self._action}

    def action(self):
        if callable(self._action):
            self._action()
    
    def indexedLabel(self, i):
        return f"{i}: {self.label}"
class SeperatorEntry(MenuEntry):
    pass

class TextEntry(MenuEntry):
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
    def get(self, i):
        return self.children[i]

class SubMenu(MenuEntries):
    def __init__(self, label: str, children: List[MenuEntry]):
        super().__init__(children)
        self.label = label

    def to_dict(self):
        return {"name": self.label, "action": [child.to_dict() for child in self.children]}


class PathEntry(MenuEntry):
    def __init__(self, path: str, label: Optional[str] = None, action: Optional[Callable[['PathEntry'], None]] = None):
        self._path = Path(path)
        if action is None:
            action = lambda self: os.system(f"${{EDITOR:-vim}} '{self._path}'")
        label = label or self._path.name
        super().__init__(label, action=action)

    def edit(self):
        os.system(f"${{EDITOR:-vim}} '{self._path}'")

    def action(self):
        if callable(self._action):
            self._action(self)

    def get_path(self) -> Path:
        return self._path

    def get_absolute_path(self) -> Path:
        return self._path.resolve()

    def get_relative_path(self, start: Optional[str] = None) -> Path:
        return self._path.relative_to(Path(start or os.getcwd()))


class FileEntry(PathEntry):
    def __init__(self, path: str, label: Optional[str] = None):
        super().__init__(path, label)
        self._action = lambda self: self.edit()


class ClipboardEntry(FileEntry):
    def __init__(self, path: str, label: Optional[str] = None):
        super().__init__(path, label)
        self._action = lambda self: self.to_clipboard()

    def to_clipboard(self):
        pass  # implement actual clipboard interaction


class DirEntry(SubMenu):
    def __init__(self, path: str, label: Optional[str] = None):
        label = label or os.path.basename(path)
        children: List[MenuEntry] = []
        for entry in sorted(os.listdir(path)):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                children.append(DirEntry(full_path))
            elif os.path.isfile(full_path):
                children.append(FileEntry(full_path))
        super().__init__(label, children)


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
        