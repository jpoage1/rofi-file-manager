# plugins/interface/cli_interface.py
import logging 

interface_type = "stateful"
name = "cli"

def add_arguments(parser):
    pass

def run_cli_interface(manager):
    # This loop is primarily for non-socket (CLI) interfaces
    while True:
        menu = manager.main_menu()
        exit(0)
        entries = list(menu.keys())
        selection = manager.run_selector(entries, "Select an option", False, False)
        if not selection:
            return
        elif menu.get(selection[0]):
            menu.get(selection[0])() # Execute the selected action
        else:
            logging.warning(f"[MenuManager] Invalid selection: {selection}. Please try again.")

def interface(config):
    return run_cli_interface(config)
