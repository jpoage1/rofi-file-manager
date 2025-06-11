# Path: plugins/dual_socket_interface/dual_socket_interface.py
# Last Modified: 2025-06-11

# plugins/interface/dual_socket_interface.py
import subprocess
import sys
import logging
import signal
import socket
import sys

from core.plugin_base import InterfacePlugin

class DualSocketInterface(InterfacePlugin):
    interface_type = "stateless" # Stateless, because state isn't established until AFTER the server subprocess is launched
    name = "dual-socket"

    priority = 100

    @staticmethod
    def add_arguments(parser):
        parser.add_argument("--host", help="Server host to connect to")
        parser.add_argument("--port", type=int, help="Server port to connect to")
        parser.add_argument("--timeout", type=float, default=2.0, help="Connection timeout in seconds")
        parser.add_argument("--retry-interval", type=float, default=0.05, help="Retry interval in seconds")

    @staticmethod
    def get_free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]
        
    @staticmethod
    def terminate_process(proc, name, timeout=5):
        if proc.poll() is None:  # Process still running
            logging.info(f"Terminating {name} (pid={proc.pid})")
            proc.terminate()
            try:
                proc.wait(timeout=timeout)
                logging.info(f"{name} exited gracefully")
            except subprocess.TimeoutExpired:
                logging.warning(f"{name} did not exit in {timeout}s; killing")
                proc.kill()
                proc.wait()

    @staticmethod
    def spawn_socket_process(interface, args):
        return subprocess.Popen([
            sys.executable, __file__,
            "--interface", interface,
            *args
        ])
    
    @staticmethod
    def interface(args):
        DualSocketInterface.run_dual_socket_mode(args)
    
    @staticmethod
    def run_dual_socket_mode(args):
        args.host = args.host or '127.0.0.1'
        args.port = int(args.port) if getattr(args, 'port', None) else DualSocketInterface.get_free_port()
        
        # Define the truly common arguments that both server and client share,
        # *excluding* the frontend argument for now.
        base_args = [
            "--host", args.host,
            "--port", str(args.port),
            "--workspace-file", args.workspace_file,
            "--timeout", str(args.timeout),
            *args.paths
        ]

        if args.cwd:
            base_args.extend(["--cwd", args.cwd])

        # Arguments specifically for the server
        # The server always needs '--frontend=socket'
        server_args = list(base_args) # Start with a copy of base_args

        # Arguments specifically for the client
        # The client needs '--frontend' only if it was originally provided in args.frontend
        client_args = list(base_args) # Start with another copy of base_args
        if args.retry_interval:
            client_args.extend(["--retry-interval", str(args.retry_interval)])
        if args.frontend:
            client_args.extend(["--frontend", args.frontend])

        from core.payload import get_timestamp
        print(f"Server starting at {get_timestamp()}")

        # Spawn the server process with its specific arguments
        server_proc = DualSocketInterface.spawn_socket_process("socket-server", server_args)

        # Spawn the client process with its specific arguments
        client_proc = DualSocketInterface.spawn_socket_process("socket-client", client_args)
        print("Done")

        def cleanup(signum=None, frame=None):
            DualSocketInterface.terminate_process(client_proc, "Client")
            DualSocketInterface.terminate_process(server_proc, "Server")
            sys.exit(0)

        signal.signal(signal.SIGINT, cleanup)
        signal.signal(signal.SIGTERM, cleanup)

        try:
            client_proc.wait()
        finally:
            cleanup()

if __name__ == "__main__":
    import os
    current_file_path = os.path.abspath(__file__)
    path_to_interface_dir = os.path.dirname(current_file_path)
    path_to_plugins_dir = os.path.dirname(path_to_interface_dir)
    project_root_dir = os.path.dirname(path_to_plugins_dir) # This should now be '/srv/projects/editor-menu'

    if project_root_dir not in sys.path:
        sys.path.insert(0, project_root_dir)
    from core.main import main
    main()
