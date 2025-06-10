# plugins/search_options.py
from core.plugin_base import WorkspacePlugin, SubMenu, BinaryToggleEntry, SelectorHelper, ExpansionDepthHelper, RegexPromptHelper, TextEntry, SeperatorEntry, MenuEntry

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
            BinaryToggleEntry("Use .gitignore", "use_gitignore", self.state),
            BinaryToggleEntry("Include dotfiles", "include_dotfiles", self.state),
            BinaryToggleEntry("Directory expansion", "directory_expansion", self.state),
            BinaryToggleEntry("Expansion recursion", "expansion_recursion", self.state),
            BinaryToggleEntry("Expansion depth", "expansion_depth", self.state),
            BinaryToggleEntry("Regex mode", "regex_mode", self.state),
            # TextEntry(f"Regex pattern: {self.state.regex_pattern or '<empty>'}"),
            # SeperatorEntry("---"),
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


    def reset_defaults(self):
        self.state.reset_defaults()
