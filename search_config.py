# search_config.py
class SearchConfig:
    def __init__(self):
        self.use_gitignore = True
        self.include_dotfiles = False
        self.directory_expansion = True
        self.expansion_recursion = True
        self.expansion_depth = None
        self.regex_mode = False
        self.regex_pattern = ""

    def reset_defaults(self):
        self.use_gitignore = True
        self.include_dotfiles = False
        self.directory_expansion = True
        self.expansion_recursion = True
        self.expansion_depth = None
        self.regex_mode = False
        self.regex_pattern = ""
