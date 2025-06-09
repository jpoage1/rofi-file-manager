import socket
import json
import logging
from menu_manager.payload import send_message, recv_message
def run_socket_client(manager):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((manager.host, manager.port))
            manager.socket_conn = s
            while True:
                data = recv_message(s, 'client')
                if not data:
                    print("No data received, exiting")
                    break
                args = json.loads(data)
                selection = manager.run_selector(
                    args['entries'],
                    args['prompt'],
                    args['multi_select'],
                    args['text_input']
                )
                send_message(s, json.dumps({"selection": selection}), 'client')
        except Exception as e:
            print(f"[Client] Error: {e}")
        finally:
            manager.socket_conn = None

def run_socket_server(manager):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((manager.host, manager.port))
            s.listen()
            print(f"Listening at {manager.host}:{manager.port}")
            conn, _ = s.accept()
            with conn:
                manager.socket_conn = conn
                def send(msg): send_message(conn, msg)
                def recv(): return recv_message(conn, 'server')
                manager.send = send
                manager.recv = recv
                result = manager.navigate_menu(manager.menu_structure_callable)
                if result in ['EXIT_SIGNAL']:
                    return

        except Exception as e:
            print(f"[Server] Error: {e}")
        finally:
            manager.socket_conn = None

def run_cli_app(manager):
    # This loop is primarily for non-socket (CLI) interfaces
    if manager.interface != "socket" and manager.interface != "socket-client":
        while True:
            menu = manager.menu_structure_callable()
            entries = list(menu.keys())
            selection = manager.run_selector(entries, "Select an option", False, False)
            if not selection:
                return
            elif menu.get(selection[0]):
                menu.get(selection[0])() # Execute the selected action
            else:
                logging.warning(f"[MenuManager] Invalid selection: {selection}. Please try again.")
    else:
        logging.info("[MenuManager] main_loop is not active for socket interfaces; socket functions handle the loop.")
