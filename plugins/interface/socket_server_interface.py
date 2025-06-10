# plugins/interface/socket_server_interface.py
import socket
import json
import logging
from menu_manager.payload import send_message, recv_message
from menu_manager.payload import get_timestamp

interface_type = "stateful"
name = "socket-server"

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def add_arguments(parser):
    parser.add_argument('--host', default=None, help='Host address for socket server')
    parser.add_argument('--port', type=int, default=None, help='Port number for socket server')

def run_socket_server_interface(manager):

    manager.host = manager.host or '127.0.0.1'
    manager.port = int(manager.port) if getattr(manager, 'port', None) else get_free_port()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((manager.host, manager.port))
            s.listen()
            print("Server Listening...")
            conn, _ = s.accept()
            print(f"Accepting connections at {manager.host}:{manager.port}")
            print(f"Server Listening at {get_timestamp()}")
            with conn:
                manager.socket_conn = conn
                def send(msg): send_message(conn, msg)
                def recv(): return recv_message(conn, 'server')
                manager.send = send
                manager.recv = recv
                result = manager.main_menu()
                if result in ['EXIT_SIGNAL']:
                    return

        except Exception as e:
            print(f"[Server] Error: {e}")
        finally:
            manager.socket_conn = None

def run_via_socket(conn, entries, prompt, multi_select=False, text_input=True):
    
    menu_data_to_send = {
        "prompt": prompt,
        "entries": entries,
        "multi_select": multi_select,
        "text_input": text_input
    }
    print("Sending socket packet", menu_data_to_send)
    send_message(conn, json.dumps(menu_data_to_send), 'server')

    data = recv_message(conn, 'server')
    if not data:
        return []
    try:
        selection_data = json.loads(data)
        print("Received pacet: ", selection_data)
        selection = selection_data.get("selection", [])
        if isinstance(selection, list):
            return selection
        return [selection]
    except (json.JSONDecodeError, KeyError):
        return []

def interface(config):
    return run_socket_server_interface(config)
