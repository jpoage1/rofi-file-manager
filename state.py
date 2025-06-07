# state.py
from pathlib import Path
from workspace import Workspace
from clipboard import Clipboard
class State:
    def __init__(self):
        self.current_mode = "Edit"
        self.use_gitignore = True
        self.include_dotfiles = False
        self.directory_expansion = True
        self.expansion_recursion = True
        self.regex_mode = False
        self.regex_pattern = ""
        # self.search_dirs_only = False
        # self.search_files_only = True
        self.show_files = True
        self.show_dirs = True
        self.root_dir = None
        self.clipboard_queue = []
        self.state_stack = []
        self.input_set = []
        self.workspace_files = set()
        self.clipboard = Clipboard()
        self.workspace = None

    def init_workspace(self):
        if self.input_set:
            paths = [Path(p) for p in self.input_set]
        elif self.root_dir:
            paths = [Path(self.root_dir)]
        else:
            paths = [Path.cwd()]
        self.workspace = Workspace(self.input_set or [self.root_dir])


    def push_state(self):
        snapshot = {
            "current_mode": self.current_mode,
            "use_gitignore": self.use_gitignore,
            "include_dotfiles": self.include_dotfiles,
            "search_dirs_only": self.search_dirs_only,
            "search_files_only": self.search_files_only,
            "regex_mode": self.regex_mode,
            "regex_pattern": self.regex_pattern,
            "root_dir": self.root_dir,
            "clipboard_queue": self.clipboard.snapshot(),
        }
        self.state_stack.append(snapshot)

    def pop_state(self):
        if self.state_stack:
            snapshot = self.state_stack.pop()
            self.current_mode = snapshot["current_mode"]
            self.use_gitignore = snapshot["use_gitignore"]
            self.include_dotfiles = snapshot["include_dotfiles"]
            self.search_dirs_only = snapshot["search_dirs_only"]
            self.search_files_only = snapshot["search_files_only"]
            self.regex_mode = snapshot["regex_mode"]
            self.regex_pattern = snapshot["regex_pattern"]
            self.root_dir = snapshot["root_dir"]
            self.clipboard.restore(snapshot["clipboard_queue"])
