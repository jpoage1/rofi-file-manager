import socket
import json
import logging

def run_socket_client(manager):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((manager.host, manager.port))
            manager.socket_conn = s
            data = s.recv(4096).decode('utf-8')
            args = json.loads(data)
            while True:
                selection = manager.run_selector(
                    args['entries'],
                    args['prompt'],
                    args['multi_select'],
                    args['text_input']
                )
                s.sendall(json.dumps({"selection": selection}).encode('utf-8'))
        except Exception as e:
            logging.error(f"[Client] Error: {e}")
        finally:
            manager.socket_conn = None

def run_socket_server(manager):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((manager.host, manager.port))
            s.listen()
            conn, _ = s.accept()
            with conn:
                manager.socket_conn = conn
                menu = manager.menu_structure_callable()
                data = {
                    "entries": list(menu.keys()),
                    "prompt": "Select an option",
                    "multi_select": False,
                    "text_input": False
                }
                conn.sendall(json.dumps(data).encode("utf-8"))
                received = conn.recv(4096).decode("utf-8")
                selected = json.loads(received)["selection"][0]
                action = menu.get(selected)
        except Exception as e:
            logging.error(f"[Server] Error: {e}")
        finally:
            manager.socket_conn = None
