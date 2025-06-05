import subprocess
import os
from dataclasses import dataclass, field
import re
import copy

def main_menu(dirs):
    entries = ["[All Files]"] + dirs
    path = rofi_select(entries, prompt="Edit target:")
    if not path:
        return
    interpret_main_menu(path, dirs)

def rofi_select(entries, prompt="Edit target:", multi_select=False):
    args = ["rofi", "-dmenu", "-p", prompt]
    if multi_select:
        args.append("-multi-select")
    rofi_input = "\n".join(entries)
    proc = subprocess.run(args, input=rofi_input, text=True, capture_output=True)
    out = proc.stdout.strip()
    return out.splitlines() if multi_select else out

def edit_files(*files):
    editor = os.environ.get("EDITOR", "vi")
    cmd = [
        "xterm",
        "-fa", "DejaVu Sans Mono Book",
        "-fs", "12",
        "-e",
        editor,
        *files
    ]
    subprocess.run(cmd)
@dataclass
class SessionState:
    current_mode: str = ""

    def set_mode(self, mode: str):
        self.current_mode = mode

def mode_menu(state: SessionState):
    modes = ["Edit", "Execute", "Clipboard"]
    choice = rofi_select(modes, prompt="Select Mode")
    if choice:
        state.set_mode(choice)

def find_subdirs(base_dir='.'):
    base_dir = base_dir or '.'
    result = []
    for root, dirs, files in os.walk(base_dir):
        if root == base_dir:
            # Skip the base directory itself
            continue
        # Get path relative to base_dir
        rel_path = os.path.relpath(root, base_dir)
        result.append(rel_path)
    return result

def find_files(base_dir='.'):
    base_dir = base_dir or '.'
    result = []
    with os.scandir(base_dir) as it:
        for entry in it:
            if entry.is_file():
                result.append(entry.name)
    return result

def find_files_recursive(base_dir='.'):
    base_dir = base_dir or '.'
    result = []
    base_len = len(os.path.abspath(base_dir)) + 1
    for root, _, files in os.walk(base_dir):
        for f in files:
            full_path = os.path.join(root, f)
            relative_path = full_path[base_len:]
            result.append(relative_path)
    return result
def find_files_maxdepth_1(base_dir='.'):
    base_dir = base_dir or '.'
    result = []
    for entry in os.scandir(base_dir):
        if entry.is_file():
            result.append(entry.name)
    return result
def get_entries(entries, current_mode):
    base_dir = entries[0] if entries else '.'
    base_dir = base_dir or '.'

    if current_mode == "Traverse":
        # Directories only, recursive excluding base_dir itself
        result = find_subdirs(base_dir)
        return sorted(result)

    elif current_mode == "FilesOnly":
        # Files only, non-recursive
        result = find_files_maxdepth_1(base_dir)
        return sorted(result)

    elif current_mode == "SearchAll":
        # Files only, recursive with relative path
        result = find_files_recursive(base_dir)
        return sorted(result)

    elif current_mode == "Edit":
        # Files and directories, non-recursive, names only excluding base_dir itself
        with os.scandir(base_dir) as it:
            result = [entry.name for entry in it if entry.name != os.path.basename(base_dir)]
        return sorted(result)

    else:
        return entries


def interpret_main_menu(path, dirs):
    fzf = FzfDir(app_state, editor_cmd)
    if path == "[All Files]":
        fzf.fzf_dir(dirs)
    elif os.path.isfile(path):
        edit_files(path)
    elif os.path.isdir(path):
        fzf.fzf_dir([path])
    else:
        print(f"Not file or directory: {path}")
@dataclass
class QueryConfig:
    use_gitignore: bool = True
    include_dotfiles: bool = False
    search_dirs_only: bool = False
    search_files_only: bool = True
    extra_globs: list[str] = field(default_factory=list)

    def build_query_args(self) -> list[str]:
        args = []

        if self.use_gitignore:
            try:
                git_root = subprocess.check_output(
                    ["git", "rev-parse", "--show-toplevel"],
                    text=True
                ).strip()
                args.extend(["--glob", f"!{git_root}/.gitignore"])
            except subprocess.CalledProcessError:
                pass

        if not self.include_dotfiles:
            args.extend(["--hidden", "--glob", "!.*"])

        if self.search_dirs_only:
            args.extend(["--type", "d"])

        if self.search_files_only:
            args.extend(["--type", "f"])

        args.extend(["--glob", "!.git"])

        args.extend(self.extra_globs)

        return args
