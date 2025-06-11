# Path: old/workspace/workspace.py
# Last Modified: 2025-06-11

# workspace/workspace.py (example snippets)

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Assume State is defined elsewhere and will be imported
# from state.state import State 

class Workspace:
    def __init__(self, json_file: str = "workspace.json", paths: Optional[List[str]] = None, cwd: Optional[str] = None):
        self.workspace_file = Path(json_file).resolve()
        self.user_added_paths: List[Path] = []
        self.generated_paths: List[Path] = []
        self.generator_blacklist_patterns: List[str] = []
        self.state: Optional[Any] = None # Will be set by State instance
        self._initial_state_config: Dict[str, Any] = {} # To load initial state from workspace file

        # Load initial config and workspace data from JSON
        self._load_from_json()

        # If CWD is provided, resolve it
        if cwd:
            self.cwd = Path(cwd).resolve()
        else:
            self.cwd = Path.cwd().resolve()
        
        # Add initial paths if provided (these are treated as user_added)
        if paths:
            self.add([Path(p).resolve() for p in paths])

    def set_state_instance(self, state_instance):
        """Sets the State instance for cross-referencing and dirty tracking."""
        self.state = state_instance

    def _load_from_json(self):
        if self.workspace_file.exists():
            try:
                with open(self.workspace_file, 'r') as f:
                    data = json.load(f)
                    self.user_added_paths = [Path(p) for p in data.get('user_added_paths', [])]
                    self.generated_paths = [Path(p) for p in data.get('generated_paths', [])]
                    self.generator_blacklist_patterns = data.get('generator_blacklist_patterns', [])
                    self._initial_state_config = data.get('state_config', {}) # Load state config
                    logging.info(f"Workspace loaded from {self.workspace_file}. Initial config: {self._initial_state_config}")
            except Exception as e:
                print(f"[ERROR] Failed to load workspace from {self.workspace_file}: {e}")
                self._initialize_default_workspace()
        else:
            self._initialize_default_workspace()

    def _initialize_default_workspace(self):
        logging.info(f"No workspace file found at {self.workspace_file} or load failed. Initializing default workspace.")
        self.user_added_paths = []
        self.generated_paths = []
        self.generator_blacklist_patterns = []
        self._initial_state_config = {} # Default empty state config
        if self.state:
            self.state.mark_dirty() # Mark dirty if starting with a new workspace

    def save(self, target_file: Optional[Path] = None):
        """Saves the workspace to the current or specified JSON file."""
        save_path = target_file if target_file else self.workspace_file
        data = {
            'user_added_paths': [str(p) for p in self.user_added_paths],
            'generated_paths': [str(p) for p in self.generated_paths],
            'generator_blacklist_patterns': self.generator_blacklist_patterns,
            'state_config': self.state.get_persistable_config() if self.state else {} # Save state config
        }
        try:
            with open(save_path, 'w') as f:
                json.dump(data, f, indent=4)
            if target_file and self.workspace_file != target_file:
                self.workspace_file = target_file # Update workspace file if saved "as"
            if self.state:
                self.state.is_dirty = False # Clear dirty flag after saving
            logging.info(f"Workspace saved to {save_path}")
        except Exception as e:
            print(f"[ERROR] Failed to save workspace to {save_path}: {e}")

    def add(self, paths: List[Path], root_dir: Optional[Path] = None):
        """Adds paths to the user_added_paths if not already present."""
        for path in paths:
            if path not in self.user_added_paths:
                self.user_added_paths.append(path)
                if self.state:
                    self.state.mark_dirty()
        # logging.info(f"Added {len(paths)} paths. Total user-added: {len(self.user_added_paths)}")

    def remove(self, paths: List[Path]):
        """Removes paths from the user_added_paths."""
        initial_count = len(self.user_added_paths)
        self.user_added_paths = [p for p in self.user_added_paths if p not in paths]
        if len(self.user_added_paths) != initial_count and self.state:
            self.state.mark_dirty()
        # logging.info(f"Removed {initial_count - len(self.user_added_paths)} paths. Total user-added: {len(self.user_added_paths)}")

    def add_generator_blacklist_pattern(self, pattern: str):
        if pattern not in self.generator_blacklist_patterns:
            self.generator_blacklist_patterns.append(pattern)
            if self.state:
                self.state.mark_dirty()
            # logging.info(f"Added blacklist pattern: {pattern}")

    def remove_generator_blacklist_pattern(self, pattern: str):
        initial_count = len(self.generator_blacklist_patterns)
        self.generator_blacklist_patterns = [p for p in self.generator_blacklist_patterns if p != pattern]
        if len(self.generator_blacklist_patterns) != initial_count and self.state:
            self.state.mark_dirty()
            # logging.info(f"Removed blacklist pattern: {pattern}")

    def reset(self):
        """Resets the workspace to its default empty state."""
        self.user_added_paths = []
        self.generated_paths = []
        self.generator_blacklist_patterns = []
        # No change to self._initial_state_config unless you want to reset that too
        if self.state:
            self.state.mark_dirty()
        # logging.info("[INFO] Workspace has been reset.")
        
    # ... other methods like list, get_generator_blacklist_patterns, etc.
