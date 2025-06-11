# core/state.py
from pathlib import Path
from core.workspace import Workspace
import logging

class State:
    def __init__(self, workspace=None, root_dir=None):
        self.root_dir = root_dir
        self.state_stack = []
        self.input_set = []
        self.workspace_files = set()
        self.workspace = workspace or Workspace("workspace.json")
        self.is_dirty: bool = False # True if there are unsaved changes
        self.auto_save_enabled: bool = False # Controls if changes are auto-saveds

    def push_state(self):
        snapshot = {
            "root_dir": str(self.root_dir) if self.root_dir else None,
        }
        self.state_stack.append(snapshot)

    def pop_state(self):
        if self.state_stack:
            snapshot = self.state_stack.pop()

            loaded_root_dir = snapshot["root_dir"]
            self.root_dir = Path(loaded_root_dir) if loaded_root_dir else None
            

    def autoSave(self, save_callable):
        """Conditionally calls the provided save_callable and clears the dirty flag."""
        if self.auto_save_enabled:
            logging.debug("Auto-save triggered.")
            save_callable() # This will call workspace.save(), which clears is_dirty

    def get_persistable_config(self) -> dict:
        """Returns a dictionary of state attributes that should be persisted."""
        return {
            "root_dir": str(self.root_dir) if self.root_dir else None,
            "auto_save_enabled": self.auto_save_enabled,
        }

    def apply_config(self, config_dict: dict):
        """Applies configuration from a dictionary to the state attributes."""
        
        # root_dir needs special handling as it's a Path object
        loaded_root_dir = config_dict.get("root_dir")
        self.root_dir = Path(loaded_root_dir) if loaded_root_dir else None
        
        self.auto_save_enabled = config_dict.get("auto_save_enabled", False) # Default to False
        logging.debug(f"Applied State config from JSON: auto_save_enabled={self.auto_save_enabled}")

    def update(self, values: dict):
        for key, value in values.items():
            setattr(self, key, value)

    def get_root_dir(self) -> Path:
        root = self.root_dir or Path(".")
        if isinstance(root, str):
            root = Path(root)
        self.root_dir = root.resolve()
        return self.root_dir
