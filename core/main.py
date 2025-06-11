# Path: core/main.py
# Last Modified: 2025-06-11

import argparse
import logging
from threading import Thread
import sys

# Core application components
from core.menu import MenuManager
from core.state import State
from core.workspace import Workspace

# Your new plugin loaders
from core.plugins import InterfacePluginLoader, SelectorPluginLoader, MenuPluginLoader
from core.plugin_manager import PluginManager # Import the new manager class
# --- Component Configuration ---
def configure_stateful_components(args):
    """
    Initializes and configures the Workspace and State objects.
    Starts a background thread for workspace cache initialization.
    """
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

# --- Argument Parsing ---
def add_arguments(parser, plugin_manager_instance: PluginManager):
    """
    Adds common command-line arguments to the parser,
    including dynamically available interfaces and selectors.
    """
    # Use the PluginManager to get available plugin names for help text
    available_interfaces = ", ".join(plugin_manager_instance.get_plugin_list("interfaces")) or "none"
    available_selectors = ", ".join(plugin_manager_instance.get_plugin_list("selectors")) or "none"

    parser.add_argument("--workspace-file", default="workspace.json",
                        help="Path to the workspace JSON file.")
    parser.add_argument("--cwd", default=None,
                        help="Current working directory for relative paths.")
    parser.add_argument("--frontend", default=None,
                        help=f"Selects a specific frontend (e.g., fzf). Available: {available_selectors}")
    parser.add_argument("--interface", default=None,
                        help=f"Selects the primary user interface (e.g., cli, web). Available: {available_interfaces}")
    parser.add_argument("paths", nargs="*",
                        help="Additional paths to include in the workspace.")

# --- Main Application Flow ---
def main():
    # 1. Initialize the central PluginManager early
    plugin_manager = PluginManager()

    # 2. Instantiate and register loaders that don't depend on application state
    # These loaders will cache their plugins the first time they are accessed
    interface_loader = InterfacePluginLoader()
    selector_loader = SelectorPluginLoader()

    plugin_manager.register_loader("interfaces", interface_loader)
    plugin_manager.register_loader("selectors", selector_loader)

    parser = argparse.ArgumentParser(description="Your application description.")
    # Pass the plugin_manager instance to add_arguments
    add_arguments(parser, plugin_manager)

    # Parse only known args first to identify the requested interface early
    args, remaining = parser.parse_known_args()

    # --- Interface Plugin Selection ---
    # Retrieve plugin map and list from the PluginManager
    interface_plugin_map = plugin_manager.get_plugin_map("interfaces")
    interface_plugin_list = plugin_manager.get_plugin_list("interfaces")

    selected_plugin_instance = None

    # Attempt to select based on --interface argument
    if args.interface:
        if args.interface in interface_plugin_map:
            candidate_plugin = interface_plugin_map[args.interface]
            if hasattr(candidate_plugin, 'available') and not candidate_plugin.available():
                logging.warning(f"Requested interface '{args.interface}' is not available in the current environment. Attempting interactive selection.")
            else:
                selected_plugin_instance = candidate_plugin
                print(f"Selected interface plugin: {selected_plugin_instance.name}")
        else:
            logging.warning(f"Requested interface '{args.interface}' not found. Attempting interactive selection.")

    # If no plugin selected yet, or the requested one isn't available, prompt for interactive selection
    if selected_plugin_instance is None:
        if not interface_plugin_list:
            print("Error: No interface plugins available to load or select.", file=sys.stderr)
            sys.exit(1)

        print("\n--- Available Interfaces ---")
        for i, name in enumerate(interface_plugin_list):
            print(f"  {i+1}. {name}")

        while selected_plugin_instance is None:
            try:
                choice = input(f"Please select an interface (1-{len(interface_plugin_list)} or enter name): ").strip()
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(interface_plugin_list):
                        chosen_name = interface_plugin_list[idx]
                        chosen_plugin = interface_plugin_map[chosen_name]
                        if hasattr(chosen_plugin, 'available') and not chosen_plugin.available():
                            print(f"Interface '{chosen_name}' is not available in the current environment. Please choose another.")
                        else:
                            selected_plugin_instance = chosen_plugin
                            print(f"You selected: {selected_plugin_instance.name}")
                    else:
                        print("Invalid number. Please try again.")
                elif choice in interface_plugin_map:
                    chosen_plugin = interface_plugin_map[choice]
                    if hasattr(chosen_plugin, 'available') and not chosen_plugin.available():
                        print(f"Interface '{choice}' is not available in the current environment. Please choose another.")
                    else:
                        selected_plugin_instance = chosen_plugin
                        print(f"You selected: {selected_plugin_instance.name}")
                else:
                    print("Invalid input. Please enter a number or a valid interface name.")
            except EOFError:
                print("\nNo selection made. Exiting.")
                sys.exit(1)
            except Exception as e:
                logging.error(f"An unexpected error occurred during interface selection: {e}")
                sys.exit(1)

    # Add interface-specific arguments after an interface is selected
    if hasattr(selected_plugin_instance, 'add_arguments'):
        selected_plugin_instance.add_arguments(parser)

    # Parse full args with interface-specific options now that they've been added
    args = parser.parse_args()

    # Final validation of the selected plugin
    if selected_plugin_instance is None:
        print("Error: No valid interface plugin could be selected.", file=sys.stderr)
        sys.exit(1)
    if not hasattr(selected_plugin_instance, "interface_type"):
        print(f"Error: Selected plugin '{selected_plugin_instance.name}' is missing required attribute 'interface_type'.", file=sys.stderr)
        sys.exit(1)

    # --- Execute the selected interface ---
    if selected_plugin_instance.interface_type == "stateful":
        state = configure_stateful_components(args)
        
        menu_manager = MenuManager(state, args)
        
        # 3. Instantiate and register MenuPluginLoader only when state and menu_manager are available
        menu_loader = MenuPluginLoader(state_context=state, menu_context=menu_manager)
        plugin_manager.register_loader("menu", menu_loader)

        # The MenuManager's load_plugins method will now use the registered MenuPluginLoader
        # through the plugin_manager (or directly as it holds the loader instance).
        # We need to ensure MenuManager has access to the plugin_manager or the loader itself.
        # A clean way is to pass plugin_manager to MenuManager if MenuManager needs to load plugins later.
        # For now, MenuManager still directly calls its loader.
        menu_manager.register_plugin_manager(plugin_manager)
        menu_manager.register_menu_plugins(menu_loader)
        
        return selected_plugin_instance.interface(menu_manager)
    else:
        return selected_plugin_instance.interface(args)

if __name__ == "__main__":
    main()
