#!/usr/bin/env python3
import os
import subprocess
import re
import copy

class State:
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
        snapshot = {
            "current_mode": self.current_mode,
            "use_gitignore": self.use_gitignore,
            "include_dotfiles": self.include_dotfiles,
            "search_dirs_only": self.search_dirs_only,
            "search_files_only": self.search_files_only,
            "regex_mode": self.regex_mode,
            "regex_pattern": self.regex_pattern,
            "root_dir": self.root_dir,
            "clipboard_queue": list(self.clipboard_queue),
        }
        self.state_stack.append(snapshot)

    def pop_state(self):
        if self.state_stack:
            snapshot = self.state_stack.pop()
            self.current_mode = snapshot["current_mode"]
            self.use_gitignore = snapshot["use_gitignore"]
            self.include_dotfiles = snapshot["include_dotfiles"]
            self.search_dirs_only = snapshot["search_dirs_only"]
            self.search_files_only = snapshot["search_files_only"]
            self.regex_mode = snapshot["regex_mode"]
            self.regex_pattern = snapshot["regex_pattern"]
            self.root_dir = snapshot["root_dir"]
            self.clipboard_queue = snapshot["clipboard_queue"]

def run_rofi(entries, prompt, multi_select=False):
    rofi_cmd = ["rofi", "-dmenu", "-p", prompt]
    if multi_select:
        rofi_cmd.append("-multi-select")
    proc = subprocess.run(rofi_cmd, input="\n".join(entries), text=True, capture_output=True)
    if proc.returncode != 0:
        return []
    result = proc.stdout.strip()
    if multi_select:
        return result.splitlines() if result else []
    else:
        return [result] if result else []

def list_directories(base_dir):
    try:
        return [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    except Exception:
        return []

def list_files(base_dir):
    try:
        return [f for f in os.listdir(base_dir) if os.path.isfile(os.path.join(base_dir, f))]
    except Exception:
        return []

def edit_files(files, editor="nvim"):
    if not files:
        return
    cmd = ["xterm", "-fa", "DejaVu Sans Mono Book", "-fs", "12", "-e", editor] + files
    subprocess.run(cmd)

def toggle_option(state, option_name):
    current = getattr(state, option_name)
    setattr(state, option_name, not current)

def toggle_menu(state):
    # Minimal example toggling use_gitignore and include_dotfiles
    entries = [
        f"[Use gitignore: {'on' if state.use_gitignore else 'off'}]",
        f"[Include dotfiles: {'on' if state.include_dotfiles else 'off'}]",
        "[Back]"
    ]
    choice = run_rofi(entries, "Toggle options", False)
    if not choice:
        return
    if choice[0] == "[Back]":
        return
    if "Use gitignore" in choice[0]:
        toggle_option(state, "use_gitignore")
    elif "Include dotfiles" in choice[0]:
        toggle_option(state, "include_dotfiles")

def mode_menu(state):
    modes = ["Edit", "Traverse", "Execute", "Clipboard"]
    choice = run_rofi(modes, f"Change mode (current: {state.current_mode})", False)
    if choice:
        state.current_mode = choice[0]

def get_entries(state):
    entries = []
    base = state.root_dir
    if state.search_dirs_only:
        entries = list_directories(base)
    elif state.search_files_only:
        entries = list_files(base)
    else:
        entries = os.listdir(base)

    # Apply regex filter if enabled
    if state.regex_mode and state.regex_pattern:
        regex = re.compile(state.regex_pattern)
        entries = [e for e in entries if regex.search(e)]

    # Filter dotfiles if needed
    if not state.include_dotfiles:
        entries = [e for e in entries if not e.startswith(".")]

    # Could apply gitignore filtering here if state.use_gitignore==True
    # (Skipping for brevity)

    return entries

def clipboard_mode_menu(state):
    entries = ["[Add to Clipboard]", "[Remove from Clipboard]", "[Commit Clipboard]", "[Back]"]
    while True:
        choice = run_rofi(entries, "Clipboard options", False)
        if not choice:
            break
        c = choice[0]
        if c == "[Add to Clipboard]":
            files = get_entries(state)
            selected = run_rofi(files, "Add files to clipboard", True)
            for f in selected:
                path = os.path.join(state.root_dir, f)
                if path not in state.clipboard_queue:
                    state.clipboard_queue.append(path)
        elif c == "[Remove from Clipboard]":
            if not state.clipboard_queue:
                continue
            selected = run_rofi(state.clipboard_queue, "Remove files from clipboard", True)
            for rem in selected:
                if rem in state.clipboard_queue:
                    state.clipboard_queue.remove(rem)
        elif c == "[Commit Clipboard]":
            content = ""
            for file_path in state.clipboard_queue:
                try:
                    with open(file_path, "r") as f:
                        content += f.read()
                except Exception:
                    pass
            if content:
                subprocess.run(["xclip", "-selection", "clipboard"], input=content, text=True)
            state.clipboard_queue.clear()
        elif c == "[Back]":
            break

def main():
    state = State()
    while True:
        entries = [
            "[Exit]",
            "[Toggle Search Options]",
            f"[Change Mode: {state.current_mode}]",
            "---"
        ] + get_entries(state)

        selection = run_rofi(entries, "Select files or options", True)
        if not selection:
            continue

        # Handle extended options
        handled = False
        for item in selection:
            if item == "[Exit]":
                exit(0)
            elif item == "[Toggle Search Options]":
                toggle_menu(state)
                handled = True
                break
            elif item.startswith("[Change Mode:"):
                mode_menu(state)
                handled = True
                break

        if handled:
            continue

        # Filter out extended options to get files only
        files = [item for item in selection if not item.startswith("[") and item != "---"]
        if not files:
            continue

        if state.current_mode == "Edit":
            edit_files([os.path.join(state.root_dir, f) for f in files])
        elif state.current_mode == "Execute":
            for f in files:
                path = os.path.join(state.root_dir, f)
                subprocess.run(["bash", path])
        elif state.current_mode == "Clipboard":
            for f in files:
                path = os.path.join(state.root_dir, f)
                if path not in state.clipboard_queue:
                    state.clipboard_queue.append(path)
            clipboard_mode_menu(state)
        elif state.current_mode == "Traverse":
            # Could add directory traversal here, skipping for brevity
            pass

if __name__ == "__main__":
    main()
