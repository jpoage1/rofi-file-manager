# search_options.py

class SearchOptions:
    def __init__(self, state):
        self.state = state

    def run_menu(self):
        options = [
            f"Use .gitignore: {'ON' if self.state.use_gitignore else 'OFF'}",
            f"Include dotfiles: {'ON' if self.state.include_dotfiles else 'OFF'}",
            f"Directory expansion: {'ON' if self.state.directory_expansion else 'OFF'}",
            f"Expansion recursion: {'ON' if self.state.expansion_recursion else 'OFF'}",
            f"Regex mode: {'ON' if self.state.regex_mode else 'OFF'}",
            f"Regex pattern: {self.state.regex_pattern or '<empty>'}",
            "---",
            "Reset to defaults",
            "Exit"
        ]
        while True:
            choice = run_rofi(options, "Search Options (toggle or edit pattern)", multi_select=False)
            if not choice:
                break
            choice = choice[0]
            if choice == "Exit":
                break
            elif choice == "Reset to defaults":
                self.reset_defaults()
            elif choice.startswith("Regex pattern"):
                new_pattern = run_rofi([], "Enter regex pattern", multi_select=False)
                if new_pattern is not None:
                    self.state.regex_pattern = new_pattern[0] if new_pattern else ""
                    options[5] = f"Regex pattern: {self.state.regex_pattern or '<empty>'}"
            else:
                self.toggle_option(choice)
                # Refresh option display
                options = [
                    f"Use .gitignore: {'ON' if self.state.use_gitignore else 'OFF'}",
                    f"Include dotfiles: {'ON' if self.state.include_dotfiles else 'OFF'}",
                    f"Directory expansion: {'ON' if self.state.directory_expansion else 'OFF'}",
                    f"Expansion recursion: {'ON' if self.state.expansion_recursion else 'OFF'}",
                    f"Regex mode: {'ON' if self.state.regex_mode else 'OFF'}",
                    f"Regex pattern: {self.state.regex_pattern or '<empty>'}",
                    "---",
                    "Reset to defaults",
                    "Exit"
                ]

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
        self.state.use_gitignore = True
        self.state.include_dotfiles = False
        self.state.directory_expansion = True
        self.state.expansion_recursion = True
        self.state.regex_mode = False
        self.state.regex_pattern = ""

