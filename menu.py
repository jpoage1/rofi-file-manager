# menu.py
# #!/usr/bin/env python3
import os
import subprocess
import re
import sys

class MenuManager:
    def __init__(self, state, editor="nvim", rofi_cmd="rofi"):
        self.state = state
        self.editor = editor
        self.rofi_cmd = rofi_cmd

    def run_rofi(self, entries, prompt, multi_select=False):
        cmd = [self.rofi_cmd, "-dmenu", "-p", prompt]
        if multi_select:
            cmd.append("-multi-select")
        proc = subprocess.run(cmd, input="\n".join(entries), text=True, capture_output=True)
        if proc.returncode != 0:
            return []
        output = proc.stdout.strip()
        return output.splitlines() if multi_select else ([output] if output else [])

    def resolve_path(self, filename):
        if self.state.mode == "MULTI":
            for p in self.state.input_set:
                if os.path.basename(p) == filename:
                    return os.path.abspath(p)
            return None
        return os.path.abspath(os.path.join(self.state.root_dir, filename))

    def list_directories(self, base_dir):
        try:
            return [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
        except Exception:
            return []

    def list_files(self, base_dir):
        try:
            return [f for f in os.listdir(base_dir) if os.path.isfile(os.path.join(base_dir, f))]
        except Exception:
            return []

    def filter_entries(self, entries):
        if self.state.regex_mode and self.state.regex_pattern:
            try:
                regex = re.compile(self.state.regex_pattern)
                entries = [e for e in entries if regex.search(e)]
            except re.error:
                entries = []
        if not self.state.include_dotfiles:
            entries = [e for e in entries if not e.startswith(".")]
        return entries

    def get_entries(self):
        if self.state.mode == "MULTI":
            entries = [os.path.basename(p) for p in self.state.input_set]
            return self.filter_entries(entries)

        base = self.state.root_dir
        if not base:
            return []

        if self.state.search_dirs_only:
            entries = self.list_directories(base)
        elif self.state.search_files_only:
            entries = self.list_files(base)
        else:
            try:
                entries = os.listdir(base)
            except Exception:
                entries = []

        return self.filter_entries(entries)

    def edit_files(self, files):
        if not files:
            return
        cmd = ["xterm", "-fa", "DejaVu Sans Mono Book", "-fs", "12", "-e", self.editor] + files
        subprocess.run(cmd)

    def toggle_option(self, option_name):
        current = getattr(self.state, option_name)
        setattr(self.state, option_name, not current)

    def toggle_menu(self):
        entries = [
            f"[Use gitignore: {'on' if self.state.use_gitignore else 'off'}]",
            f"[Include dotfiles: {'on' if self.state.include_dotfiles else 'off'}]",
            "[Back]"
        ]
        choice = self.run_rofi(entries, "Toggle options", False)
        if not choice or choice[0] == "[Back]":
            return
        if "Use gitignore" in choice[0]:
            self.toggle_option("use_gitignore")
        elif "Include dotfiles" in choice[0]:
            self.toggle_option("include_dotfiles")

    def mode_menu(self):
        modes = ["Edit", "Traverse", "Execute", "Clipboard"]
        choice = self.run_rofi(modes, f"Change mode (current: {self.state.current_mode})", False)
        if choice:
            self.state.current_mode = choice[0]

    def clipboard_mode_menu(self):
        while True:
            entries = []
            all_files = [os.path.join(self.state.root_dir, f) for f in self.get_entries()]
            non_clipboard = [f for f in all_files if f not in self.state.clipboard.get_files()]

            if non_clipboard:
                entries.append("[Add to Clipboard]")
            elif self.state.clipboard.get_files():
                entries.append("[Remove from Clipboard]")
                entries.append("[Commit Clipboard]")
            entries.append("[Back]")

            choice = self.run_rofi(entries, "Clipboard options", False)
            if not choice:
                break
            c = choice[0]

            if c == "[Add to Clipboard]":
                files = self.get_entries()
                selected = self.run_rofi(files, "Add files to clipboard", True)
                paths = [self.resolve_path(f) for f in selected if self.resolve_path(f)]
                self.state.clipboard.add_files(paths)
            elif c == "[Remove from Clipboard]":
                selected = self.run_rofi(self.state.clipboard.get_files(), "Remove files from clipboard", True)
                self.state.clipboard.remove_files(selected)
            elif c == "[Commit Clipboard]":
                self.state.clipboard.commit()
            elif c == "[Back]":
                break

    def cwd_menu(self):
        dirs = ["/", os.path.expandvars("$HOME"), "/some/custom/dir"]
        if self.state.mode == "MULTI":
            dirs.insert(0, f"[{self.state.workspace.label}]")
        selected = self.run_rofi(dirs, "Change working directory", False)
        if selected:
            choice = selected[0]
            if self.state.mode == "MULTI" and choice == f"[{self.state.workspace.label}]":
                self.state.workspace.reset()
            else:
                new_dir = os.path.expandvars(choice)
                if os.path.isdir(new_dir):
                    self.state.root_dir = new_dir
                    self.state.mode = "NORMAL"

    def generate_menu_entries(self):
        entries = [
            "[Exit]",
            f"[CWD: {os.path.abspath(self.state.root_dir) if self.state.mode == 'NORMAL' else self.state.workspace.label}]",
            "[Change CWD]",
            "[Manage Workspace]",
            "[Toggle Search Options]",
            f"[Change Mode: {self.state.current_mode}]",
        ]
        if self.state.mode == "MULTI":
            entries.append("[Reset Workspace]")
        entries.append("---")
        entries += self.get_entries()
        return entries

    def handle_special_options(self, selection):
        for item in selection:
            if item == "[Exit]":
                exit(0)
            elif item == "[Toggle Search Options]":
                self.toggle_menu()
                return True
            elif item == "[Change CWD]":
                self.cwd_menu()
                return True
            elif item.startswith("[Change Mode:"):
                self.mode_menu()
                return True
            elif item == "[Reset Workspace]":
                self.reset_to_files()
                return True
        return False

    def filter_file_entries(self, selection):
        return [item for item in selection if not item.startswith("[") and item != "---"]

    def dispatch_mode_action(self, resolved):
        if self.state.current_mode == "Edit":
            self.edit_files(resolved)
        elif self.state.current_mode == "Execute":
            for path in resolved:
                subprocess.run(["bash", path])
        elif self.state.current_mode == "Clipboard":
            self.state.clipboard.add_files(resolved)
            self.clipboard_mode_menu()
        elif self.state.current_mode == "Traverse":
            pass  # Traversal logic placeholder

    def reset_to_files(self):
        input_paths = self.get_input_paths()
        abs_paths = [os.path.abspath(p) for p in input_paths] if input_paths else []
        if len(abs_paths) == 1 and os.path.isdir(abs_paths[0]):
            self.state.root_dir = abs_paths[0]
            self.state.mode = "NORMAL"
        elif abs_paths:
            self.state.input_set = abs_paths
            self.state.mode = "MULTI"
        else:
            self.state.root_dir = os.getcwd()
            self.state.mode = "NORMAL"

    def get_input_paths(self):
        paths = []
        if len(sys.argv) > 1:
            paths.extend(sys.argv[1:])
        if not sys.stdin.isatty():
            paths.extend(line.strip() for line in sys.stdin if line.strip())
        return paths

    def main_loop(self):
        while True:
            entries = self.generate_menu_entries()
            selection = self.run_rofi(entries, "Select files or options", multi_select=True)
            if not selection:
                continue
            if self.handle_special_options(selection):
                continue
            files = self.filter_file_entries(selection)
            if not files:
                continue
            resolved = [self.resolve_path(f) for f in files if self.resolve_path(f)]
            if not resolved:
                continue
            self.dispatch_mode_action(resolved)
