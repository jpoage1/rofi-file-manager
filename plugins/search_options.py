# plugins/search_options.py
from core.plugin_base import WorkspacePlugin, SubMenu, MenuEntry, SelectorHelper, ExpansionDepthHelper, RegexPromptHelper

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

    def _build_menu(self) -> SubMenu:
        options = [
            MenuEntry(f"Use .gitignore: {'ON' if self.state.use_gitignore else 'OFF'}"),
            MenuEntry(f"Include dotfiles: {'ON' if self.state.include_dotfiles else 'OFF'}"),
            MenuEntry(f"Directory expansion: {'ON' if self.state.directory_expansion else 'OFF'}"),
            MenuEntry(f"Expansion recursion: {'ON' if self.state.expansion_recursion else 'OFF'}"),
            MenuEntry(f"Expansion depth: {self.state.expansion_depth if self.state.expansion_depth is not None else 'Unlimited'}"),
            MenuEntry(f"Regex mode: {'ON' if self.state.regex_mode else 'OFF'}"),
            MenuEntry(f"Regex pattern: {self.state.regex_pattern or '<empty>'}"),
            MenuEntry("---"),
            MenuEntry("Reset to defaults", action=self.reset_defaults)
        ]
        return SubMenu("Search Options", options)
    
    def run_menu(self):
        selector = SelectorHelper(self.menu.run_selector)
        regex_prompt = RegexPromptHelper(self.menu.run_selector)
        depth_prompt = ExpansionDepthHelper(self.menu.run_selector)

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
                self.state.regex_pattern = regex_prompt.prompt()
            elif choice.startswith("Expansion depth"):
                depth = depth_prompt.prompt()
                self.state.expansion_depth = depth
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
