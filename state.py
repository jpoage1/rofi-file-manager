# state.py
from workspace import Workspace
from clipboard import Clipboard
class State:
    def __init__(self):
        self.current_mode = "Edit"
        self.use_gitignore = True
        self.include_dotfiles = False
        self.search_dirs_only = False
        self.search_files_only = True
        self.regex_mode = False
        self.regex_pattern = ""
        self.root_dir = "."
        self.clipboard_queue = []
        self.state_stack = []
        self.input_set = []
        self.mode = "NORMAL"  # or "MULTI"
        self.workspace_label = "Workspace"
        self.workspace_files = set()
        self.clipboard = Clipboard()
        self.workspace = Workspace()


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
