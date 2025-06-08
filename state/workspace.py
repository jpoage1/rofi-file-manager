# workspace.py
import json
import fcntl
from pathlib import Path
import re

class Workspace:
    def __init__(self, json_file=None, paths=None, cwd=None):
        self.cwd = Path(cwd).resolve() if cwd else Path.cwd().resolve()
        self.json_file = Path(json_file if json_file else "workspace.json")

        # Internal sets to manage different categories of paths
        self._generated_paths = set()  # Paths from the dynamic generator (args.paths)
        self._user_paths = set()       # Paths explicitly added/managed by the user
        self._ignored_paths = set()    # Paths explicitly removed by the user (blacklist of individual paths)
        self._generator_blacklist_patterns = [] # NEW: List of regex patterns for generator output

        # Phase 1: Load all configuration (user paths, ignored paths, AND generator blacklist) from JSON
        self._load_config_from_json()

        # Phase 2: Process dynamically generated paths (from args.paths)
        if paths:
            for p_str in paths:
                p_resolved = Path(p_str).resolve() # Always work with resolved paths for consistency

                # --- NEW: Apply the generator blacklist here ---
                if self._is_blacklisted_by_generator_pattern(p_resolved):
                    print(f"[DEBUG] Generated path '{p_resolved}' matched blacklist pattern, skipping.")
                    continue
                # --- END NEW ---

                if p_resolved.exists() and p_resolved not in self._ignored_paths:
                    self._generated_paths.add(p_resolved)
                elif not p_resolved.exists():
                    print(f"[WARNING] Generated path '{p_resolved}' does not exist, skipping.")

        print(f"[DEBUG] Workspace initialized: Generated={len(self._generated_paths)}, User={len(self._user_paths)}, Ignored={len(self._ignored_paths)}, Blacklist Patterns={len(self._generator_blacklist_patterns)}")
    def _load_config_from_json(self):
        """Helper to load all configuration aspects (user_paths, ignored_paths, blacklist) from JSON."""
        if not self.json_file.exists():
            return
        try:
            with open(self.json_file, "r") as f:
                fcntl.flock(f, fcntl.LOCK_SH)
                data = json.load(f)
                fcntl.flock(f, fcntl.LOCK_UN)
            
            # Load user paths
            for p_str in data.get("user_paths", []):
                p_resolved = Path(p_str).resolve()
                if p_resolved.exists(): # Only add if it still exists
                    self._user_paths.add(p_resolved)
                else:
                    print(f"[WARNING] User path '{p_resolved}' from {self.json_file} does not exist, skipping.")

            # Load ignored paths (individual paths explicitly removed by user)
            self._ignored_paths.update(Path(p).resolve() for p in data.get("ignored_paths", []))

            # --- NEW: Load generator blacklist patterns ---
            self._generator_blacklist_patterns = data.get("generator_blacklist_patterns", [])
            # Validate patterns if desired, e.g., compile them now for efficiency and error checking
            # self._compiled_blacklist_patterns = [re.compile(p) for p in self._generator_blacklist_patterns]
            # (Decided to compile on demand in _is_blacklisted_by_generator_pattern for simplicity in this example)
            # --- END NEW ---
            
            print(f"[DEBUG] Loaded {len(self._user_paths)} user paths, {len(self._ignored_paths)} ignored paths, and {len(self._generator_blacklist_patterns)} blacklist patterns from '{self.json_file}'.")

        except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
            print(f"[WARNING] Could not load workspace.json: {e}. Starting with fresh configuration.")
            # Ensure internal sets are clean if load failed
            self._generated_paths.clear()
            self._user_paths.clear()
            self._ignored_paths.clear()
            self._generator_blacklist_patterns.clear() # Clear blacklist patterns too


    # --- NEW HELPER METHOD ---
    def _is_blacklisted_by_generator_pattern(self, path: Path) -> bool:
        """Checks if a path matches any of the generator blacklist regex patterns."""
        path_str = str(path) # Convert Path to string for regex matching
        for pattern in self._generator_blacklist_patterns:
            try:
                # Use re.search for substring matching, re.fullmatch for exact match
                if re.search(pattern, path_str):
                    return True
            except re.error as e:
                print(f"[ERROR] Invalid regex pattern in blacklist: '{pattern}' - {e}")
                # Decide how to handle invalid patterns: skip, or treat as if no match
                # For now, we'll continue to the next pattern, effectively ignoring the bad one.
        return False
    # --- END NEW HELPER METHOD ---

    def save(self, json_file_path: Path = None): # Make json_file_path optional
        if json_file_path:
            # If a new path is provided, update self.json_file
            self.json_file = json_file_path.resolve()
            print(f"[INFO] Workspace file path updated to: {self.json_file}")

        tmp_path = self.json_file.with_suffix(".tmp")
        try:
            with open(tmp_path, "w") as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                json.dump({
                    "user_paths": [str(p) for p in sorted(list(self._user_paths))],
                    "ignored_paths": [str(p) for p in sorted(list(self._ignored_paths))],
                    "generator_blacklist_patterns": self._generator_blacklist_patterns
                }, f, indent=2)
                f.flush()
                fcntl.flock(f, fcntl.LOCK_UN)
            tmp_path.rename(self.json_file)
            print(f"[INFO] Workspace saved to: {self.json_file}. User paths: {len(self._user_paths)}, Ignored paths: {len(self._ignored_paths)}, Blacklist patterns: {len(self._generator_blacklist_patterns)}")
        except Exception as e:
            print(f"[ERROR] Failed to save workspace to {self.json_file}: {e}")
            # Attempt to clean up temp file if error occurs
            if tmp_path.exists():
                tmp_path.unlink()
    
    # Add new methods to manage the blacklist patterns from your application/UI
    def add_generator_blacklist_pattern(self, pattern: str):
        if pattern not in self._generator_blacklist_patterns:
            self._generator_blacklist_patterns.append(pattern)
            self.save()
            print(f"[DEBUG] Added generator blacklist pattern: '{pattern}'.")

    def remove_generator_blacklist_pattern(self, pattern: str):
        if pattern in self._generator_blacklist_patterns:
            self._generator_blacklist_patterns.remove(pattern)
            self.save()
            print(f"[DEBUG] Removed generator blacklist pattern: '{pattern}'.")
            # Note: Removing a blacklist pattern won't automatically add previously
            # ignored paths from the generator. They would only be added on the
            # next app restart when the generator runs again.

    def get_generator_blacklist_patterns(self) -> list[str]:
        return self._generator_blacklist_patterns.copy() # Return a copy to prevent external modification

    # The add(), remove(), list(), and reset() methods remain the same as previously defined.
    # Their logic already correctly interacts with _generated_paths, _user_paths, and _ignored_paths.

    # def load(self):
    #     if not self.json_file.exists():
    #         return
    #     with open(self.json_file, "r") as f:
    #         fcntl.flock(f, fcntl.LOCK_SH)
    #         data = json.load(f)
    #         fcntl.flock(f, fcntl.LOCK_UN)
    #     self.paths.update(Path(p) for p in data.get("paths", []))
        
    # def save(self):
    #     tmp_path = self.json_file.with_suffix(".tmp")
    #     with open(tmp_path, "w") as f:
    #         fcntl.flock(f, fcntl.LOCK_EX)
    #         json.dump({"paths": [str(p) for p in self.paths]}, f, indent=2)
    #         f.flush()
    #         fcntl.flock(f, fcntl.LOCK_UN)
    #     tmp_path.rename(self.json_file)

    def add(self, entries, root_dir=None):
        root = Path(root_dir) if root_dir else self.cwd
        for entry in entries:
            full_path = root / entry
            if full_path.exists():
                self.paths.add(full_path)
        self.save()

    def remove(self, entries, root_dir=None):
        root = Path(root_dir) if root_dir else self.cwd
        for entry in entries:
            full_path = (root / entry).resolve()
            self.paths.discard(full_path)
        self.save()

    def list(self):
        return sorted(self.paths)

    def list_workspace_files(self):
        return sorted(p for p in self.paths if p.is_file())

    def list_directories(self):
        return sorted(p for p in self.paths if p.is_dir())
    
    def expand_directories():
        pass

    def reset(self):
        self.paths.clear()
        self.save() 

    def get_current_json_file_path(self):
        return self.json_file
