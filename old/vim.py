def run_fzf_socket_loop(entries, prompt="workspace>", multi_select=False, text_input=True, server_address=('localhost', 12345)):
    while True:
        payload = {
            "entries": entries,
            "prompt": prompt,
            "multi_select": multi_select,
            "text_input": text_input
        }

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(server_address)
                sock.sendall(json.dumps(payload).encode())
                sock.shutdown(socket.SHUT_WR)

                chunks = []
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)
                response = b''.join(chunks).decode()
        except Exception:
            break

        try:
            result = json.loads(response)
        except Exception:
            break

        if isinstance(result, list) and result:
            entries = result
        else:
            break

def main():
    entries = get_open_files()
    if entries:
        run_fzf_socket_loop(entries)

if __name__ == "__main__":
    main()
