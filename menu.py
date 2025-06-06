# menu.py
import subprocess
import re
import sys
from pathlib import Path

import os

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
                if Path(p).name == filename:
                    return str(Path(p).resolve())
            return None
        return str((Path(self.state.root_dir) / filename).resolve())

    def list_directories(self, base_dir):
        base = Path(base_dir)
        try:
            return [d.name for d in base.iterdir() if d.is_dir()]
        except Exception:
            return []

    def list_files(self, base_dir):
        base = Path(base_dir)
        try:
            return [f.name for f in base.iterdir() if f.is_file()]
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
            entries = [Path(p).name for p in self.state.input_set]
            print("DEBUG: MULTI mode entries:", entries, file=sys.stderr)
            return self.filter_entries(entries)

        base = self.state.root_dir
        print("DEBUG: os.listdir('/') =", os.listdir('/'), file=sys.stderr)
        print("DEBUG: root_dir =", base, file=sys.stderr)
        if not base:
            print("DEBUG: root_dir is empty or None", file=sys.stderr)
            return []

        base_path = Path(base)
        print("DEBUG: base_path.exists() =", base_path.exists(), file=sys.stderr)
        print("DEBUG: base_path.is_dir() =", base_path.is_dir(), file=sys.stderr)

        try:
            dirs = []
            files = []
            for p in base_path.iterdir():
                if p.is_dir():
                    dirs.append(p.name)
                elif p.is_file():
                    files.append(p.name)

            entries = []
            if self.state.show_dirs:
                entries.extend(dirs)
            if self.state.show_files:
                entries.extend(files)

            print("DEBUG: dirs =", dirs, file=sys.stderr)
            print("DEBUG: files =", files, file=sys.stderr)
            print("DEBUG: combined entries =", entries, file=sys.stderr)
        except Exception as e:
            print("DEBUG: Exception while listing base_path:", e, file=sys.stderr)
            entries = []


        filtered = self.filter_entries(entries)
        print("DEBUG: filtered entries =", filtered, file=sys.stderr)
        return filtered

    def edit_files(self, files):
        if not files:
            return
        # Convert to absolute paths using Path
        abs_files = [str(Path(f).resolve()) for f in files]
        cmd = ["xterm", "-fa", "DejaVu Sans Mono Book", "-fs", "12", "-e", self.editor] + abs_files
        subprocess.run(cmd)

    def toggle_option(self, option_name):
        current = getattr(self.state, option_name, None)
        if current is not None:
            setattr(self.state, option_name, not current)

    def toggle_menu(self):
        while True:
            entries = [
                f"[Show files: {'on' if getattr(self.state, 'show_files', True) else 'off'}]",
                f"[Show directories: {'on' if getattr(self.state, 'show_dirs', True) else 'off'}]",
                f"[Use gitignore: {'on' if getattr(self.state, 'use_gitignore', False) else 'off'}]",
                f"[Include dotfiles: {'on' if getattr(self.state, 'include_dotfiles', False) else 'off'}]",
                "[Back]"
            ]
            choice = self.run_rofi(entries, "Toggle options", False)
            if not choice or choice[0] == "[Back]":
                return
            if "Use gitignore" in choice[0]:
                self.toggle_option("use_gitignore")
            elif "Include dotfiles" in choice[0]:
                self.toggle_option("include_dotfiles")
            elif "Show files" in choice[0]:
                self.toggle_option("show_files")
            elif "Show directories" in choice[0]:
                self.toggle_option("show_dirs")
    def mode_menu(self):
        modes = ["Edit", "Traverse", "Execute", "Clipboard"]
        choice = self.run_rofi(modes, f"Change mode (current: {getattr(self.state, 'current_mode', '')})", False)
        if choice:
            self.state.current_mode = choice[0]

    def clipboard_mode_menu(self):
        all_files = [str(Path(self.state.root_dir) / f) for f in self.get_entries()]
        while True:
            entries = []
            clipboard_files = self.state.clipboard.get_files() if hasattr(self.state, 'clipboard') else []
            non_clipboard = [] if hasattr(self.state, 'clipboard') else []

            if non_clipboard:
                entries.append("[Add to Clipboard]")
            if clipboard_files:
                entries.append("[Remove from Clipboard]")
                entries.append("[Commit Clipboard]")
            entries.append("[Back]")

            choice = self.run_rofi(entries, "Clipboard options", False)
            if not choice:
                break
            c = choice[0]

            if c == "[Add to Clipboard]":
                selected = self.run_rofi(non_clipboard, "Add files to clipboard", True)
                paths = [self.resolve_path(f) for f in selected if self.resolve_path(f)]
                self.state.clipboard.add_files(paths)
            elif c == "[Remove from Clipboard]":
                selected = self.run_rofi(clipboard_files, "Remove files from clipboard", True)
                self.state.clipboard.remove_files(selected)
            elif c == "[Commit Clipboard]":
                self.state.clipboard.commit()
            elif c == "[Back]":
                break

    def cwd_menu(self):
        dirs = ["/", str(Path.home()), "/some/custom/dir"]
        workspace_entry = getattr(self.state.workspace, 'label', None)
        if workspace_entry and workspace_entry not in dirs:
            dirs.insert(0, workspace_entry)
        selected = self.run_rofi(dirs, "Change working directory", False)
        if selected:
            choice = selected[0]
            if self.state.mode == "MULTI" and hasattr(self.state, 'workspace') and choice == f"[{workspace_entry}]":
                self.state.workspace.reset()
            else:
                new_dir = Path(choice).expanduser()
                if new_dir.is_dir():
                    self.state.root_dir = str(new_dir.resolve())
                    self.state.mode = "NORMAL"

    def generate_menu_entries(self):
        entries = [
            "[Exit]",
            f"[CWD: {str(Path(self.state.root_dir).resolve()) if self.state.mode == 'NORMAL' else getattr(self.state.workspace, 'label', '')}]",
            "[Change CWD]",
            "[Manage Workspace]",
            "[Toggle Search Options]",
            f"[Change Mode: {getattr(self.state, 'current_mode', '')}]",
        ]
        if self.state.mode == "MULTI":
            entries.append("[Reset Workspace]")
        entries.append("---")
        entries += self.get_entries()
        return entries

    def handle_special_options(self, selection):
        for item in selection:
            if item == "[Exit]":
                sys.exit(0)
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
        elif self.state.current_mode == "Clipboard" and hasattr(self.state, 'clipboard'):
            self.state.clipboard.add_files(resolved)
            self.clipboard_mode_menu()
        elif self.state.current_mode == "Traverse":
            pass  # Placeholder for traversal logic

    def reset_to_files(self):
        input_paths = self.get_input_paths()
        abs_paths = [str(Path(p).resolve()) for p in input_paths] if input_paths else []
        if len(abs_paths) == 1 and Path(abs_paths[0]).is_dir():
            self.state.root_dir = abs_paths[0]
            self.state.mode = "NORMAL"
        elif abs_paths:
            self.state.input_set = abs_paths
            self.state.mode = "MULTI"
        else:
            self.state.root_dir = str(Path.cwd())
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
