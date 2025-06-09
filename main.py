#!/usr/bin/env python
# main.py
import argparse
import socket
import subprocess
import sys
import time
import logging
import signal
from threading import Thread


from utils.utils import get_input_paths
from menu_manager import MenuManager
from state.state import State
from pathlib import Path
from state.workspace import Workspace
from menu_manager.interface import run_socket_client, run_socket_server, run_cli_app

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

# def main():
#     args = get_args()
#     # Begin threading
#     workspace = Workspace(
#         json_file=args.workspace_file,
#         paths=args.paths,
#         cwd=args.cwd
#     )
#     state = State(workspace)
#     workspace.set_state(state)
#     Thread(target=workspace.initialize_cache, daemon=True).start()

#     if state.is_dirty and state.auto_save_enabled:
#         logging.info("[INFO] Performing initial auto-save due to dirty state and auto-save being enabled.")
#         state.autoSave(state.workspace.save)

#     if args.interface == 'socket' or args.interface == 'sockets':
#         print("Starting in socket mode")
#         port = args.port or get_free_port()
#         host = args.host or '127.0.0.1'

#         common_args = [
#             "--host", host,
#             "--port", str(port),
#             "--workspace-file", args.workspace_file,
#             *args.paths
#         ]

#         if args.cwd:
#             common_args.extend(["--cwd", args.cwd])

#         server_proc = subprocess.Popen([
#             sys.executable, __file__,
#             "--interface", "socket-server",
#             *common_args
#         ])

#         time.sleep(1)

#         if args.frontend:
#             common_args.extend(["--frontend", args.frontend])
#         client_proc = subprocess.Popen([
#             sys.executable, __file__,
#             "--interface", "socket-client",
#             *common_args
#         ])

#         def cleanup(signum=None, frame=None):
#             terminate_process(client_proc, "Client")
#             terminate_process(server_proc, "Server")
#             sys.exit(0)

#         signal.signal(signal.SIGINT, cleanup)
#         signal.signal(signal.SIGTERM, cleanup)

#         try:
#             client_proc.wait()
#         finally:
#             cleanup()

#         return
#     # End threading

#     # Normal single instance mode
#     menu_manager = MenuManager(state, args.interface, args.frontend)
#     menu_manager.host = '127.0.0.1'
#     if hasattr(args, 'port') and args.port:
#         menu_manager.port = int(args.port)
#     else:
#         menu_manager.port = 12345

#     if args.interface == "socket-server" or args.interface == "sockets-server":
#         logging.info("[INFO] Starting application in server mode (interface: socket).")
        
#         run_socket_server(menu_manager)
#     elif args.interface == "socket-client" or  args.interface == "sockets-client":
#         logging.info("[INFO] Starting application in client mode (interface: socket-client).")
#         run_socket_client(host, port)
#     else:
#         logging.info("[INFO] Starting application in CLI mode.")
#         run_cli_app(menu_manager)
def spawn_socket_process(interface, common_args):
    return subprocess.Popen([
        sys.executable, __file__,
        "--interface", interface,
        *common_args
    ])



def run_dual_socket_mode(args):
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


def configure_stateful_components(args):
    workspace = Workspace(
        json_file=args.workspace_file,
        paths=args.paths,
        cwd=args.cwd
    )
    state = State(workspace)
    workspace.set_state(state)
    Thread(target=workspace.initialize_cache, daemon=True).start()

    if state.is_dirty and state.auto_save_enabled:
        logging.info("[INFO] Performing initial auto-save due to dirty state and auto-save being enabled.")
        state.autoSave(state.workspace.save)

    return state


def configure_menu_manager(state, args) -> MenuManager:
    return MenuManager(state, args.interface, args.frontend, args.host, args.port)

def main():
    args = get_args()
    args.host = args.host or '127.0.0.1'
    args.port = int(args.port) if getattr(args, 'port', None) else get_free_port()

    if args.interface in {'socket', 'sockets'}:
        print("Starting in socket mode")
        run_dual_socket_mode(args)
        return

    if args.interface in {"socket-client", "sockets-client"}:
        logging.info("[INFO] Starting application in client mode (interface: socket-client).")
        run_socket_client(args.host, args.port, args.frontend)
        return

    state = configure_stateful_components(args)

    if args.interface in {"socket-server", "sockets-server"}:
        logging.info("[INFO] Starting application in server mode (interface: socket-server).")
        run_socket_server(configure_menu_manager(state, args))
    else:
        logging.info("[INFO] Starting application in CLI mode.")
        run_cli_app(configure_menu_manager(state, args))


def get_args():
    parser = argparse.ArgumentParser(description="Manage workspace state")
    parser.add_argument("--workspace-file", default="workspace.json")
    parser.add_argument("--cwd", default=None)
    parser.add_argument("--frontend", default=None, help="Available frontends: fzf rofi cli")
    parser.add_argument("--interface", default=None, help="Interface type: 'socket-server' for stand-alone server, 'socket-client' for stand-alone client, 'socket' to launch both, or 'cli' for console.")
    parser.add_argument("--host", help="Host for socket communication")
    parser.add_argument("--port", type=int, help="Port number for socket communication")
    parser.add_argument("paths", nargs="*")
    return parser.parse_args()

if __name__ == "__main__":
    main()
