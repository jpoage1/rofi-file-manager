# main.py
import argparse
import logging
from threading import Thread
import sys

from core.menu import MenuManager
from core.state import State
from core.workspace import Workspace

from core.plugins import load_interface_plugins

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

def main():
    parser = argparse.ArgumentParser()
    add_arguments(parser)  # Add common args

    # Parse only known args first to detect interface
    args, remaining = parser.parse_known_args()

    plugins = load_interface_plugins()
    plugin = plugins.get(args.interface)

    if plugin and hasattr(plugin, 'add_arguments'):
        plugin.add_arguments(parser)  # Add interface-specific args

    # Parse full args with interface-specific options
    args = parser.parse_args()

    if not hasattr(args, 'interface') or args.interface is None:
        print("Error: --interface argument is required.", file=sys.stderr)
        sys.exit(1)

    if plugin is None:
        print(f"Error: Interface plugin '{args.interface}' not found.", file=sys.stderr)
        sys.exit(1)

    if not hasattr(plugin, "interface_type"):
        print(f"Error: Plugin '{args.interface}' is missing required attribute 'interface_type'.", file=sys.stderr)
        sys.exit(1)

    if plugin.interface_type == "stateful":
        state = configure_stateful_components(args)
        config = MenuManager(state, args)
        return plugin.interface(config)
    else:
        return plugin.interface(args)

def add_arguments(parser):
    parser.add_argument("--workspace-file", default="workspace.json")
    parser.add_argument("--cwd", default=None)
    parser.add_argument("--frontend", default=None, help="Available frontends: fzf rofi cli")
    parser.add_argument("--interface", default=None, help="Interface type: 'socket-server' for stand-alone server, 'socket-client' for stand-alone client, 'socket' to launch both, or 'cli' for console.")
    parser.add_argument("paths", nargs="*")

if __name__ == "__main__":
    main()
