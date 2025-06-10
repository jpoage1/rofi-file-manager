# plugins/workspace_management.py
from pathlib import Path
import re
import logging
from filesystem.filesystem import list_files


from core.plugin_base import WorkspacePlugin
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

    def _main_menu_entry(self):
        return {
            "name": "Workspace Management",
            "action": self._build_options,
        }
    
    def _build_options(self):
        save_status = (
            " (Auto-Save ON)" if self.state.auto_save_enabled else
            " (Unsaved Changes)" if self.state.is_dirty else
            " (Saved)"
        )
        return [
            {
                "name": "Traverse to a new directory",
                "action": self.traverse_directory,
            },
            {
                "name": "Add files",
                "action": self.add_files,
            },
            {
                "name": "Remove files",
                "action": self.remove_files,
            },
            {
                "name": "Generator Blacklist",
                "action": self.manage_generator_blacklist,
            },
            {
                "name": "Reset Workspace",
                "action": self.reset_workspace,
            },
            {
                "name": f"Save Workspace{save_status}",
                "action": self.save_workspace,
            },
            {
                "name": "Save Workspace As...",
                "action": self.save_workspace_as,
            },
            {
                "name": f"Auto-Save: {'On' if self.state.auto_save_enabled else 'Off'}",
                "action": self.toggle_auto_save,
            },
        ]

    def manage_generator_blacklist(self):
        blacklist_menu = [
            {
                "name": "View current patterns",
                "action": self._view_blacklist_patterns,
            },
            {
                "name": "Add new pattern",
                "action": self._add_blacklist_pattern,
            },
            {
                "name": "Remove pattern",
                "action": self._remove_blacklist_pattern,
            },
        ]
        self.navigate_menu(blacklist_menu)

    def _view_blacklist_patterns(self):
        patterns = self.state.workspace.get_generator_blacklist_patterns()
        if not patterns:
            self.run_selector(["No blacklist patterns configured."], prompt="Generator Blacklist (Read-Only)")
            return
        display_patterns = [f"{i+1}. {p}" for i, p in enumerate(patterns)]
        self.run_selector(display_patterns, prompt="Generator Blacklist (Read-Only)")

    def _add_blacklist_pattern(self):
        prompt_text = "Enter new regex pattern (e.g., .*/__pycache__.*)"
        new_pattern_result = self.run_selector([], prompt=prompt_text)
        
        if not new_pattern_result or not new_pattern_result[0]:
            logging.debug("No new pattern entered.")
            return
        
        new_pattern = new_pattern_result[0].strip()
        if not new_pattern:
            self.run_selector(["Pattern cannot be empty."], prompt="Error")
            return

        try:
            re.compile(new_pattern)
        except re.error as e:
            self.run_selector([f"Invalid Regex: {e}"], prompt="Error")
            logging.error(f"[ERROR] Invalid regex pattern entered: '{new_pattern}' - {e}")
            return

        self.state.workspace.add_generator_blacklist_pattern(new_pattern)
        # Manually set dirty flag for now.
        self.state.is_dirty = True
        self.run_selector([f"Pattern '{new_pattern}' added. Status updated."], prompt="Success")


    def _remove_blacklist_pattern(self):
        patterns = self.state.workspace.get_generator_blacklist_patterns()
        if not patterns:
            self.run_selector(["No blacklist patterns to remove."], prompt="Generator Blacklist")
            return
        
        display_patterns = [f"{i+1}. {p}" for i, p in enumerate(patterns)]
        selection_list = self.run_selector(display_patterns, prompt="Select pattern(s) to remove", multi_select=True)
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
            self.run_selector([f"Removed pattern(s). Status updated."], prompt="Success")
        else:
            self.run_selector(["No patterns removed."], prompt="Info")

    def reset_workspace(self):
        confirm_options = ["Yes, reset it", "No, keep it"]
        confirmation = self.run_selector(confirm_options, prompt="Are you sure you want to reset workspace? This will clear all user-added paths and custom ignored paths.")
        if confirmation and confirmation[0] == "Yes, reset it":
            self.state.workspace.reset()
            # Manually set dirty flag for now.
            self.state.is_dirty = True
            self.run_selector(["Workspace reset to generated defaults. Status updated."], prompt="Success")
            logging.info("[INFO] Workspace reset performed.")
        else:
            self.run_selector(["Workspace reset cancelled."], prompt="Cancelled")
            logging.info("[INFO] Workspace reset cancelled by user.")

    def save_workspace(self):
        """Conditionally saves workspace or indicates status."""
        current_path = self.state.workspace.get_current_json_file_path()

        if self.state.auto_save_enabled:
            self.run_selector([f"Auto-Save is ON. Workspace is automatically saved to {current_path}."], prompt="Auto-Save Status")
        elif self.state.is_dirty:
            confirm_options = [f"Yes, save to {current_path}", "No, cancel"]
            confirmation = self.run_selector(confirm_options, prompt="Confirm Save")
            if confirmation and confirmation[0].startswith("Yes"):
                self.state.workspace.save()
                self.state.is_dirty = False # Clear dirty flag after explicit save
                self.run_selector([f"Workspace saved to {current_path}"], prompt="Success")
            else:
                self.run_selector(["Save cancelled."], prompt="Cancelled")
        else: # No unsaved changes and auto-save is off
            self.run_selector([f"Workspace is currently saved to {current_path} (No unsaved changes)."], prompt="Save Status")

    def save_workspace_as(self):
        """Prompts user for a new path and saves the workspace there."""
        current_path = self.state.workspace.get_current_json_file_path()
        prompt_text = f"Enter new workspace file path (Current: {current_path})"
        
        new_path_result = self.run_selector([], prompt=prompt_text)
        
        if not new_path_result or not new_path_result[0]:
            self.run_selector(["No path entered. Save cancelled."], prompt="Cancelled")
            return
        
        new_path_str = new_path_result[0].strip()
        if not new_path_str:
            self.run_selector(["Empty path entered. Save cancelled."], prompt="Cancelled")
            return

        new_path = Path(new_path_str).resolve()

        self.state.workspace.save(new_path)
        self.state.is_dirty = False # Clear dirty flag after explicit save as
        self.run_selector([f"Workspace saved to new path: {new_path}"], prompt="Success")
        logging.info(f"Workspace file path changed to: {new_path}")

    def toggle_auto_save(self):
        self.state.auto_save_enabled = not self.state.auto_save_enabled
        status = "On" if self.state.auto_save_enabled else "Off"
        # self.run_selector([f"Auto-Save turned {status}."], prompt="Auto-Save Status")
        logging.info(f"Auto-Save toggled to: {status}")
        # Note: We are not auto-saving here yet. That will be the next step.

    def remove_files(self):
        entries = self.state.workspace.list()
        selection = self.run_selector([str(p) for p in entries], prompt="Select Files to Remove", multi_select=True)
        if selection:
            self.state.workspace.remove([entries[[str(e) for e in entries].index(s)] for s in selection])
        self.update_file_watcher()

    def add_files(self):
        root_dir = self.get_root_dir()
        entries = list_files(root_dir)
        selection = self.run_selector([str(e) for e in entries], prompt="Select Files to Add", multi_select=True)
        if selection:
            self.state.workspace.add([entries[[str(e) for e in entries].index(s)] for s in selection], root_dir=root_dir)
        self.update_file_watcher()

    def get_root_dir(self) -> Path:
        root = self.state.root_dir or Path(".")
        if isinstance(root, str):
            root = Path(root)
        self.state.root_dir = root.resolve()
        return self.state.root_dir

    def traverse_directory(self):
        while True:
            dirs = list_directories(self.get_root_dir())
            selection = self.run_selector([str(d) for d in dirs], prompt="Select Directory")
            if not selection:
                return
            self.state.root_dir = dirs[[str(d) for d in dirs].index(selection[0])]

    # def add_files(self):
    #     root_dir = self.get_root_dir()
    #     entries = list_files(root_dir)
    #     selection = self.run_selector([str(e) for e in entries], prompt="Select Files to Add", multi_select=True)
    #     if selection:
    #         self.state.workspace.add([entries[[str(e) for e in entries].index(s)] for s in selection], root_dir=root_dir)
    #     self.update_file_watcher()

    # def remove_files(self):
    #     entries = self.state.workspace.list()
    #     selection = self.run_selector([str(p) for p in entries], prompt="Select Files to Remove", multi_select=True)
    #     if selection:
    #         self.state.workspace.remove([entries[[str(e) for e in entries].index(s)] for s in selection])
    #     self.update_file_watcher()
