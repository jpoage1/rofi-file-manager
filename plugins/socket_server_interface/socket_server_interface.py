# plugins/interface/socket_server_interface.py
import socket
import json
import logging
import sys
from core.payload import send_message, recv_message, get_timestamp
from core.plugin_base import InterfacePlugin


class SocketServerInterface(InterfacePlugin):
    interface_type = "stateful"
    name = "socket-server"

    priority = 500

    @staticmethod
    def get_free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--host', default='127.0.0.1', help='Host address for socket server')
        parser.add_argument('--port', type=int, default=SocketServerInterface.get_free_port(), help='Port number for socket server')
        parser.add_argument("--timeout", type=float, default=5.0, help="Connection timeout in seconds")

    @staticmethod
    def interface(manager):
        SocketServerInterface.run_socket_server_interface(manager)

    @staticmethod
    def run_socket_server_interface(manager):
        args = manager.args
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((args.host, args.port))
                s.listen()
                print("Server Listening...")
                s.settimeout(args.timeout)
                conn, _ = s.accept()
                print(f"Accepting connections at {args.host}:{args.port}")
                print(f"Server Listening at {get_timestamp()}")
                with conn:
                    manager.run_selector = lambda entries, prompt, multi_select=False, text_input=True: SocketServerInterface.run_via_socket(conn, entries, prompt, multi_select, text_input)
                    def send(msg): send_message(conn, msg)
                    def recv(): return recv_message(conn, 'server')
                    manager.send = send
                    manager.recv = recv
                    result = manager.main_menu()
                    manager.main_loop()
                    if result in ['EXIT_SIGNAL']:
                        return
            except Exception as e:
                print(f"SERVER ERROR: {e}", file=sys.stderr)
                sys.exit(1) # Indicate failure
            finally:
                if 's' in locals():
                    s.close()
            sys.exit(0)
            
    @staticmethod
    def run_via_socket(conn, entries, prompt, multi_select, text_input):
        
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
