from pathlib import Path
from filesystem.filesystem import list_files, list_directories
from core.core import edit_files
from state.search_options import SearchOptions
from state.workspace_utils import get_filtered_workspace_paths
from filesystem.tree_utils import build_tree, flatten_tree
from filters.main import get_entries

import re

class MenuManager:
    def __init__(self, state):
        self.state = state
        self.search_options = SearchOptions(state)
        self.menu_structure_callable = self._get_main_menu_structure

    # --- NEW: Method to dynamically generate the main menu structure ---
    def _get_main_menu_structure(self):
        """Dynamically builds the main menu structure, especially for save status."""

        print(f"Auto-Save: {self.state.auto_save_enabled}")
        
        save_status_text = ""
        if self.state.auto_save_enabled:
            save_status_text = " (Auto-Save ON)"
        elif self.state.is_dirty:
            save_status_text = " (Unsaved Changes)"
        else:
            save_status_text = " (Saved)"
            
        save_option_label = f"Save Workspace{save_status_text}"
        # fixme This label isnt beging toggled?
        auto_save_toggle_label = f"Auto-Save: {'On' if self.state.auto_save_enabled else 'Off'}"

        return {
            'Workspace Tree': self.browse_workspace,
            'Search Workspace': self.search_workspace,
            'Filters': self.search_options.run_menu,
            'Workspace Management': self._get_workspace_management_menu, 
            'Clipboard Management': {
                'Commit clipboard queue to the clipboard': lambda: None,
                'Add to workspace paths to clipboard queue': self.add_workspace_to_clipboard,
                'Add cwd paths to clipboard queue': self.add_cwd_to_clipboard,
                'Remove from clipboard queue': self.remove_from_clipboard,
            },
        }
    # --- END NEW ---
    def main_loop(self):
        self.navigate_menu(self.menu_structure_callable)
        
    def _get_workspace_management_menu(self):
        """Dynamically builds the Workspace Management sub-menu, including dynamic labels."""
        
        # This print will now run every time the WORKSPACE MANAGEMENT sub-menu is generated.
        print(f"Generating Workspace Management Menu - Auto-Save State: {self.state.auto_save_enabled}")

        save_status_text = ""
        if self.state.auto_save_enabled:
            save_status_text = " (Auto-Save ON)"
        elif self.state.is_dirty:
            save_status_text = " (Unsaved Changes)"
        else:
            save_status_text = " (Saved)"
            
        save_option_label = f"Save Workspace{save_status_text}"
        auto_save_toggle_label = f"Auto-Save: {'On' if self.state.auto_save_enabled else 'Off'}"

        return {
            'Traverse to a new directory': self.traverse_directory,
            'Add files': self.add_files,
            'Remove files': self.remove_files,
            'Generator Blacklist': self.manage_generator_blacklist,
            'Reset Workspace': self.reset_workspace,
            save_option_label: self.save_workspace,
            'Save Workspace As...': self.save_workspace_as,
            auto_save_toggle_label: self.toggle_auto_save,
        }

    def navigate_menu(self, menu_source):
        while True:
            # # Determine the actual menu dictionary to display
            # print(f"menu_source {type(menu_source)} {menu_source}")
            current_menu_dict = menu_source() if callable(menu_source) else menu_source
            if not current_menu_dict:
                return
            
            # print(f"Callable (in navigate_menu loop): {callable(menu_source)}") # This will now be True for dynamic sub-menus

            # print(f"current_menu_dict {type(current_menu_dict)}")
            
            choice = self.state.run_selector(list(current_menu_dict.keys()), prompt="Select an option")
            if not choice:
                return # User cancelled, return to parent menu or exit

            selected_option_key = choice[0]
            action = current_menu_dict[selected_option_key]

            # Case 1: The action is a callable method that performs a command (e.g., toggle_auto_save, save_workspace)
            if callable(action) and not isinstance(action, type(self._get_main_menu_structure)): 
                # The 'type(self._get_main_menu_structure)' is a way to check if the callable is one of our menu-generating methods.
                # This ensures we don't accidentally execute a menu-generating callable as a direct action.
                action() # Execute the command
                # Loop continues, and current_menu_dict will be re-generated if menu_source is callable,
                # thus refreshing the display.
            
            # Case 2: The action is a sub-menu (either a static dictionary or a callable that generates a dictionary)
            elif isinstance(action, dict) or callable(action): 
                # Navigate into this sub-menu. `action` here *is* the `menu_source` for the next level.
                self.navigate_menu(action) 
                # After the sub-menu returns (meaning its Rofi was cancelled or an action completed within it),
                # the current menu (parent) needs to be regenerated. The loop continuing handles this.
            
            # If an action returns (e.g., a function call finishes or a sub-menu is exited)
            # The loop will naturally re-run, re-generating `current_menu_dict`
            # using the potentially updated `menu_source` (if it's callable)

    def search_workspace(self):
        entries = get_entries(self.state)
        entries_str = [str(e) for e in entries]
        tree = build_tree(entries_str)
        choices = flatten_tree(tree)

        while True:
            selection = self.state.run_selector(choices, prompt="Workspace Files")
            if not selection:
                return
            edit_files([Path(s) for s in selection])

    def get_root_dir(self) -> Path:
        root = self.state.root_dir
        if not root:
            root = Path(".")
        elif isinstance(root, str):
            root = Path(root)
        self.state.root_dir = root.resolve()
        return self.state.root_dir

    def traverse_directory(self):
        while True:
            root_dir = self.get_root_dir()
            dirs = list_directories(root_dir)
            selection = self.state.run_selector([str(d) for d in dirs], prompt="Select Directory")
            if not selection:
                return
            self.state.root_dir = dirs[[str(d) for d in dirs].index(selection[0])]

    def add_files(self):
        while True:
            root_dir = self.get_root_dir()
            entries = list_files(root_dir)
            selection = self.state.run_selector([str(e) for e in entries], prompt="Select Files to Add", multi_select=True)
            if not selection:
                return
            selected = [entries[[str(e) for e in entries].index(s)] for s in selection]
            self.state.workspace.add(selected, root_dir=root_dir)

    def remove_files(self):
        while True:
            entries = self.state.workspace.list()
            selection = self.state.run_selector([str(p) for p in entries], prompt="Select Files to Remove", multi_select=True)
            if not selection:
                return
            selected = [entries[[str(e) for e in entries].index(s)] for s in selection]
            self.state.workspace.remove(selected)

    def add_workspace_to_clipboard(self):
        while True:
            entries = self.state.workspace.list()
            selection = self.state.run_selector([str(p) for p in entries], prompt="Select Workspace Paths", multi_select=True)
            if not selection:
                return
            selected = [entries[[str(e) for e in entries].index(s)] for s in selection]
            self.state.clipboard.add_files(selected)

    def add_cwd_to_clipboard(self):
        while True:
            root_dir = self.get_root_dir()
            entries = list_files(root_dir)
            selection = self.state.run_selector([str(e) for e in entries], prompt="Select CWD Files", multi_select=True)
            if not selection:
                return
            selected = [entries[[str(e) for e in entries].index(s)] for s in selection]
            self.state.clipboard.add_files(selected)

    def remove_from_clipboard(self):
        while True:
            entries = self.state.clipboard.get_files()
            selection = self.state.run_selector([str(p) for p in entries], prompt="Select Clipboard Paths to Remove", multi_select=True)
            if not selection:
                return
            selected = [entries[[str(e) for e in entries].index(s)] for s in selection]
            self.state.clipboard.remove_files(selected)

    def browse_workspace(self):
        while True:
            entries = sorted(str(p) for p in self.state.workspace.list())
            choice = self.state.run_selector(entries, prompt="Select Root")
            if not choice:
                return
            selected_path = Path(choice[0])
            if selected_path.is_file():
                edit_files([selected_path])
            else:
                self._browse_tree(choice[0])

    def _browse_tree(self, current_dir):
        cur_path = Path(current_dir).resolve()
        stack = []

        while True:
            try:
                entries = sorted(cur_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            except Exception:
                entries = []

            display = [f"{e.name}/" if e.is_dir() else e.name for e in entries]
            choice = self.state.run_selector(display, prompt=str(cur_path))
            if not choice:
                if stack:
                    cur_path = stack.pop()
                    continue
                return

            name = choice[0].rstrip("/")
            next_path = cur_path / name
            print(next_path)
            if next_path.is_dir():
                stack.append(cur_path)
                cur_path = next_path
            else:
                edit_files([next_path])

     # --- Blacklist Management (modified to set dirty flag manually for now) ---
    def manage_generator_blacklist(self):
        blacklist_menu = {
            'View current patterns': self._view_blacklist_patterns,
            'Add new pattern': self._add_blacklist_pattern,
            'Remove pattern': self._remove_blacklist_pattern,
        }
        self.navigate_menu(blacklist_menu)

    def _view_blacklist_patterns(self):
        patterns = self.state.workspace.get_generator_blacklist_patterns()
        if not patterns:
            self.state.run_selector(["No blacklist patterns configured."], prompt="Generator Blacklist (Read-Only)")
            return
        display_patterns = [f"{i+1}. {p}" for i, p in enumerate(patterns)]
        self.state.run_selector(display_patterns, prompt="Generator Blacklist (Read-Only)")

    def _add_blacklist_pattern(self):
        prompt_text = "Enter new regex pattern (e.g., .*/__pycache__.*)"
        new_pattern_result = self.state.run_selector([], prompt=prompt_text)
        
        if not new_pattern_result or not new_pattern_result[0]:
            print("[DEBUG] No new pattern entered.")
            return
        
        new_pattern = new_pattern_result[0].strip()
        if not new_pattern:
            self.state.run_selector(["Pattern cannot be empty."], prompt="Error")
            return

        try:
            re.compile(new_pattern)
        except re.error as e:
            self.state.run_selector([f"Invalid Regex: {e}"], prompt="Error")
            print(f"[ERROR] Invalid regex pattern entered: '{new_pattern}' - {e}")
            return

        self.state.workspace.add_generator_blacklist_pattern(new_pattern)
        # Manually set dirty flag for now.
        self.state.is_dirty = True
        self.state.run_selector([f"Pattern '{new_pattern}' added. Status updated."], prompt="Success")


    def _remove_blacklist_pattern(self):
        patterns = self.state.workspace.get_generator_blacklist_patterns()
        if not patterns:
            self.state.run_selector(["No blacklist patterns to remove."], prompt="Generator Blacklist")
            return
        
        display_patterns = [f"{i+1}. {p}" for i, p in enumerate(patterns)]
        selection_list = self.state.run_selector(display_patterns, prompt="Select pattern(s) to remove", multi_select=True)
        if not selection_list:
            print("[DEBUG] No pattern selected for removal.")
            return

        removed_any = False
        for sel_str in selection_list:
            try:
                parts = sel_str.split(' ', 1)
                if len(parts) > 1:
                    pattern_to_remove = parts[1]
                    self.state.workspace.remove_generator_blacklist_pattern(pattern_to_remove)
                    removed_any = True
                    print(f"[INFO] Removed generator blacklist pattern: '{pattern_to_remove}'")
                else:
                    print(f"[WARNING] Could not parse selection string '{sel_str}', skipping.")
            except Exception as e:
                print(f"[ERROR] Error removing pattern '{sel_str}': {e}")
        
        if removed_any:
            # Manually set dirty flag for now.
            self.state.is_dirty = True
            self.state.run_selector([f"Removed pattern(s). Status updated."], prompt="Success")
        else:
            self.state.run_selector(["No patterns removed."], prompt="Info")

    def reset_workspace(self):
        confirm_options = ["Yes, reset it", "No, keep it"]
        confirmation = self.state.run_selector(confirm_options, prompt="Are you sure you want to reset workspace? This will clear all user-added paths and custom ignored paths.")
        if confirmation and confirmation[0] == "Yes, reset it":
            self.state.workspace.reset()
            # Manually set dirty flag for now.
            self.state.is_dirty = True
            self.state.run_selector(["Workspace reset to generated defaults. Status updated."], prompt="Success")
            print("[INFO] Workspace reset performed.")
        else:
            self.state.run_selector(["Workspace reset cancelled."], prompt="Cancelled")
            print("[INFO] Workspace reset cancelled by user.")

    # --- UPDATED Save Workspace Method ---
    def save_workspace(self):
        """Conditionally saves workspace or indicates status."""
        current_path = self.state.workspace.get_current_json_file_path()

        if self.state.auto_save_enabled:
            self.state.run_selector([f"Auto-Save is ON. Workspace is automatically saved to {current_path}."], prompt="Auto-Save Status")
        elif self.state.is_dirty:
            confirm_options = [f"Yes, save to {current_path}", "No, cancel"]
            confirmation = self.state.run_selector(confirm_options, prompt="Confirm Save")
            if confirmation and confirmation[0].startswith("Yes"):
                self.state.workspace.save()
                self.state.is_dirty = False # Clear dirty flag after explicit save
                self.state.run_selector([f"Workspace saved to {current_path}"], prompt="Success")
            else:
                self.state.run_selector(["Save cancelled."], prompt="Cancelled")
        else: # No unsaved changes and auto-save is off
            self.state.run_selector([f"Workspace is currently saved to {current_path} (No unsaved changes)."], prompt="Save Status")

    def save_workspace_as(self):
        """Prompts user for a new path and saves the workspace there."""
        current_path = self.state.workspace.get_current_json_file_path()
        prompt_text = f"Enter new workspace file path (Current: {current_path})"
        
        new_path_result = self.state.run_selector([], prompt=prompt_text)
        
        if not new_path_result or not new_path_result[0]:
            self.state.run_selector(["No path entered. Save cancelled."], prompt="Cancelled")
            return
        
        new_path_str = new_path_result[0].strip()
        if not new_path_str:
            self.state.run_selector(["Empty path entered. Save cancelled."], prompt="Cancelled")
            return

        new_path = Path(new_path_str).resolve()

        self.state.workspace.save(new_path)
        self.state.is_dirty = False # Clear dirty flag after explicit save as
        self.state.run_selector([f"Workspace saved to new path: {new_path}"], prompt="Success")
        print(f"[INFO] Workspace file path changed to: {new_path}")

    # --- NEW Toggle Auto-Save Method ---
    def toggle_auto_save(self):
        self.state.auto_save_enabled = not self.state.auto_save_enabled
        status = "On" if self.state.auto_save_enabled else "Off"
        # self.state.run_selector([f"Auto-Save turned {status}."], prompt="Auto-Save Status")
        print(f"[INFO] Auto-Save toggled to: {status}")
        # Note: We are not auto-saving here yet. That will be the next step.
