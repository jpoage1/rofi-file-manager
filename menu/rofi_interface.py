# rofi_interface.py
import subprocess
import socket

def run_selector(backend, entries, prompt, multi_select=False, text_input=True):
    if backend == "fzf":
        return run_fzf(entries, prompt, multi_select, text_input)
    elif backend == "rofi":
        return run_rofi(entries, prompt, multi_select, text_input)
    elif backend == "vim":
        return run_via_socket(entries, prompt, multi_select, text_input)
    else:
        raise ValueError(f"Unknown selector backend: {backend}")

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

def run_via_socket(entries, prompt, multi_select=False, text_input=True, server_address=('localhost', 12345)):
    # Prepare data payload (e.g., JSON)
    import json
    data = {
        "entries": entries,
        "prompt": prompt,
        "multi_select": multi_select,
        "text_input": text_input
    }
    payload = json.dumps(data).encode()

    # Connect to socket server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(server_address)
        sock.sendall(payload)
        sock.shutdown(socket.SHUT_WR)  # Indicate no more data to send

        # Receive response (blocking)
        chunks = []
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
        response_data = b"".join(chunks).decode()

    # Assume response_data is JSON list of selected entries
    try:
        result = json.loads(response_data)
    except Exception:
        result = []

    return result


def run_rofi(entries, prompt, multi_select=False, text_input=True):
    cmd = ["rofi", "-dmenu", "-p", prompt]
    if multi_select:
        cmd.append("-multi-select")
    proc = subprocess.run(cmd, input="\n".join(entries), text=True, capture_output=True)
    if proc.returncode != 0:
        return []
    result = proc.stdout.strip()
    return result.splitlines() if multi_select else [result] if result else []

def toggle_option(state, option_name):
    current = getattr(state, option_name)
    setattr(state, option_name, not current)
