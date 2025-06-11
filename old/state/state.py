# Path: old/state/state.py
# Last Modified: 2025-06-11

# old/state/state.py
from pathlib import Path
from state.workspace import Workspace
from core.clipboard import Clipboard
from core.search_config import SearchConfig
import logging

class State:
    def __init__(self, workspace=None, clipboard=None, root_dir=None):
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
            "use_gitignore": self.use_gitignore,
            "include_dotfiles": self.include_dotfiles,
            "search_dirs_only": self.search_dirs_only,
            "search_files_only": self.search_files_only,
            "regex_mode": self.regex_mode,
            "regex_pattern": self.regex_pattern,
            "root_dir": str(self.root_dir) if self.root_dir else None,
            "clipboard_queue": [str(p) for p in self.clipboard.snapshot()],
        }
        self.state_stack.append(snapshot)

    def pop_state(self):
        if self.state_stack:
            snapshot = self.state_stack.pop()
            self.use_gitignore = snapshot["use_gitignore"]
            self.include_dotfiles = snapshot["include_dotfiles"]
            self.search_dirs_only = snapshot["search_dirs_only"]
            self.search_files_only = snapshot["search_files_only"]
            self.regex_mode = snapshot["regex_mode"]
            self.regex_pattern = snapshot["regex_pattern"]

            loaded_root_dir = snapshot["root_dir"]
            self.root_dir = Path(loaded_root_dir) if loaded_root_dir else None
            
            loaded_clipboard_queue = snapshot["clipboard_queue"]
            self.clipboard.restore([Path(p) for p in loaded_clipboard_queue])


    # def save_to_file(self, path):
    #     with open(path, "w") as f:
    #         json.dump(self.to_dict(), f, indent=2)

    # @classmethod
    # def load_from_file(cls, path):
    #     path = Path(path)
    #     if not path.exists():
    #         path.write_text(json.dumps({}))
    #     with open(path) as f:
    #         data = json.load(f)
    #     return cls.from_dict(data)
    
    # @classmethod
    # def from_dict(cls, data):
    #     workspace = Workspace("workspace.json")
    #     clipboard = Clipboard()
    #     root_dir = data.get("root_dir")
        
    #     # Create state instance
    #     state = cls(workspace=workspace, clipboard=clipboard, root_dir=root_dir)
        
    #     # Restore auto_save_enabled from saved state, default to False
    #     state.auto_save_enabled = data.get("auto_save_enabled", False)
    #     state.is_dirty = False # Always start clean on load

    #     return state

    # def to_dict(self):
    #     return {
    #         "use_gitignore": self.use_gitignore,
    #         "include_dotfiles": self.include_dotfiles,
    #         "search_dirs_only": self.search_dirs_only,
    #         "search_files_only": self.search_files_only,
    #         "regex_mode": self.regex_mode,
    #         "regex_pattern": self.regex_pattern,
    #         "root_dir": str(self.root_dir) if self.root_dir else None,
    #         "clipboard_queue": [str(p) for p in self.clipboard.snapshot()],
    #         "input_set": self.input_set,
    #         # --- NEW: Persist auto_save_enabled ---
    #         "auto_save_enabled": self.auto_save_enabled,
    #         # --- END NEW ---
    #         # is_dirty should NOT be persisted as it's a runtime flag
    #     }
    def autoSave(self, save_callable):
        """Conditionally calls the provided save_callable and clears the dirty flag."""
        if self.auto_save_enabled:
            logging.debug("Auto-save triggered.")
            save_callable() # This will call workspace.save(), which clears is_dirty

    def get_persistable_config(self) -> dict:
        """Returns a dictionary of state attributes that should be persisted."""
        return {
            "use_gitignore": self.use_gitignore,
            "include_dotfiles": self.include_dotfiles,
            "search_dirs_only": self.search_dirs_only,
            "search_files_only": self.search_files_only,
            "regex_mode": self.regex_mode,
            "regex_pattern": self.regex_pattern,
            "root_dir": str(self.root_dir) if self.root_dir else None,
            "clipboard_queue": [str(p) for p in self.clipboard.snapshot()],
            "auto_save_enabled": self.auto_save_enabled,
        }

    def apply_config(self, config_dict: dict):
        """Applies configuration from a dictionary to the state attributes."""
        # Use .get() with defaults to handle cases where a key might be missing in older JSONs
        self.use_gitignore = config_dict.get("use_gitignore", True) # Default to True
        self.include_dotfiles = config_dict.get("include_dotfiles", False) # Default to False
        self.search_dirs_only = config_dict.get("search_dirs_only", False) # Default to False
        self.search_files_only = config_dict.get("search_files_only", False) # Default to False
        self.regex_mode = config_dict.get("regex_mode", False) # Default to False
        self.regex_pattern = config_dict.get("regex_pattern", "") # Default to empty string
        
        # root_dir needs special handling as it's a Path object
        loaded_root_dir = config_dict.get("root_dir")
        self.root_dir = Path(loaded_root_dir) if loaded_root_dir else None

        # Clipboard queue needs special handling (list of Path objects)
        loaded_clipboard_queue = config_dict.get("clipboard_queue", [])
        self.clipboard.restore([Path(p) for p in loaded_clipboard_queue])
        
        self.auto_save_enabled = config_dict.get("auto_save_enabled", False) # Default to False
        logging.debug(f"Applied State config from JSON: auto_save_enabled={self.auto_save_enabled}")
