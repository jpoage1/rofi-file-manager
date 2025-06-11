# Path: old/menu_manager/manager.py
# Last Modified: 2025-06-11

# menu_manager/manager.py
from pathlib import Path
from menu_manager.core import edit_files
from state.search_options import SearchOptions
from filters.main import get_entries
# from filesystem.tree_utils import build_tree, flatten_tree

from .menu_workspace import WorkspaceActions
from .menu_clipboard import ClipboardActions
import re
import logging
from menu_manager.interface import selector, run_via_socket

# logging.basicConfig(level=logging.DEBUG)

class MenuManager(WorkspaceActions, ClipboardActions):
    def __init__(self, state, interface=None, frontend=None, host=None, port=None):
        self.state = state
        self.interface = interface or "cli"
        self.frontend = frontend or "fzf"
        self.search_options = SearchOptions(self, state)
        self.menu_structure_callable = self._get_main_menu_structure
        self.socket_conn = None
        self.host = host or '127.0.0.1'
        self.port = int(port or 65432)

    def _get_main_menu_structure(self):
        return {
            'Workspace Tree': self.browse_workspace,
            'Search Workspace': self.search_workspace,
            'Filters': self.search_options.run_menu,
            'Workspace Management': self._get_workspace_management_menu,
            'Clipboard Management': self._get_clipboard_menu()
        }

    def _get_workspace_management_menu(self):
        save_status = (
            " (Auto-Save ON)" if self.state.auto_save_enabled else
            " (Unsaved Changes)" if self.state.is_dirty else
            " (Saved)"
        )
        return {
            'Traverse to a new directory': self.traverse_directory,
            'Add files': self.add_files,
            'Remove files': self.remove_files,
            'Generator Blacklist': self.manage_generator_blacklist,
            'Reset Workspace': self.reset_workspace,
            f"Save Workspace{save_status}": self.save_workspace,
            'Save Workspace As...': self.save_workspace_as,
            f"Auto-Save: {'On' if self.state.auto_save_enabled else 'Off'}": self.toggle_auto_save,
        }

    def _get_clipboard_menu(self):
        return {
            'Commit clipboard queue to the clipboard': lambda: None,
            'Add to workspace paths to clipboard queue': self.add_workspace_to_clipboard,
            'Add cwd paths to clipboard queue': self.add_cwd_to_clipboard,
            'Remove from clipboard queue': self.remove_from_clipboard,
        }

    def run_selector(self, entries, prompt, multi_select=False, text_input=True):
        try:
            if self.interface == "socket-server" or self.interface == "sockets-server":
                selected_option = run_via_socket(self.socket_conn, entries, prompt, multi_select, text_input)
            else:
                selected_option = selector(self.frontend, entries, prompt, multi_select, text_input)
            return selected_option
        except EOFError:
            logging.info("[MenuManager] EOF received, exiting CLI.")
            return ["Quit"]
        
    def navigate_menu(self, menu_source):
        while True:
            current_menu_dict = menu_source() if callable(menu_source) else menu_source
            if not current_menu_dict: return

            choice = self.run_selector(list(current_menu_dict.keys()), prompt="Select an option")
            
            if not choice:
                # logging.info("[MenuManager] User cancelled selector or received empty choice. Exiting current menu level.")
                return '' # Propagate cancellation

            selected_option_key = choice[0]
            action = current_menu_dict.get(selected_option_key)

            # Handle explicit signals first
            if action == 'EXIT_SIGNAL':
                logging.info("[MenuManager] 'Exit Application' selected. Signaling application exit.")
                return 'EXIT_SIGNAL'
            elif action == 'BACK_SIGNAL':
                logging.info("[MenuManager] 'Back to Main Menu' selected. Signaling return to parent.")
                return 'BACK_SIGNAL'

            if callable(action) and not isinstance(action, type(self._get_main_menu_structure)) \
                                and not (hasattr(action, '__name__') and action.__name__ in ['_get_main_menu_structure', '_get_workspace_management_menu', 'run_menu']):
                action() # Execute the command
            elif isinstance(action, dict) or callable(action):
                result = self.navigate_menu(action)
                if result in ['EXIT_SIGNAL', 'BACK_SIGNAL', 'CANCELLED']:
                    return result # Propagate signals from sub-menus
            elif action is None:
                logging.info(f"[MenuManager] Warning: No action found for selected key: '{selected_option_key}'")

  
    def search_workspace(self):
        entries = self.state.workspace.cache

        entries_str = [str(e) for e in entries]
        # These are redundant, but may become useful if future features require it
        # tree = build_tree(entries_str) # Create a directory tree
        # choices = flatten_tree(tree)
        choices = sorted(entries_str)

        while True:
            selection = self.run_selector(choices, prompt="Workspace Files")
            if not selection:
                return
            edit_files([Path(s) for s in selection])

    def browse_workspace(self):
        while True:
            entries = sorted(str(p) for p in self.state.workspace.list())
            choice = self.run_selector(entries, prompt="Select Root")
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
            choice = self.run_selector(display, prompt=str(cur_path))
            if not choice:
                if stack:
                    cur_path = stack.pop()
                    continue
                return

            name = choice[0].rstrip("/")
            next_path = cur_path / name
            logging.info(next_path)
            if next_path.is_dir():
                stack.append(cur_path)
                cur_path = next_path
            else:
                edit_files([next_path])

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

   
    def _get_workspace_management_menu(self):
        """Dynamically builds the Workspace Management sub-menu, including dynamic labels."""
        
        # This print will now run every time the WORKSPACE MANAGEMENT sub-menu is generated.
        logging.info(f"Generating Workspace Management Menu - Auto-Save State: {self.state.auto_save_enabled}")

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
    

    def _get_main_menu_structure(self):
        """Dynamically builds the main menu structure, especially for save status."""

        logging.info(f"Auto-Save: {self.state.auto_save_enabled}")
        
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
    