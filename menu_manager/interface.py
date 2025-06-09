import socket
import json
import logging
from menu_manager.payload import send_message, recv_message
from menu_manager.frontend import run_fzf, run_rofi, run_cli_selector
from menu_manager.payload import get_timestamp

def run_socket_client(host, port, frontend):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
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

def run_socket_server(manager):
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



def selector(frontend, *args, **kwargs):
    if frontend == "fzf":
        return run_fzf(*args, **kwargs)
    elif frontend == "rofi":
        return run_rofi(*args, **kwargs)
    elif frontend == "cli":
        return run_cli_selector(*args, **kwargs)
    else:
        print(f"No selector found for {frontend}")
        exit(1)


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
