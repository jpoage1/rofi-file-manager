# menu_manager.py

from rofi_interface import run_rofi
from filesystem import list_files, list_directories
from core import edit_files
from pathlib import Path

class MenuManager:
    def __init__(self, state):
        self.state = state
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
            entries = [str(p) for p in self.state.workspace.list()]
            selection = run_rofi(entries, prompt="Workspace Files")
            if not selection:
                break
            edit_files(selection)

    def traverse_directory(self):
        # Implement the logic to traverse to a new directory
        dirs = list_directories(self.state.root_dir)
        selection = run_rofi(dirs, prompt="Select Directory")
        if selection:
            self.state.root_dir = str(Path(self.state.root_dir) / selection[0])

    def add_files(self):
        # Implement the logic to add files to the workspace
        files = list_files(self.state.root_dir)
        selection = run_rofi(files, prompt="Select Files to Add", multi_select=True)
        if selection:
            self.state.workspace.add(self.state.root_dir, selection)

    def remove_files(self):
        # Implement the logic to remove files from the workspace
        entries = [str(p) for p in self.state.workspace.list()]
        selection = run_rofi(entries, prompt="Select Files to Remove", multi_select=True)
        if selection:
            self.state.workspace.remove(selection)

    def add_workspace_to_clipboard(self):
        # Implement the logic to add workspace paths to the clipboard queue
        entries = [str(p) for p in self.state.workspace.list()]
        selection = run_rofi(entries, prompt="Select Workspace Paths", multi_select=True)
        if selection:
            self.state.clipboard.add_files(selection)

    def add_cwd_to_clipboard(self):
        # Implement the logic to add cwd paths to the clipboard queue
        files = list_files(self.state.root_dir)
        selection = run_rofi(files, prompt="Select CWD Files", multi_select=True)
        if selection:
            self.state.clipboard.add_files([str(Path(self.state.root_dir) / f) for f in selection])

    def remove_from_clipboard(self):
        # Implement the logic to remove paths from the clipboard queue
        entries = [str(p) for p in self.state.clipboard.get_files()]
        selection = run_rofi(entries, prompt="Select Clipboard Paths to Remove", multi_select=True)
        if selection:
            self.state.clipboard.remove_files(selection)
