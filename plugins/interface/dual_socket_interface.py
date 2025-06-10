# plugins/interface/dual_socket_interface.py
import subprocess
import sys
import logging
import signal
import socket
import sys


interface_type = "stateless" # Stateless, because state isn't established until AFTER the server subprocess is launched
name = "dual-socket"

def add_arguments(parser):
    try:
        from plugins.interface.socket_client_interface import add_arguments as add_client_arguments
        add_client_arguments(parser)
    except ImportError as e:
        print(f"Error: Required client plugin not found: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        from plugins.interface.socket_server_interface import add_arguments as add_server_arguments
        add_server_arguments(parser)
    except ImportError as e:
        print(f"Error: Required server plugin not found: {e}", file=sys.stderr)
        sys.exit(1)
        
def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]
    
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

def spawn_socket_process(interface, common_args):
    return subprocess.Popen([
        sys.executable, __file__,
        "--interface", interface,
        *common_args
    ])

def run_dual_socket_mode(args):
    args.host = args.host or '127.0.0.1'
    args.port = int(args.port) if getattr(args, 'port', None) else get_free_port()

    common_args = [
        "--host", args.host,
        "--port", str(args.port),
        "--workspace-file", args.workspace_file,
        *args.paths
    ]
    if args.cwd:
        common_args.extend(["--cwd", args.cwd])
    if args.frontend:
        common_args.extend(["--frontend", args.frontend])
    
    from menu_manager.payload import get_timestamp
    print(f"Server starting at {get_timestamp()}")
    server_proc = spawn_socket_process("socket-server", common_args)
    client_proc = spawn_socket_process("socket-client", common_args)

    def cleanup(signum=None, frame=None):
        terminate_process(client_proc, "Client")
        terminate_process(server_proc, "Server")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        client_proc.wait()
    finally:
        cleanup()

def interface(config):
    return run_dual_socket_mode(config)
