class AppState:
    def __init__(self):
        self.use_gitignore = 1
        self.include_dotfiles = 0
        self.search_dirs_only = 0
        self.search_files_only = 1

    def toggle_use_gitignore(self):
        self.use_gitignore = 1 - self.use_gitignore

    def toggle_include_dotfiles(self):
        self.include_dotfiles = 1 - self.include_dotfiles

    def toggle_search_dirs_only(self):
        self.search_dirs_only = 1 - self.search_dirs_only

    def toggle_search_files_only(self):
        self.search_files_only = 1 - self.search_files_only


def toggle_menu(state: AppState):
    while True:
        options = [
            f"Use .gitignore: {state.use_gitignore}",
            f"Include dotfiles: {state.include_dotfiles}",
            f"Search dirs only: {state.search_dirs_only}",
            f"Search files only: {state.search_files_only}",
            "Continue"
        ]

        choice = rofi_select(options, prompt="Toggle options")

        if choice == f"Use .gitignore: {1 - state.use_gitignore}":
            state.toggle_use_gitignore()
        elif choice == f"Include dotfiles: {1 - state.include_dotfiles}":
            state.toggle_include_dotfiles()
        elif choice == f"Search dirs only: {1 - state.search_dirs_only}":
            state.toggle_search_dirs_only()
        elif choice == f"Search files only: {1 - state.search_files_only}":
            state.toggle_search_files_only()
        elif choice == "Continue":
            break
