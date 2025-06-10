# plugins/interface/socket_server_interface.py
import json
import logging
from menu_manager.payload import send_message, recv_message
from menu_manager.payload import get_timestamp

name = "socket"

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

def selector(entries, prompt, multi_select, text_input):
    return run_via_socket(entries, prompt, multi_select, text_input)
