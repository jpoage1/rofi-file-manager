# menu_manager.py

from rofi_interface import run_rofi
from filesystem import list_files, list_directories
from core import edit_files
from pathlib import Path

from search_options import SearchOptions

class MenuManager:
    def __init__(self, state):
        self.state = state
        self.search_options = SearchOptions(state)
        self.menu_structure = {
            'Browse Workspace': self.browse_workspace,
            'Workspace Management': {
                'Traverse to a new directory': self.traverse_directory,
                'Add files': self.add_files,
                'Remove files': self.remove_files
            },
            'Clipboard Management': {
                'Add to workspace paths to clipboard queue': self.add_workspace_to_clipboard,
                'Add cwd paths to clipboard queue': self.add_cwd_to_clipboard,
                'Remove from clipboard queue': self.remove_from_clipboard
            }
        }

    def main_loop(self):
        self.navigate_menu(self.menu_structure)

    def navigate_menu(self, menu):
        while True:
            options = list(menu.keys())
            choice = run_rofi(options, prompt="Select an option")
            if not choice:
                break
            selected = choice[0]
            action = menu[selected]
            if callable(action):
                action()
            elif isinstance(action, dict):
                self.navigate_menu(action)

    def browse_workspace(self):
        while True:
            raw_entries = [str(p) for p in self.state.workspace.list()]
            entries = self.prepend_search_options_entry(raw_entries)
            selection = run_rofi(entries, prompt="Workspace Files")
            if not selection:
                break
            if self.handle_search_options_entry(selection[0]):
                continue
            # normal selection handling
            edit_files(selection)

    def get_root_dir(self):
        if not self.state.root_dir:
            self.state.root_dir = Path(".")
        return self.state.root_dir
    
    def traverse_directory(self):
        # Implement the logic to traverse to a new directory
        dirs = list_directories(self.state.root_dir)
        selection = run_rofi(dirs, prompt="Select Directory")
        if selection:
            self.state.root_dir = str(Path(self.get_root_dir()) / selection[0])

    def add_files(self):
        while True:
            root_dir = self.get_root_dir()
            raw_entries = list_files(root_dir)
            entries = self.prepend_search_options_entry(raw_entries)
            selection = run_rofi(entries, prompt="Select Files to Add", multi_select=True)
            if not selection:
                break
            if self.handle_search_options_entry(selection[0]):
                continue
            self.state.workspace.add(root_dir, selection)

    def remove_files(self):
        # Implement the logic to remove files from the workspace
        entries = [str(p) for p in self.state.workspace.list()]
        selection = run_rofi(entries, prompt="Select Files to Remove", multi_select=True)
        if selection:
            self.state.workspace.remove(selection)

    def add_workspace_to_clipboard(self):
        while True:
            raw_entries = [str(p) for p in self.state.workspace.list()]
            entries = self.prepend_search_options_entry(raw_entries)
            selection = run_rofi(entries, prompt="Select Workspace Paths", multi_select=True)
            if not selection:
                break
            if self.handle_search_options_entry(selection[0]):
                continue
            self.state.clipboard.add_files(selection)

    def add_cwd_to_clipboard(self):
        while True:
            root_dir = self.get_root_dir()
            raw_entries = list_files(root_dir)
            entries = self.prepend_search_options_entry(raw_entries)
            selection = run_rofi(entries, prompt="Select CWD Files", multi_select=True)
            if not selection:
                break
            if self.handle_search_options_entry(selection[0]):
                continue
            self.state.clipboard.add_files([str(Path(root_dir) / f) for f in selection])


    def remove_from_clipboard(self):
        # Implement the logic to remove paths from the clipboard queue
        entries = [str(p) for p in self.state.clipboard.get_files()]
        selection = run_rofi(entries, prompt="Select Clipboard Paths to Remove", multi_select=True)
        if selection:
            self.state.clipboard.remove_files(selection)

    def prepend_search_options_entry(self, entries):
        # Insert "Enter Search Options Menu" at the start
        return ["Enter Search Options Menu"] + entries

    def handle_search_options_entry(self, selection):
        if selection == "Enter Search Options Menu":
            self.search_options.run_menu()
            return True
        return False
