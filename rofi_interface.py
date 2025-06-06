# rofi_interface.py
import subprocess
import os
from core import get_entries

from filesystem import resolve_path

def run_rofi(entries, prompt, multi_select=False):
    cmd = ["rofi", "-dmenu", "-p", prompt]
    if multi_select:
        cmd.append("-multi-select")
    proc = subprocess.run(cmd, input="\n".join(entries), text=True, capture_output=True)
    if proc.returncode != 0:
        return []
    result = proc.stdout.strip()
    if multi_select:
        return result.splitlines() if result else []
    return [result] if result else []

def mode_menu(state):
    modes = ["Edit", "Traverse", "Execute", "Clipboard"]
    choice = run_rofi(modes, f"Change mode (current: {state.current_mode})", False)
    if choice:
        state.current_mode = choice[0]

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

def toggle_option(state, option_name):
    current = getattr(state, option_name)
    setattr(state, option_name, not current)

def clipboard_mode_menu(state):
    while True:
        entries = []
        all_files = [os.path.join(state.root_dir, f) for f in get_entries(state)]
        non_clipboard_files = [f for f in all_files if f not in state.clipboard.get_files()]

        if non_clipboard_files:
            entries.append("[Add to Clipboard]")
        elif state.clipboard.get_files():
            entries.append("[Remove from Clipboard]")
            entries.append("[Commit Clipboard]")
        entries.append("[Back]")

        choice = run_rofi(entries, "Clipboard options", False)
        if not choice:
            break
        c = choice[0]

        if c == "[Add to Clipboard]":
            files = get_entries(state)
            selected = run_rofi(files, "Add files to clipboard", True)
            paths = []
            for f in selected:
                resolved = resolve_path(state, f)
                if resolved:
                    paths.append(resolved)

            state.clipboard.add_files(paths)
        elif c == "[Remove from Clipboard]":
            selected = run_rofi(state.clipboard.get_files(), "Remove files from clipboard", True)
            state.clipboard.remove_files(selected)
        elif c == "[Commit Clipboard]":
            state.clipboard.commit()
        elif c == "[Back]":
            break