class BaseState:
    def __init__(self):
        self.use_gitignore = True
        self.state_stack = []

    def push_state(self):
        self.state_stack.append(copy.deepcopy(self.__dict__))

    def pop_state(self):
        if self.state_stack:
            self.__dict__.update(self.state_stack.pop())

    def toggle_use_gitignore(self):
        self.use_gitignore = not self.use_gitignore


class MenuApp:
    def __init__(self):
        self.state_stack = []
        self.current_state = MenuState()

    def push_state(self):
        self.state_stack.append(copy.deepcopy(self.current_state))

    def pop_state(self):
        self.current_state = self.state_stack.pop()
class MenuState:
    def __init__(self):
        self.mode = 'edit'
        self.use_gitignore = True
        self.path = ''
        self.state_stack = []
    def toggle_search_options(self):
        self.use_gitignore = not self.use_gitignore

    def change_mode(self, new_mode):
        self.mode = new_mode

class AppState:
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

    def push_state(self):
        self.state_stack.append(self.__dict__.copy())

    def pop_state(self):
        if self.state_stack:
            self.__dict__.update(self.state_stack.pop())

    def toggle_use_gitignore(self):
        self.use_gitignore = not self.use_gitignore

    def toggle_include_dotfiles(self):
        self.include_dotfiles = not self.include_dotfiles

    def toggle_search_dirs_only(self):
        self.search_dirs_only = not self.search_dirs_only

    def toggle_search_files_only(self):
        self.search_files_only = not self.search_files_only

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

        if choice == f"Use .gitignore: {not state.use_gitignore}":
            state.toggle_use_gitignore()
        elif choice == f"Include dotfiles: {not state.include_dotfiles}":
            state.toggle_include_dotfiles()
        elif choice == f"Search dirs only: {not state.search_dirs_only}":
            state.toggle_search_dirs_only()
        elif choice == f"Search files only: {not state.search_files_only}":
            state.toggle_search_files_only()
        elif choice == "Continue":
            break


class ClipboardManager:
    def __init__(self):
        self.queue = []

    def add_by_pattern(self, pattern: str):
        try:
            files = subprocess.check_output(["rg", "--files", pattern], text=True).splitlines()
        except subprocess.CalledProcessError:
            files = [pattern]

        for f in files:
            if f not in self.queue:
                self.queue.append(f)

    def add_by_regex(self, pattern: str):
        regex = re.compile(pattern)
        matches = [
            f for f in find_files_recursive()
            if regex.search(f)
        ]
        for f in matches:
            if f not in self.queue:
                self.queue.append(f)

    def remove(self, files: list[str]):
        self.queue = [f for f in self.queue if f not in files]

    def show_queue(self):
        return self.queue.copy()

    def commit(self):
        try:
            all_content = subprocess.check_output(["cat"] + self.queue, text=True)
            subprocess.run(["xclip", "-selection", "clipboard"], input=all_content, text=True)
        except Exception:
            pass
        self.queue.clear()


def clipboard_mode_menu(manager: ClipboardManager):
    while True:
        options = [
            "Add files by pattern",
            "Add files by regex",
            "Remove file(s) from queue",
            "Show queue",
            "Commit and exit",
            "Cancel"
        ]

        choice = rofi_select(options, prompt="Clipboard mode")

        if choice == "Add files by pattern":
            pattern = rofi_select([], prompt="Enter pattern")
            if pattern:
                manager.add_by_pattern(pattern)

        elif choice == "Add files by regex":
            pattern = rofi_select([], prompt="Enter regex pattern")
            if pattern:
                manager.add_by_regex(pattern)

        elif choice == "Remove file(s) from queue":
            if not manager.queue:
                continue
            selection = rofi_select(manager.queue, prompt="Remove files", multi_select=True)
            if selection:
                manager.remove(selection)

        elif choice == "Show queue":
            queue_str = "\n".join(manager.show_queue()) or "[Queue empty]"
            rofi_select([queue_str], prompt="Current clipboard queue")

        elif choice == "Commit and exit":
            manager.commit()
            break

        elif choice == "Cancel":
            break
import subprocess

