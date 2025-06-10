# plugins/search_options.py
from core.plugin_base import WorkspacePlugin

class SearchOptions(WorkspacePlugin):
    priority = 40

    def __init__(self, menu, state):
        super().__init__(menu, state)
        self.state.update({
            "use_gitignore": True,
            "include_dotfiles": False,
            "expansion_depth": None,
            "expansion_recursion": True,
            "directory_expansion": True,
            "regex_mode": False,
            "regex_pattern": "",
            "show_files": True,
            "search_dirs_only": False,
            "search_files_only": False,
            "show_dirs": True,
        })
    
    def _main_menu_entry(self):
        return {
            "name": "Search Options",
            "action": self._build_options,
        }
    
    def _build_options(self):
        return [
            f"Use .gitignore: {'ON' if self.state.use_gitignore else 'OFF'}",
            f"Include dotfiles: {'ON' if self.state.include_dotfiles else 'OFF'}",
            f"Directory expansion: {'ON' if self.state.directory_expansion else 'OFF'}",
            f"Expansion recursion: {'ON' if self.state.expansion_recursion else 'OFF'}",
            f"Expansion depth: {self.state.expansion_depth if self.state.expansion_depth is not None else 'Unlimited'}",
            f"Regex mode: {'ON' if self.state.regex_mode else 'OFF'}",
            f"Regex pattern: {self.state.regex_pattern or '<empty>'}",
            "---",
            "Reset to defaults",
            "Exit"
        ]
    
    def run_menu(self):
        options = self._build_options()
        while True:
            choice = self.menu.run_selector(options, "Search Options (toggle or edit)", multi_select=False)
            if not choice:
                break
            choice = choice[0]

            if choice == "Exit":
                break
            elif choice == "Reset to defaults":
                self.reset_defaults()
            elif choice.startswith("Regex pattern"):
                new_pattern = self.menu.run_selector([], "Enter regex pattern", multi_select=False)
                if new_pattern is not None:
                    self.state.regex_pattern = new_pattern[0] if new_pattern else ""
            elif choice.startswith("Expansion depth"):
                new_depth = self.menu.run_selector([], "Enter max recursion depth (empty for unlimited)", multi_select=False)
                if new_depth is not None:
                    val = new_depth[0].strip()
                    if val == "" or val.lower() in ("none", "unlimited"):
                        self.state.expansion_depth = None
                    else:
                        try:
                            depth_int = int(val)
                            self.state.expansion_depth = max(0, depth_int)
                        except ValueError:
                            pass
            else:
                self.toggle_option(choice)

            options = self._build_options()

    def toggle_option(self, option_label):
        if option_label.startswith("Use .gitignore"):
            self.state.use_gitignore = not self.state.use_gitignore
        elif option_label.startswith("Include dotfiles"):
            self.state.include_dotfiles = not self.state.include_dotfiles
        elif option_label.startswith("Directory expansion"):
            self.state.directory_expansion = not self.state.directory_expansion
        elif option_label.startswith("Expansion recursion"):
            self.state.expansion_recursion = not self.state.expansion_recursion
        elif option_label.startswith("Regex mode"):
            self.state.regex_mode = not self.state.regex_mode

    def reset_defaults(self):
        self.state.reset_defaults()
