# plugins/workspace_management.py
from pathlib import Path
import re
import logging
import threading
from core.filesystem import list_files

from core.plugin_base import WorkspacePlugin, SubMenu, MenuEntry, TreeEntry
# logging.basicConfig(level=logging.DEBUG)

class WorkspaceManager(WorkspacePlugin):
    priority = 30
    
    def __init__(self, menu, state):
        super().__init__(menu, state)
        self.state.update({
            "workspace_files": set(),
            # "workspace": workspace or Workspace("workspace.json"),
            "is_dirty": False,
            "auto_save_enabled": False
        })
        self.workspace = state.workspace
        self.cache = self.workspace.cache
        self.watcher = self.start_file_watcher()
        
    def _build_menu(self) -> SubMenu:
        save_status = (
            " (Auto-Save ON)" if self.state.auto_save_enabled else
            " (Unsaved Changes)" if self.state.is_dirty else
            " (Saved)"
        )
        options = [
            TreeEntry(self.get_root_dir(), "Traverse to a new directory"),
            MenuEntry("Add files", action=self.add_files),
            MenuEntry("Remove files", action=self.remove_files),
            MenuEntry("Generator Blacklist", action=self.manage_generator_blacklist),
            MenuEntry("Reset Workspace", action=self.reset_workspace),
            MenuEntry(f"Save Workspace{save_status}", action=self.save_workspace),
            MenuEntry("Save Workspace As...", action=self.save_workspace_as),
            MenuEntry(f"Auto-Save: {'On' if self.state.auto_save_enabled else 'Off'}", action=self.toggle_auto_save),
        ]
        return SubMenu("Workspace Management", options)

    def manage_generator_blacklist(self) -> SubMenu:
        blacklist_menu = [
            MenuEntry("View current patterns", action=self._view_blacklist_patterns),
            MenuEntry("Add new pattern", action=self._add_blacklist_pattern),
            MenuEntry("Remove pattern", action=self._remove_blacklist_pattern),
        ]
        return SubMenu("Generator Blacklist", blacklist_menu)

    def _view_blacklist_patterns(self):
        patterns = self.state.workspace.get_generator_blacklist_patterns()
        if not patterns:
            self.menu.run_selector(["No blacklist patterns configured."], prompt="Generator Blacklist (Read-Only)")
            return
        display_patterns = [f"{i+1}. {p}" for i, p in enumerate(patterns)]
        self.menu.run_selector(display_patterns, prompt="Generator Blacklist (Read-Only)")

    def _add_blacklist_pattern(self):
        prompt_text = "Enter new regex pattern (e.g., .*/__pycache__.*)"
        new_pattern_result = self.menu.run_selector([], prompt=prompt_text)
        
        if not new_pattern_result or not new_pattern_result[0]:
            logging.debug("No new pattern entered.")
            return
        
        new_pattern = new_pattern_result[0].strip()
        if not new_pattern:
            self.menu.run_selector(["Pattern cannot be empty."], prompt="Error")
            return

        try:
            re.compile(new_pattern)
        except re.error as e:
            self.menu.run_selector([f"Invalid Regex: {e}"], prompt="Error")
            logging.error(f"[ERROR] Invalid regex pattern entered: '{new_pattern}' - {e}")
            return

        self.state.workspace.add_generator_blacklist_pattern(new_pattern)
        # Manually set dirty flag for now.
        self.state.is_dirty = True
        self.menu.run_selector([f"Pattern '{new_pattern}' added. Status updated."], prompt="Success")

    def remove_files(self):
        entries = self.state.workspace.list()
        selection = self.menu.run_selector([str(p) for p in entries], prompt="Select Files to Remove", multi_select=True)
        if selection:
            self.state.workspace.remove([entries[[str(e) for e in entries].index(s)] for s in selection])
        self.update_file_watcher()

    def add_files(self):
        root_dir = self.get_root_dir()
        entries = list_files(root_dir)
        selection = self.menu.run_selector([str(e) for e in entries], prompt="Select Files to Add", multi_select=True)
        if selection:
            self.state.workspace.add([entries[[str(e) for e in entries].index(s)] for s in selection], root_dir=root_dir)
        self.update_file_watcher()

    def _remove_blacklist_pattern(self):
        patterns = self.state.workspace.get_generator_blacklist_patterns()
        if not patterns:
            self.menu.run_selector(["No blacklist patterns to remove."], prompt="Generator Blacklist")
            return
        
        display_patterns = [f"{i+1}. {p}" for i, p in enumerate(patterns)]
        selection_list = self.menu.run_selector(display_patterns, prompt="Select pattern(s) to remove", multi_select=True)
        if not selection_list:
            logging.debug("No pattern selected for removal.")
            return

        removed_any = False
        for sel_str in selection_list:
            try:
                parts = sel_str.split(' ', 1)
                if len(parts) > 1:
                    pattern_to_remove = parts[1]
                    self.state.workspace.remove_generator_blacklist_pattern(pattern_to_remove)
                    removed_any = True
                    logging.info(f"Removed generator blacklist pattern: '{pattern_to_remove}'")
                else:
                    logging.warning(f"Could not parse selection string '{sel_str}', skipping.")
            except Exception as e:
                logging.error(f"Error removing pattern '{sel_str}': {e}")
        
        if removed_any:
            # Manually set dirty flag for now.
            self.state.is_dirty = True
            self.menu.run_selector([f"Removed pattern(s). Status updated."], prompt="Success")
        else:
            self.menu.run_selector(["No patterns removed."], prompt="Info")

    def reset_workspace(self):
        confirm_options = ["Yes, reset it", "No, keep it"]
        confirmation = self.menu.run_selector(confirm_options, prompt="Are you sure you want to reset workspace? This will clear all user-added paths and custom ignored paths.")
        if confirmation and confirmation[0] == "Yes, reset it":
            self.state.workspace.reset()
            # Manually set dirty flag for now.
            self.state.is_dirty = True
            self.menu.run_selector(["Workspace reset to generated defaults. Status updated."], prompt="Success")
            logging.info("[INFO] Workspace reset performed.")
        else:
            self.menu.run_selector(["Workspace reset cancelled."], prompt="Cancelled")
            logging.info("[INFO] Workspace reset cancelled by user.")

    def save_workspace(self):
        """Conditionally saves workspace or indicates status."""
        current_path = self.state.workspace.get_current_json_file_path()

        if self.state.auto_save_enabled:
            self.menu.run_selector([f"Auto-Save is ON. Workspace is automatically saved to {current_path}."], prompt="Auto-Save Status")
        elif self.state.is_dirty:
            confirm_options = [f"Yes, save to {current_path}", "No, cancel"]
            confirmation = self.menu.run_selector(confirm_options, prompt="Confirm Save")
            if confirmation and confirmation[0].startswith("Yes"):
                self.state.workspace.save()
                self.state.is_dirty = False # Clear dirty flag after explicit save
                self.menu.run_selector([f"Workspace saved to {current_path}"], prompt="Success")
            else:
                self.menu.run_selector(["Save cancelled."], prompt="Cancelled")
        else: # No unsaved changes and auto-save is off
            self.menu.run_selector([f"Workspace is currently saved to {current_path} (No unsaved changes)."], prompt="Save Status")

    def save_workspace_as(self):
        """Prompts user for a new path and saves the workspace there."""
        current_path = self.state.workspace.get_current_json_file_path()
        prompt_text = f"Enter new workspace file path (Current: {current_path})"
        
        new_path_result = self.menu.run_selector([], prompt=prompt_text)
        
        if not new_path_result or not new_path_result[0]:
            self.menu.run_selector(["No path entered. Save cancelled."], prompt="Cancelled")
            return
        
        new_path_str = new_path_result[0].strip()
        if not new_path_str:
            self.menu.run_selector(["Empty path entered. Save cancelled."], prompt="Cancelled")
            return

        new_path = Path(new_path_str).resolve()

        self.state.workspace.save(new_path)
        self.state.is_dirty = False # Clear dirty flag after explicit save as
        self.menu.run_selector([f"Workspace saved to new path: {new_path}"], prompt="Success")
        logging.info(f"Workspace file path changed to: {new_path}")

    def toggle_auto_save(self):
        self.state.auto_save_enabled = not self.state.auto_save_enabled
        status = "On" if self.state.auto_save_enabled else "Off"
        # self.menu.run_selector([f"Auto-Save turned {status}."], prompt="Auto-Save Status")
        logging.info(f"Auto-Save toggled to: {status}")
        # Note: We are not auto-saving here yet. That will be the next step.


    def get_root_dir(self) -> Path:
        root = self.state.root_dir or Path(".")
        if isinstance(root, str):
            root = Path(root)
        self.state.root_dir = root.resolve()
        return self.state.root_dir
    
    @staticmethod
    def list_directories(base_dir):
        base = Path(base_dir)
        try:
            return [p.name for p in base.iterdir() if p.is_dir()]
        except Exception:
            return []
        
    def _traverse_directory(base_dir):
        base = Path(base_dir)
        try:
            return [p.name for p in base.iterdir() if p.is_dir()]
        except Exception:
            return []

    def traverse_directory(self):
        while True:
            dirs = self.list_directories(self.get_root_dir())
            selection = self.menu.run_selector([str(d) for d in dirs], prompt="Select Directory")
            if not selection:
                return
            self.state.root_dir = dirs[[str(d) for d in dirs].index(selection[0])]

    def traverse_directory(self):
        while True:
            dirs = list_directories(self.state.get_root_dir())
            selection = self.menu.run_selector([str(d) for d in dirs], prompt="Select Directory")
            if not selection:
                return
            self.state.root_dir = dirs[[str(d) for d in dirs].index(selection[0])]


    # def add_files(self):
    #     root_dir = self.get_root_dir()
    #     entries = list_files(root_dir)
    #     selection = self.menu.run_selector([str(e) for e in entries], prompt="Select Files to Add", multi_select=True)
    #     if selection:
    #         self.state.workspace.add([entries[[str(e) for e in entries].index(s)] for s in selection], root_dir=root_dir)
    #     self.update_file_watcher()

    # def remove_files(self):
    #     entries = self.state.workspace.list()
    #     selection = self.menu.run_selector([str(p) for p in entries], prompt="Select Files to Remove", multi_select=True)
    #     if selection:
    #         self.state.workspace.remove([entries[[str(e) for e in entries].index(s)] for s in selection])
    #     self.update_file_watcher()
    def _mark_dirty(self):
        self.state.is_dirty = True
    def _confirm(self, prompt: str, yes="Yes", no="No") -> bool:
        response = self.menu.run_selector([yes, no], prompt=prompt)
        return bool(response) and response[0] == yes
    def _prompt_for_path(self, prompt: str) -> Path | None:
        result = self.menu.run_selector([], prompt=prompt)
        if not result:
            return None
        return Path(result[0].strip()).resolve()

    def _resolve_selection(self, selection, entries):
        index_map = {str(e): e for e in entries}
        return [index_map[s] for s in selection if s in index_map]
    
    def update_file_watcher(self):
        self.watcher.stop()
        self.watcher.join()  # ensure thread terminates
        self.watcher = self.start_file_watcher()
    
    def start_file_watcher(self):
        from core.watcher import CacheUpdater
        from watchdog.observers import Observer
        event_handler = CacheUpdater(self.cache)
        observer = Observer()
        root_paths = list(self.state.workspace.list())
        for root_path in root_paths:
            observer.schedule(event_handler, str(root_path), recursive=True)
        observer_thread = threading.Thread(target=observer.start, daemon=True)
        observer_thread.start()
        return observer
    


