# core/workspace.py
import json
import fcntl
from pathlib import Path
import re
from typing import List, Set
import hashlib
import logging

from watchdog.observers import Observer
import threading

from menu_manager.watcher import CacheUpdater

from filters.gitignore import is_ignored_by_stack
from filters.path_utils import resolve_path_and_inode
from filters.filtering import filter_entries
from filters.main import expand_directories, get_gitignore_specs

class Workspace:
    def __init__(self, json_file=None, paths=None, cwd=None):
        self.state = None
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
        self._last_loaded_hash: str | None = None # Initialize hash tracking


        self.cache: set[str] = set()  # cached paths (canonical strings)
        self.cache_file = Path('.cache.json')
        self.cache_lock = threading.RLock()
        self.observer = None

        # Phase 1: Load all configuration from JSON. This will populate _initial_* sets/dict.
        self._load_config_from_json()

        # Phase 2: Process dynamically generated paths (from args.paths)
        if paths:
            for p_str in paths:
                p_resolved = Path(p_str).resolve()

                if self._is_blacklisted_by_generator_pattern(p_resolved):
                    logging.debug(f"Generated path '{p_resolved}' matched blacklist pattern, skipping.")
                    continue

                if p_resolved.exists() and p_resolved not in self._ignored_paths:
                    self._generated_paths.add(p_resolved)
                elif not p_resolved.exists():
                    logging.warning(f" Generated path '{p_resolved}' does not exist, skipping.")

        logging.debug(f"Workspace initialized: Generated={len(self._generated_paths)}, User={len(self._user_paths)}, Ignored={len(self._ignored_paths)}, Blacklist Patterns={len(self._generator_blacklist_patterns)}")

    def _load_config_from_json(self):
        """Helper to load all configuration aspects (user_paths, ignored_paths, blacklist, and state_config) from JSON."""
        # Calculate hash first for comparison *before* trying to load
        current_file_hash_on_disk = self._calculate_file_hash(self.json_file)

        if not self.json_file.exists() or self.json_file.stat().st_size == 0:
            logging.debug(f"Workspace JSON file '{self.json_file}' not found or is empty.")
            # Set initial config to defaults if file is empty/non-existent
            self._initial_user_paths = set()
            self._initial_ignored_paths = set()
            self._initial_generator_blacklist_patterns = []
            self._initial_state_config = self._get_default_state_config()
            self._last_loaded_hash = None # No file, no hash
            
            # Clear current runtime sets as well, in case of a reload to empty
            self._user_paths.clear()
            self._ignored_paths.clear()
            self._generator_blacklist_patterns.clear()
            self._generated_paths.clear() # Generated paths are *not* loaded from JSON, clear on full reload
            return
        
        try:
            with open(self.json_file, "r") as f:
                fcntl.flock(f, fcntl.LOCK_SH)
                data = json.load(f)
                fcntl.flock(f, fcntl.LOCK_UN)
            
            # Clear current workspace sets *before* populating to ensure a fresh state on reload
            self._user_paths.clear()
            self._ignored_paths.clear()
            self._generator_blacklist_patterns.clear()
            self._generated_paths.clear() # Always clear generated paths, they are only for current session CLI input

            # Load Workspace-specific config
            loaded_user_paths: Set[Path] = set()
            for p_str in data.get("user_paths", []):
                p_resolved = Path(p_str).resolve()
                if p_resolved.exists():
                    loaded_user_paths.add(p_resolved)
                else:
                    logging.warning(f" User path '{p_resolved}' from {self.json_file} does not exist on load, skipping.")

            loaded_ignored_paths: Set[Path] = set(Path(p).resolve() for p in data.get("ignored_paths", []))
            loaded_patterns: List[str] = data.get("generator_blacklist_patterns", [])

            # Populate current workspace sets with loaded data
            self._user_paths.update(loaded_user_paths)
            self._ignored_paths.update(loaded_ignored_paths)
            self._generator_blacklist_patterns.extend(loaded_patterns)

            # Populate initial (loaded) state for dirty checking (these are copies of what was just loaded)
            self._initial_user_paths = loaded_user_paths.copy()
            self._initial_ignored_paths = loaded_ignored_paths.copy()
            self._initial_generator_blacklist_patterns = loaded_patterns.copy()

            # Load State-specific config
            loaded_state_config: dict = data.get("state_config", {})
            self._initial_state_config = self._merge_with_default_state_config(loaded_state_config)
            
            # Update the last loaded hash after successful load
            self._last_loaded_hash = current_file_hash_on_disk

            logging.debug(f"Loaded {len(self._user_paths)} user paths, {len(self._ignored_paths)} ignored paths, {len(self._generator_blacklist_patterns)} blacklist patterns, and State config from '{self.json_file}'.")

        except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
            logging.warning(f" Could not load workspace.json: {e}. Starting with fresh configuration.")
            # Ensure _initial_* capture defaults if load failed
            self._initial_user_paths = set()
            self._initial_ignored_paths = set()
            self._initial_generator_blacklist_patterns = []
            self._initial_state_config = self._get_default_state_config()
            self._last_loaded_hash = None # Clear hash if load failed (as file content is unreliable)
            
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
            logging.info(f"Workspace file path updated to: {self.json_file}")

        tmp_path = self.json_file.with_suffix(".tmp")
        try:
            with open(tmp_path, "w") as f:
                fcntl.flock(f, fcntl.LOCK_EX) # Exclusive lock for writing
                
                # Consolidate all non-ignored paths first
                current_potential_active_paths = (self._user_paths | self._generated_paths) - self._ignored_paths
                
                # Further filter by generator blacklist patterns
                final_paths_to_save = set()
                for p in current_potential_active_paths:
                    if not self._is_blacklisted_by_generator_pattern(p):
                        final_paths_to_save.add(p)

                data_to_save = {
                    "user_paths": [str(p) for p in sorted(list(final_paths_to_save))], # CHANGED: Now reflects all filters
                    "ignored_paths": [str(p) for p in sorted(list(self._ignored_paths))],
                    "generator_blacklist_patterns": self._generator_blacklist_patterns
                }
                
                if hasattr(self, 'state') and self.state is not None:
                    data_to_save["state_config"] = self.state.get_persistable_config()

                json.dump(data_to_save, f, indent=2)
                f.flush() # Ensure data is written to disk before unlocking/renaming
                fcntl.flock(f, fcntl.LOCK_UN)
            
            tmp_path.rename(self.json_file) # Atomic rename
            logging.info(f"Workspace saved to: {self.json_file}. User paths: {len(self._user_paths)}, Ignored paths: {len(self._ignored_paths)}, Blacklist patterns: {len(self._generator_blacklist_patterns)}")
            
            # Update the last loaded hash after successful save
            self._last_loaded_hash = self._calculate_file_hash(self.json_file)

            # Clear dirty flag after successful save
            if hasattr(self, 'state') and self.state is not None:
                self.state.is_dirty = False

        except Exception as e:
            print(f"[ERROR] Failed to save workspace to {self.json_file}: {e}")
            if tmp_path.exists():
                tmp_path.unlink() # Clean up temp file on error

    def _mark_dirty_and_auto_save(self):
        """Helper to mark the state as dirty and trigger auto-save if enabled."""
        if hasattr(self, 'state') and self.state is not None:
            self.state.is_dirty = True
            self.state.autoSave(self.save) # This will call workspace.save() and clear dirty flag
        else:
            logging.warning("[WARNING] Workspace's state object is not set. Cannot mark dirty or auto-save via state.")

    def add_generator_blacklist_pattern(self, pattern: str):
        if pattern not in self._generator_blacklist_patterns:
            self._generator_blacklist_patterns.append(pattern)
            self._mark_dirty_and_auto_save()
            logging.debug(f"Added generator blacklist pattern: '{pattern}'.")

    def remove_generator_blacklist_pattern(self, pattern: str):
        if pattern in self._generator_blacklist_patterns:
            self._generator_blacklist_patterns.remove(pattern)
            self._mark_dirty_and_auto_save()
            logging.debug(f"Removed generator blacklist pattern: '{pattern}'.")

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
            logging.info(f"Added {added_count} paths to workspace.")

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
            logging.info(f"Removed {removed_count} paths from workspace (added to ignored list).")

    def _calculate_file_hash(self, file_path: Path) -> str | None:
        """Calculates the SHA256 hash of the given file's content."""
        if not file_path.exists():
            return None
        
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                # Read in chunks to handle potentially large files efficiently
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            print(f"[ERROR] Failed to calculate hash for {file_path}: {e}")
            return None

    def _check_for_external_changes_and_reload(self):
        """
        Checks if the workspace file on disk has changed externally.
        If it has, reloads the configuration from the file.
        """
        if not self.json_file.exists():
            # If file disappeared, treat as changed or fresh start
            if self._last_loaded_hash is not None:
                logging.info(f"Workspace file '{self.json_file}' no longer exists; reloading to empty state.")
                self._load_config_from_json() # Will effectively clear internal state
            return

        current_file_hash = self._calculate_file_hash(self.json_file)

        if current_file_hash is None: # Error calculating hash, assume no change or handle as error
            return

        if self._last_loaded_hash != current_file_hash:
            logging.info(f"Workspace file '{self.json_file}' has changed externally. Reloading configuration.")
            self._load_config_from_json() # This method also updates self._last_loaded_hash

    def list(self) -> List[Path]:
        self._check_for_external_changes_and_reload() # Ensure current state before reading
        """Returns a sorted list of all active paths in the workspace, applying all filters."""
        # Start with all user and generated paths, remove individually ignored ones
        all_potential_paths = (self._user_paths | self._generated_paths) - self._ignored_paths
        
        # Now, filter out paths that match any generator blacklist pattern
        active_paths = set()
        for p in all_potential_paths:
            if not self._is_blacklisted_by_generator_pattern(p):
                active_paths.add(p)
        return list(active_paths)

    
    def list_workspace_files(self) -> Set[Path]:
        return {p for p in self.list() if p.is_file()}

    def list_directories(self) -> Set[Path]:
        return {p for p in self.list() if p.is_dir()}

    def list_paths(self) -> Set[Path]:
        return self.list_directories().union(self.list_workspace_files())

    def reset(self):
        self._user_paths.clear()
        self._generated_paths.clear()
        self._ignored_paths.clear()
        self._generator_blacklist_patterns.clear()
        self._mark_dirty_and_auto_save()
        logging.info("[INFO] Workspace reset (all paths and blacklist patterns cleared).")

    def get_current_json_file_path(self) -> Path: # Type hint corrected
        return self.json_file

    # def set_state(self, state):
    #     """Sets the state object and then determines if the workspace is initially dirty."""
    #     self.state = state
    #     self.state.apply_config(self._initial_state_config)
    #     self._determine_initial_dirty_state()

    #     import time
    #     start = time.perf_counter()
    #     state.cache = self.build_cache()
    #     end = time.perf_counter()
    #     from menu_manager.payload import write_log
    #     write_log(f"build_cache: Execution time: {end - start:.6f} seconds")

    #     self.watcher = self.start_file_watcher()

    def set_state(self, state):
        """Sets the state object and then determines if the workspace is initially dirty."""
        self.state = state
        self.state.apply_config(self._initial_state_config)
        from core.payload import get_timestamp
        # print(f"Building cache at {get_timestamp()}")

    def initialize_cache(self):
        self._determine_initial_dirty_state()
        self.cache = self._load_or_build_cache()
        self.start_file_watcher()
        self._validate_cache

    def _load_or_build_cache(self):
        if self.cache_file.exists():
            try:
                text = self.cache_file.read_text()
                return set(json.loads(text))
            except:
                return set()
        else:
            cache = self.build_cache()
            cache_set = set(str(p) for p in cache)
            self._save_cache(cache_set)
            return cache_set

    def _save_cache(self):
        text = json.dumps(self.cache)
        self.cache_file.write_text(text)

    def _validate_cache(self):
        from state.scanner import validate_cache_against_fs
        updated = validate_cache_against_fs(self.cache, self.list_directories(), self.list_directories())
        if updated:
            self._save_cache()


    def _determine_initial_dirty_state(self):
            """
            Determines if the workspace should be marked dirty immediately after initialization
            based on loaded JSON, command-line input, and existing file system state.
            """
            
            is_dirty_flag = False

            # 1. Check for changes in Workspace-specific config (user paths, ignored, blacklist)
            # If in-memory (current) is different from what was loaded from JSON, it's dirty.
            if self._user_paths != self._initial_user_paths or \
            self._ignored_paths != self._initial_ignored_paths or \
            set(self._generator_blacklist_patterns) != set(self._initial_generator_blacklist_patterns):
                is_dirty_flag = True
                logging.debug("Initial dirty state reason: Workspace config loaded from JSON differs from in-memory (e.g., paths filtered out or modified before setState).")

            # 2. Check if command-line input paths introduced new active paths
            # If 'generated_paths' exist (from CLI) AND they aren't already part of 'user_paths' from JSON,
            # then the workspace state is conceptually "dirty" because CLI paths are not saved.
            if not is_dirty_flag and self._generated_paths:
                
                # --- START NEW DEBUGGING CODE ---
                logging.debug("Checking for new generated paths:")
                logging.debug(f"  _generated_paths: {self._generated_paths}")
                logging.debug(f"  _initial_json_file_exists: {self._initial_json_file_exists}")
                logging.debug(f"  _initial_user_paths: {self._initial_user_paths}")

                paths_not_in_initial_user_paths = [
                    p for p in self._generated_paths if p not in self._initial_user_paths
                ]
                if paths_not_in_initial_user_paths:
                    print(f"  Generated paths NOT found in _initial_user_paths: {paths_not_in_initial_user_paths}")
                # --- END NEW DEBUGGING CODE ---

                if not self._initial_json_file_exists or \
                any(p not in self._initial_user_paths for p in self._generated_paths):
                    is_dirty_flag = True
                    logging.debug("Initial dirty state reason: New generated paths introduced via CLI input or JSON was empty.")
            
            # 3. Check for changes in State-specific config
            if not is_dirty_flag and hasattr(self, 'state') and self.state is not None:
                current_state_config = self.state.get_persistable_config()
                
                # --- START NEW DEBUGGING CODE ---
                # Added a print here for state config comparison for future debugging if needed
                logging.debug("Checking State config consistency:")
                logging.debug(f"  Current persistable State config: {current_state_config}")
                logging.debug(f"  Initial loaded State config: {self._initial_state_config}")
                # --- END NEW DEBUGGING CODE ---

                if current_state_config != self._initial_state_config:
                    is_dirty_flag = True
                    logging.debug("Initial dirty state reason: State configuration differs from loaded JSON or defaults.")
            
            # Final status report
            if hasattr(self, 'state') and self.state is not None:
                self.state.is_dirty = is_dirty_flag
                if self.state.is_dirty:
                    logging.debug("Workspace is marked as initially dirty.")
                else:
                    logging.debug("Workspace is initially clean.")
            else:
                logging.warning("State object not available to set initial dirty flag.")
    
    def autoSave(self):
        if hasattr(self, 'state') and self.state is not None:
            return self.state.autoSave(self.save)
        else:
            logging.error("[ERROR] Workspace's state object is not set. Cannot auto-save.")

    def build_cache(self):
        state = self.state
        logging.debug("build_greedy_cache: Starting full workspace scan and caching.")
        workspace_roots = list(state.workspace.list_directories())
        processed_root_inodes = set()
        project_root_for_gitignore = Path.cwd()
        global_gitignore_specs = get_gitignore_specs(project_root_for_gitignore, state.use_gitignore)

        cache = []

        for root in workspace_roots:
            canonical_path, inode_key = resolve_path_and_inode(root)
            if not canonical_path or not inode_key or inode_key in processed_root_inodes:
                continue
            processed_root_inodes.add(inode_key)

            if state.use_gitignore and is_ignored_by_stack(root, global_gitignore_specs):
                continue

            visited_inodes = set()
            root_entries = [root]

            expanded = expand_directories(
                root_entries,
                state,
                current_depth=0,
                active_gitignore_specs=global_gitignore_specs,
                visited_inodes_for_current_traversal=visited_inodes
            )
            cache.extend(expanded)

        cache.extend(self.list_files)
        logging.debug(f"build_greedy_cache: Cached {len(cache)} entries total.")
        return sorted(cache)

    def query_from_cache(self):
        cache = self.cache
        logging.debug(f"query_from_cache: Filtering {len(cache)} cached entries.")
        filtered = filter_entries(cache, self.get_state())
        logging.debug(f"query_from_cache: Filtered down to {len(filtered)} entries.")
        return filtered
    
    def get_state(self):
        if not self.state:
            print("State not initialized")
            exit(1)
        return self.state
    
    def update_file_watcher(self):
        self.watcher.stop()
        self.watcher.join()  # ensure thread terminates
        self.watcher = self.start_file_watcher()
    
    def start_file_watcher(self):
        event_handler = CacheUpdater(self.cache)
        observer = Observer()
        root_paths = list(self.state.workspace.list())
        for root_path in root_paths:
            observer.schedule(event_handler, str(root_path), recursive=True)
        observer_thread = threading.Thread(target=observer.start, daemon=True)
        observer_thread.start()
        return observer
    


