# interface.py
import subprocess
import json

def run_fzf(entries, prompt, multi_select=False, text_input=True):
    cmd = ["fzf", "--prompt", prompt + ": "]
    if multi_select:
        cmd.append("--multi")
    if not text_input:
        cmd.append("--no-sort")
    proc = subprocess.run(cmd, input="\n".join(entries), text=True, capture_output=True)
    if proc.returncode != 0:
        return []
    result = proc.stdout.strip()
    return result.splitlines() if multi_select else [result] if result else []


def run_rofi(entries, prompt, multi_select=False, text_input=True):
    cmd = ["rofi", "-dmenu", "-p", prompt]
    if multi_select:
        cmd.append("-multi-select")
    proc = subprocess.run(cmd, input="\n".join(entries), text=True, capture_output=True)
    if proc.returncode != 0:
        return []
    result = proc.stdout.strip()
    return result.splitlines() if multi_select else [result] if result else []

def run_via_socket(conn, entries, prompt, multi_select=False, text_input=True):
    # This method in ServerMenuState would *send* the menu data to the client,
    # not call run_selector_via_socket directly.
    # It's the server's job to provide the menu data.
    # The client's run_selector_via_socket *receives* that data.

    # So, on the server, the logic would be:
    menu_data_to_send = {
        "prompt": prompt,
        "entries": entries,
        "multi_select": multi_select,
        "text_input": text_input
    }
    menu_json = json.dumps(menu_data_to_send)
    conn.sendall(menu_json.encode('utf-8'))

    # Wait for selection from the client
    data = conn.recv(4096)
    if not data:
        return [] # Client disconnected or error
    selection = data.decode('utf-8')
    return [selection] # Return as a list, like fzf/rofi would.
    
def toggle_option(state, option_name):
    current = getattr(state, option_name)
    setattr(state, option_name, not current)
