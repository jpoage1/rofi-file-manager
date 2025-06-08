# workspace.py
import json
import fcntl
from pathlib import Path
import re
from typing import List, Set # <--- ADD THIS LINE

class Workspace:
    def __init__(self, json_file=None, paths=None, cwd=None):
        self.cwd = Path(cwd).resolve() if cwd else Path.cwd().resolve()
        self.json_file = Path(json_file if json_file else "workspace.json")

        # Internal sets to manage different categories of paths
        self._generated_paths: Set[Path] = set()  # Paths from the dynamic generator (args.paths)
        self._user_paths: Set[Path] = set()       # Paths explicitly added/managed by the user
        self._ignored_paths: Set[Path] = set()    # Paths explicitly removed by the user (blacklist of individual paths)
        self._generator_blacklist_patterns: List[str] = [] # List of regex patterns for generator output

        # Store initial (loaded) state for dirty checking
        self._initial_user_paths: Set[Path] = set()
        self._initial_ignored_paths: Set[Path] = set()
        self._initial_generator_blacklist_patterns: List[str] = []
        self._initial_state_config: dict = {} # To store the state_config *as loaded from JSON*
        self._initial_json_file_exists: bool = self.json_file.exists() and self.json_file.stat().st_size > 0

        # Phase 1: Load all configuration from JSON. This will populate _initial_* sets/dict.
        self._load_config_from_json()

        # Phase 2: Process dynamically generated paths (from args.paths)
        if paths:
            for p_str in paths:
                p_resolved = Path(p_str).resolve()

                if self._is_blacklisted_by_generator_pattern(p_resolved):
                    print(f"[DEBUG] Generated path '{p_resolved}' matched blacklist pattern, skipping.")
                    continue

                if p_resolved.exists() and p_resolved not in self._ignored_paths:
                    self._generated_paths.add(p_resolved)
                elif not p_resolved.exists():
                    print(f"[WARNING] Generated path '{p_resolved}' does not exist, skipping.")

        print(f"[DEBUG] Workspace initialized: Generated={len(self._generated_paths)}, User={len(self._user_paths)}, Ignored={len(self._ignored_paths)}, Blacklist Patterns={len(self._generator_blacklist_patterns)}")

    def _load_config_from_json(self):
        """Helper to load all configuration aspects (user_paths, ignored_paths, blacklist, and state_config) from JSON."""
        if not self.json_file.exists() or self.json_file.stat().st_size == 0:
            print(f"[DEBUG] Workspace JSON file '{self.json_file}' not found or is empty.")
            # Set initial config to defaults if file is empty/non-existent
            self._initial_user_paths = set()
            self._initial_ignored_paths = set()
            self._initial_generator_blacklist_patterns = []
            self._initial_state_config = self._get_default_state_config() # Use default state config for comparison
            return
        
        try:
            with open(self.json_file, "r") as f:
                fcntl.flock(f, fcntl.LOCK_SH)
                data = json.load(f)
                fcntl.flock(f, fcntl.LOCK_UN)
            
            # Load Workspace-specific config
            loaded_user_paths: Set[Path] = set()
            for p_str in data.get("user_paths", []):
                p_resolved = Path(p_str).resolve()
                if p_resolved.exists():
                    loaded_user_paths.add(p_resolved)
                else:
                    print(f"[WARNING] User path '{p_resolved}' from {self.json_file} does not exist on load, skipping.")

            loaded_ignored_paths: Set[Path] = set(Path(p).resolve() for p in data.get("ignored_paths", []))
            loaded_patterns: List[str] = data.get("generator_blacklist_patterns", [])

            # Populate current workspace sets
            self._user_paths.update(loaded_user_paths)
            self._ignored_paths.update(loaded_ignored_paths)
            self._generator_blacklist_patterns.extend(loaded_patterns)

            # Populate initial (loaded) state for dirty checking
            self._initial_user_paths.update(loaded_user_paths)
            self._initial_ignored_paths.update(loaded_ignored_paths)
            self._initial_generator_blacklist_patterns.extend(loaded_patterns)

            # Load State-specific config
            loaded_state_config: dict = data.get("state_config", {})
            self._initial_state_config = self._merge_with_default_state_config(loaded_state_config)
            
            print(f"[DEBUG] Loaded {len(self._user_paths)} user paths, {len(self._ignored_paths)} ignored paths, {len(self._generator_blacklist_patterns)} blacklist patterns, and State config from '{self.json_file}'.")

        except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
            print(f"[WARNING] Could not load workspace.json: {e}. Starting with fresh configuration.")
            # Ensure _initial_* capture defaults if load failed
            self._initial_user_paths = set()
            self._initial_ignored_paths = set()
            self._initial_generator_blacklist_patterns = []
            self._initial_state_config = self._get_default_state_config() # Use default state config for comparison

    def _get_default_state_config(self) -> dict:
        """Returns a dictionary representing the default values for the persistable State attributes."""
        return {
            "use_gitignore": True,
            "include_dotfiles": False,
            "search_dirs_only": False,
            "search_files_only": False,
            "regex_mode": False,
            "regex_pattern": "",
            "root_dir": None,
            "clipboard_queue": [],
            "auto_save_enabled": False,
        }

    def _merge_with_default_state_config(self, loaded_config: dict) -> dict:
        """Merges loaded state config with defaults to ensure all keys are present."""
        default_config = self._get_default_state_config()
        merged_config = default_config.copy()
        # Update with loaded values, overriding defaults
        for key, value in loaded_config.items():
            if key == "root_dir" and value is not None:
                # Ensure root_dir is stored as a string in config, Path when in State
                merged_config[key] = str(Path(value).resolve())
            elif key == "clipboard_queue":
                # Ensure clipboard queue paths are stored as strings in config
                merged_config[key] = [str(Path(p).resolve()) for p in value]
            else:
                merged_config[key] = value
        return merged_config

    def _is_blacklisted_by_generator_pattern(self, path: Path) -> bool:
        """Checks if a path matches any of the generator blacklist regex patterns."""
        path_str = str(path)
        for pattern in self._generator_blacklist_patterns:
            try:
                if re.search(pattern, path_str):
                    return True
            except re.error as e:
                print(f"[ERROR] Invalid regex pattern in blacklist: '{pattern}' - {e}")
        return False

    def save(self, json_file_path: Path = None):
        """Saves the current workspace state (paths, blacklist, and state config) to the JSON file."""
        if json_file_path:
            self.json_file = json_file_path.resolve()
            print(f"[INFO] Workspace file path updated to: {self.json_file}")

        tmp_path = self.json_file.with_suffix(".tmp")
        try:
            with open(tmp_path, "w") as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                
                data_to_save = {
                    "user_paths": [str(p) for p in sorted(list(self._user_paths))],
                    "ignored_paths": [str(p) for p in sorted(list(self._ignored_paths))],
                    "generator_blacklist_patterns": self._generator_blacklist_patterns
                }
                
                # Add state configuration if state object is linked
                if hasattr(self, 'state') and self.state is not None:
                    data_to_save["state_config"] = self.state.get_persistable_config()

                json.dump(data_to_save, f, indent=2)
                f.flush()
                fcntl.flock(f, fcntl.LOCK_UN)
            
            tmp_path.rename(self.json_file)
            print(f"[INFO] Workspace saved to: {self.json_file}. User paths: {len(self._user_paths)}, Ignored paths: {len(self._ignored_paths)}, Blacklist patterns: {len(self._generator_blacklist_patterns)}")
            
            # Clear dirty flag after successful save
            if hasattr(self, 'state') and self.state is not None:
                self.state.is_dirty = False

        except Exception as e:
            print(f"[ERROR] Failed to save workspace to {self.json_file}: {e}")
            if tmp_path.exists():
                tmp_path.unlink()

    def _mark_dirty_and_auto_save(self):
        """Helper to mark the state as dirty and trigger auto-save if enabled."""
        if hasattr(self, 'state') and self.state is not None:
            self.state.is_dirty = True
            self.state.autoSave(self.save) # This will call workspace.save() and clear dirty flag
        else:
            print("[WARNING] Workspace's state object is not set. Cannot mark dirty or auto-save via state.")

    def add_generator_blacklist_pattern(self, pattern: str):
        if pattern not in self._generator_blacklist_patterns:
            self._generator_blacklist_patterns.append(pattern)
            self._mark_dirty_and_auto_save()
            print(f"[DEBUG] Added generator blacklist pattern: '{pattern}'.")

    def remove_generator_blacklist_pattern(self, pattern: str):
        if pattern in self._generator_blacklist_patterns:
            self._generator_blacklist_patterns.remove(pattern)
            self._mark_dirty_and_auto_save()
            print(f"[DEBUG] Removed generator blacklist pattern: '{pattern}'.")

    def get_generator_blacklist_patterns(self) -> List[str]: # Type hint corrected
        return self._generator_blacklist_patterns.copy()

    def add(self, entries: List[str], root_dir: Path = None): # Type hints corrected
        root = Path(root_dir) if root_dir else self.cwd
        added_count = 0
        for entry in entries:
            full_path = (root / entry).resolve()
            if full_path.exists() and full_path not in self._user_paths:
                self._user_paths.add(full_path)
                if full_path in self._ignored_paths:
                    self._ignored_paths.discard(full_path)
                added_count += 1
        if added_count > 0:
            self._mark_dirty_and_auto_save()
            print(f"[INFO] Added {added_count} paths to workspace.")

    def remove(self, entries: List[str], root_dir: Path = None): # Type hints corrected
        root = Path(root_dir) if root_dir else self.cwd
        removed_count = 0
        for entry in entries:
            full_path = (root / entry).resolve()
            if full_path in self._user_paths:
                self._user_paths.discard(full_path)
                self._ignored_paths.add(full_path)
                removed_count += 1
            elif full_path in self._generated_paths:
                 self._generated_paths.discard(full_path)
                 self._ignored_paths.add(full_path)
                 removed_count += 1
        if removed_count > 0:
            self._mark_dirty_and_auto_save()
            print(f"[INFO] Removed {removed_count} paths from workspace (added to ignored list).")

    def list(self) -> List[Path]: # Type hint corrected
        """Returns a sorted list of all active paths in the workspace."""
        active_paths = (self._user_paths | self._generated_paths) - self._ignored_paths
        return sorted(list(active_paths))

    def list_workspace_files(self) -> List[Path]: # Type hint corrected
        """Returns a sorted list of all active file paths in the workspace."""
        return sorted(p for p in self.list() if p.is_file())

    def list_directories(self) -> List[Path]: # Type hint corrected
        """Returns a sorted list of all active directory paths in the workspace."""
        return sorted(p for p in self.list() if p.is_dir())
    
    def expand_directories(self):
        # This method's implementation would depend on your expansion logic
        pass

    def reset(self):
        self._user_paths.clear()
        self._generated_paths.clear()
        self._ignored_paths.clear()
        self._generator_blacklist_patterns.clear()
        self._mark_dirty_and_auto_save()
        print("[INFO] Workspace reset (all paths and blacklist patterns cleared).")

    def get_current_json_file_path(self) -> Path: # Type hint corrected
        return self.json_file

    def setState(self, state):
        """Sets the state object and then determines if the workspace is initially dirty."""
        self.state = state
        self.state.apply_config(self._initial_state_config)
        self._determine_initial_dirty_state()
        
    def _determine_initial_dirty_state(self):
        """Determines if the workspace should be marked dirty immediately after initialization
        based on loaded JSON, command-line input, and existing file system state."""
        
        is_dirty_flag = False

        # 1. Check for changes in Workspace-specific config (user paths, ignored, blacklist)
        if self._user_paths != self._initial_user_paths or \
           self._ignored_paths != self._initial_ignored_paths or \
           set(self._generator_blacklist_patterns) != set(self._initial_generator_blacklist_patterns):
            is_dirty_flag = True
            print("[DEBUG] Initial dirty state reason: Workspace config loaded from JSON differs from in-memory (filtering/changes).")

        # 2. Check if command-line input paths introduced new active paths
        if not is_dirty_flag and self._generated_paths:
            if not self._initial_json_file_exists or \
               any(p not in self._initial_user_paths for p in self._generated_paths):
                is_dirty_flag = True
                print("[DEBUG] Initial dirty state reason: New generated paths introduced via CLI input or JSON was empty.")
        
        # 3. Check for changes in State-specific config
        if not is_dirty_flag and hasattr(self, 'state') and self.state is not None:
            current_state_config = self.state.get_persistable_config()
            
            # Ensure consistency for comparison: convert Paths to strings in current config
            current_state_config_comparable = current_state_config.copy()
            if "root_dir" in current_state_config_comparable and current_state_config_comparable["root_dir"] is not None:
                 current_state_config_comparable["root_dir"] = str(current_state_config_comparable["root_dir"])
            current_state_config_comparable["clipboard_queue"] = [str(p) for p in current_state_config_comparable.get("clipboard_queue", [])]

            # Compare with the initial loaded state config
            # _initial_state_config is already in a comparable string format from _load_config_from_json
            if current_state_config_comparable != self._initial_state_config:
                is_dirty_flag = True
                print("[DEBUG] Initial dirty state reason: State configuration differs from loaded JSON or defaults.")
        
        if hasattr(self, 'state') and self.state is not None:
            self.state.is_dirty = is_dirty_flag
            if self.state.is_dirty:
                print("[DEBUG] Workspace is marked as initially dirty.")
            else:
                print("[DEBUG] Workspace is initially clean.")
        else:
            print("[WARNING] State object not available to set initial dirty flag.")
    
    def autoSave(self):
        if hasattr(self, 'state') and self.state is not None:
            return self.state.autoSave(self.save)
        else:
            print("[ERROR] Workspace's state object is not set. Cannot auto-save.")

