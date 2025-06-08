# search_options.py
from pathlib import Path

class SearchOptions:
    def __init__(self, state):
        self.config = state.search_config
        
    def run_menu(self):
        options = self._build_options()
        while True:
            choice = self.config.run_selector(options, "Search Options (toggle or edit)", multi_select=False)
            if not choice:
                break
            choice = choice[0]

            if choice == "Exit":
                break
            elif choice == "Reset to defaults":
                self.reset_defaults()
            elif choice.startswith("Regex pattern"):
                new_pattern = self.config.run_selector([], "Enter regex pattern", multi_select=False)
                if new_pattern is not None:
                    self.state.regex_pattern = new_pattern[0] if new_pattern else ""
            elif choice.startswith("Expansion depth"):
                new_depth = self.config.run_selector([], "Enter max recursion depth (empty for unlimited)", multi_select=False)
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


    def _build_options(self):
        return [
            f"Use .gitignore: {'ON' if self.config.use_gitignore else 'OFF'}",
            f"Include dotfiles: {'ON' if self.config.include_dotfiles else 'OFF'}",
            f"Directory expansion: {'ON' if self.config.directory_expansion else 'OFF'}",
            f"Expansion recursion: {'ON' if self.config.expansion_recursion else 'OFF'}",
            f"Expansion depth: {self.config.expansion_depth if self.config.expansion_depth is not None else 'Unlimited'}",
            f"Regex mode: {'ON' if self.config.regex_mode else 'OFF'}",
            f"Regex pattern: {self.config.regex_pattern or '<empty>'}",
            "---",
            "Reset to defaults",
            "Exit"
        ]

    def toggle_option(self, option_label):
        if option_label.startswith("Use .gitignore"):
            self.config.use_gitignore = not self.config.use_gitignore
        elif option_label.startswith("Include dotfiles"):
            self.config.include_dotfiles = not self.config.include_dotfiles
        elif option_label.startswith("Directory expansion"):
            self.config.directory_expansion = not self.config.directory_expansion
        elif option_label.startswith("Expansion recursion"):
            self.config.expansion_recursion = not self.config.expansion_recursion
        elif option_label.startswith("Regex mode"):
            self.config.regex_mode = not self.config.regex_mode

    def reset_defaults(self):
        self.config.reset_defaults()
