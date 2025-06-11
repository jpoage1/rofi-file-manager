# plugins/interface/socket_client_interface.py
import socket
import json
import logging
import errno
import sys
import time
import shutil

from core.payload import send_message, recv_message, get_timestamp
from core.plugin_base import InterfacePlugin

class SocketClientInterface(InterfacePlugin):
    interface_type = "stateless"
    name = "socket-client"

    @staticmethod
    def available():
        return shutil.which("fzf") is not None

    @staticmethod
    def add_arguments(parser):
        parser.add_argument("--host", default='127.0.0.1', help="Server host to connect to")
        parser.add_argument("--port", type=int, default=None, help="Server port to connect to")
        parser.add_argument("--timeout", type=float, default=5.0, help="Connection timeout in seconds")
        parser.add_argument("--retry-interval", type=float, default=0.05, help="Retry interval in seconds")

    @staticmethod
    def interface(args):
        SocketClientInterface.run_socket_client_interface(args)
        
    @staticmethod
    def run_socket_client_interface(args):
        from core.selector import selector
        print(args)
        frontend = args.frontend

        start = time.time()
        connected = False
        while time.time() - start < args.timeout:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    try:
                        connected = True
                        print(f"Client connecting to {args.host}:{args.port}")
                        print(f"Client connecting at {get_timestamp()}")
                        s.connect((args.host, args.port))
                        # s.settimeout(args.timeout)
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
                        print(f"CLIENT ERROR: {e}", file=sys.stderr)
                        # sys.exit(1) # Indicate failure
                    finally:
                        if 's' in locals():
                            s.close()
                    # End try
                # End socket
            except OSError as e:
                if e.errno not in (errno.ECONNREFUSED, errno.EHOSTUNREACH):
                    raise
            print(args)
            time.sleep(args.retry_interval)
        # End while    
        if not connected:
            raise TimeoutError(f"Server did not become ready at {args.host}:{args.port} within {args.timeout} seconds.")
        sys.exit(0) # Indicate success
