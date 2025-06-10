# plugins/interface/socket_client_interface.py
import socket
import json
import logging
import errno
import time

from menu_manager.payload import send_message, recv_message
from menu_manager.payload import get_timestamp

interface_type = "stateless"
name = "socket-client"

def add_arguments(parser):
    parser.add_argument("--host", help="Server host to connect to")
    parser.add_argument("--port", type=int, help="Server port to connect to")
    parser.add_argument("--timeout", type=float, default=2.0, help="Connection timeout in seconds")
    parser.add_argument("--retry-interval", type=float, default=0.05, help="Retry interval in seconds")

def run_socket_client_interface(config):
    host = config.get("host")
    port = config.get("port")
    timeout = config.get("timeout", 2.0)
    retry_interval = config.get("retry-interval", 0.05)
    frontend = config.get("frontend")
    selector = config.get("selector")

    start = time.time()
    connected = False
    while time.time() - start < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    connected = True
                    print(f"Client connecting to {host}:{port}")
                    print(f"Client connecting at {get_timestamp()}")
                    s.connect((host, port))
                    print(f"Client connected at {get_timestamp()}")
                    while True:
                        data = recv_message(s, 'client')
                        if not data:
                            print("No data received, exiting")
                            break
                        args = json.loads(data)
                        selection = selector(
                            frontend, 
                            args['entries'],
                            args['prompt'],
                            args['multi_select'],
                            args['text_input']
                        )
                        send_message(s, json.dumps({"selection": selection}), 'client')
                except Exception as e:
                    print(f"[Client] Error: {e}")
        except OSError as e:
            if e.errno not in (errno.ECONNREFUSED, errno.EHOSTUNREACH):
                raise
        time.sleep(retry_interval)
    if not connected:
        raise TimeoutError(f"Server did not become ready at {host}:{port} within {timeout} seconds.")

def interface(config):
    return run_socket_client_interface(config)
