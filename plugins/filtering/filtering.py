# Path: plugins/filtering/filtering.py
# Last Modified: 2025-06-11

from core.plugin_base import WorkspacePlugin, SubMenu, BinaryToggleEntry, SelectorHelper, ExpansionDepthHelper, RegexPromptHelper, TextInputEntry, VoidEntry, MenuEntry

class FilterOptions(WorkspacePlugin):
    priority = 40

    name = "filtering"

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
            TextInputEntry(f"Regex pattern: {self.state.regex_pattern or '<empty>'}"),
            VoidEntry("---"),
            MenuEntry("Reset to defaults", action=self.reset_defaults)
        ]
        return SubMenu("Search Options", options)
    
    def reset_defaults(self):
        self.state.reset_defaults()
