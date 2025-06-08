# state.py
from pathlib import Path
import json
from state.workspace import Workspace
from clipboard.clipboard import Clipboard
from search_config import SearchConfig
class State:
    def __init__(self, workspace=None, clipboard=None, root_dir=None):
        self.current_mode = "Edit"
        self.use_gitignore = True
        self.include_dotfiles = False
        self.expansion_depth = None
        self.expansion_recursion = True
        self.directory_expansion = True
        self.regex_mode = False
        self.regex_pattern = ""
        self.show_files = True
        self.search_dirs_only = False
        self.search_files_only = False
        self.show_dirs = True
        self.root_dir = root_dir
        self.clipboard_queue = []
        self.state_stack = []
        self.input_set = []
        self.workspace_files = set()
        self.clipboard = clipboard or Clipboard()
        self.workspace = workspace or Workspace("workspace.json")
        self.search_config = SearchConfig()
        self.is_dirty: bool = False # True if there are unsaved changes
        self.auto_save_enabled: bool = False # Controls if changes are auto-saveds

    def push_state(self):
        snapshot = {
            "current_mode": self.current_mode,
            "use_gitignore": self.use_gitignore,
            "include_dotfiles": self.include_dotfiles,
            "search_dirs_only": self.search_dirs_only,
            "search_files_only": self.search_files_only,
            "regex_mode": self.regex_mode,
            "regex_pattern": self.regex_pattern,
            "root_dir": self.root_dir,
            "clipboard_queue": self.clipboard.snapshot(),
        }
        self.state_stack.append(snapshot)

    def pop_state(self):
        if self.state_stack:
            snapshot = self.state_stack.pop()
            self.current_mode = snapshot["current_mode"]
            self.use_gitignore = snapshot["use_gitignore"]
            self.include_dotfiles = snapshot["include_dotfiles"]
            self.search_dirs_only = snapshot["search_dirs_only"]
            self.search_files_only = snapshot["search_files_only"]
            self.regex_mode = snapshot["regex_mode"]
            self.regex_pattern = snapshot["regex_pattern"]
            self.root_dir = snapshot["root_dir"]
            self.clipboard.restore(snapshot["clipboard_queue"])

    def save_to_file(self, path):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, path):
        path = Path(path)
        if not path.exists():
            path.write_text(json.dumps({}))
        with open(path) as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data):
        workspace = Workspace("workspace.json")
        clipboard = Clipboard()
        root_dir = data.get("root_dir")
        
        # Create state instance
        state = cls(workspace=workspace, clipboard=clipboard, root_dir=root_dir)
        
        # Restore auto_save_enabled from saved state, default to False
        state.auto_save_enabled = data.get("auto_save_enabled", False)
        state.is_dirty = False # Always start clean on load

        return state

    def to_dict(self):
        return {
            "current_mode": self.current_mode,
            "use_gitignore": self.use_gitignore,
            "include_dotfiles": self.include_dotfiles,
            "search_dirs_only": self.search_dirs_only,
            "search_files_only": self.search_files_only,
            "regex_mode": self.regex_mode,
            "regex_pattern": self.regex_pattern,
            "root_dir": str(self.root_dir) if self.root_dir else None,
            "clipboard_queue": [str(p) for p in self.clipboard.snapshot()],
            "input_set": self.input_set,
            # --- NEW: Persist auto_save_enabled ---
            "auto_save_enabled": self.auto_save_enabled,
            # --- END NEW ---
            # is_dirty should NOT be persisted as it's a runtime flag
        }
    def autoSave(self, autoSave):
        if self.auto_save_enabled:
            autoSave()
            self.state.is_dirty = False