class FzfDir:
    def __init__(self, app_state, editor_cmd):
        self.app_state = app_state
        self.editor_cmd = editor_cmd

    def get_entries(self, cwd_entries):
        # Placeholder: Implement actual logic to get directory entries
        # Returns a list of entries based on cwd_entries and app_state filters
        return []  # Replace with actual implementation

    def run_rofi(self, options, entries):
        menu_list = options + entries
        rofi_input = "\n".join(menu_list)
        try:
            result = subprocess.run(
                ["rofi", "-dmenu", "-multi-select", "-p", "Select files or options"],
                input=rofi_input.encode(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            output = result.stdout.decode().strip()
            return output.split("\n") if output else []
        except subprocess.CalledProcessError:
            return []

    def fzf_dir(self, cwd_entries):
        raw_entries = self.get_entries(cwd_entries)

        if self.app_state.regex_mode and self.app_state.regex_pattern:
            filtered_entries = [
                e for e in raw_entries if re.search(self.app_state.regex_pattern, e)
            ]
        else:
            filtered_entries = raw_entries

        extended_options = [
            "[Toggle Search Options]",
            f"[Change Mode: {self.app_state.current_mode}]",
            "---",
        ]

        selection = self.run_rofi(extended_options, filtered_entries)

        if not selection:
            # Fallback menu - here assumed to be re-running with entries or other logic
            self.menu(filtered_entries)
            return

        # Handle extended options exactly
        for item in selection:
            if item == "[Toggle Search Options]":
                self.toggle_menu()
                self.fzf_dir(cwd_entries)
                return
            elif item.startswith("[Change Mode:"):
                self.mode_menu()
                self.fzf_dir(cwd_entries)
                return

        # Filter out extended options from selection to get only files
        files = [item for item in selection if not item.startswith("[")]

        if not files:
            self.menu(filtered_entries)
            return

        mode = self.app_state.current_mode
        if mode == "Traverse":
            pass  # no-op
        elif mode == "Edit":
            subprocess.run([self.editor_cmd] + files)
        elif mode == "Execute":
            for f in files:
                subprocess.run(["bash", f])
        elif mode == "Clipboard":
            self.app_state.clipboard_queue.extend(files)
            self.clipboard_mode_menu()
            self.fzf_dir(cwd_entries)
            return

    def toggle_menu(self):
        # Implement toggle search options logic
        pass

    def mode_menu(self):
        # Implement mode change logic
        pass

    def menu(self, entries):
        # Implement fallback menu logic
        pass

    def clipboard_mode_menu(self):
        # Implement clipboard mode menu logic
        pass

import subprocess
import re

class FzfDir:
    def __init__(self, app_state, editor_cmd):
        self.app_state = app_state
        self.editor_cmd = editor_cmd

    def get_entries(self, cwd_entries):
        # Placeholder: Implement logic to return list of directory entries from cwd_entries
        return []  # Replace with actual implementation

    def run_rofi(self, options, entries):
        menu_items = options + entries
        rofi_input = "\n".join(menu_items)
        try:
            result = subprocess.run(
                ["rofi", "-dmenu", "-multi-select", "-p", "Select files or options"],
                input=rofi_input.encode(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            output = result.stdout.decode().strip()
            return output.splitlines() if output else []
        except subprocess.CalledProcessError:
            return []

    def fzf_dir(self, cwd_entries):
        raw_entries = self.get_entries(cwd_entries)

        if getattr(self.app_state, "regex_mode", False) and self.app_state.regex_pattern:
            filtered_entries = [
                e for e in raw_entries if re.search(self.app_state.regex_pattern, e)
            ]
        else:
            filtered_entries = raw_entries

        extended_options = [
            "[Toggle Search Options]",
            f"[Change Mode: {self.app_state.current_mode}]",
            "---",
        ]

        selection = self.run_rofi(extended_options, filtered_entries)

        if not selection:
            self.menu(filtered_entries)
            return

        for item in selection:
            if item == "[Toggle Search Options]":
                self.toggle_menu()
                self.fzf_dir(cwd_entries)
                return
            elif item.startswith("[Change Mode:"):
                self.mode_menu()
                self.fzf_dir(cwd_entries)
                return

        files = [item for item in selection if not item.startswith("[")]

        if not files:
            self.menu(filtered_entries)
            return

        mode = self.app_state.current_mode
        if mode == "Traverse":
            pass
        elif mode == "Edit":
            subprocess.run(
                [
                    "xterm",
                    "-fa",
                    "DejaVu Sans Mono Book",
                    "-fs",
                    "12",
                    "-e",
                    self.editor_cmd,
                    *files,
                ]
            )
        elif mode == "Execute":
            for f in files:
                subprocess.run(["bash", f])
        elif mode == "Clipboard":
            self.app_state.clipboard_queue.extend(files)
            self.clipboard_mode_menu()
            self.fzf_dir(cwd_entries)
            return

    def toggle_menu(self):
        # Implement toggle search options logic
        pass

    def mode_menu(self):
        # Implement mode change logic
        pass

    def menu(self, entries):
        # Implement fallback menu logic
        pass

    def clipboard_mode_menu(self):
        # Implement clipboard mode menu logic
        pass


if __name__ == "__main__":
    state = AppState()
    main_menu(find_subdirs('.'))
