from pathlib import Path
from filesystem.filesystem import list_files, list_directories
from core.core import edit_files
from state.search_options import SearchOptions
from state.workspace_utils import get_filtered_workspace_paths
from filesystem.tree_utils import build_tree, flatten_tree
from filters.main import get_entries
from menu_manager.frontend import run_fzf, run_rofi, run_via_socket

import socket
import json
import re
import logging

class MenuManager:
    def __init__(self, state, backend=None, frontend=None, host='127.0.0.1', port=65432):
        self.state = state
        self.backend = backend or "fzf"
        self.frontend = frontend or "fzf"
        self.search_options = SearchOptions(self, state)
        self.menu_structure_callable = self._get_main_menu_structure
        self.socket_conn = None
        self.host = host
        self.port = port


    def _get_main_menu_structure(self):
        """Dynamically builds the main menu structure, especially for save status."""

        print(f"Auto-Save: {self.state.auto_save_enabled}")
        
        return {
            'Workspace Tree': self.browse_workspace,
            'Search Workspace': self.search_workspace,
            'Filters': self.search_options.run_menu,
            'Workspace Management': self._get_workspace_management_menu, 
            'Clipboard Management': {
                'Commit clipboard queue to the clipboard': lambda: None,
                'Add to workspace paths to clipboard queue': self.add_workspace_to_clipboard,
                'Add cwd paths to clipboard queue': self.add_cwd_to_clipboard,
                'Remove from clipboard queue': self.remove_from_clipboard,
            },
        }
    
   
    def _get_workspace_management_menu(self):
        """Dynamically builds the Workspace Management sub-menu, including dynamic labels."""
        
        # This print will now run every time the WORKSPACE MANAGEMENT sub-menu is generated.
        logging.info(f"Generating Workspace Management Menu - Auto-Save State: {self.state.auto_save_enabled}")

        save_status_text = ""
        if self.state.auto_save_enabled:
            save_status_text = " (Auto-Save ON)"
        elif self.state.is_dirty:
            save_status_text = " (Unsaved Changes)"
        else:
            save_status_text = " (Saved)"
            
        save_option_label = f"Save Workspace{save_status_text}"
        auto_save_toggle_label = f"Auto-Save: {'On' if self.state.auto_save_enabled else 'Off'}"

        return {
            'Traverse to a new directory': self.traverse_directory,
            'Add files': self.add_files,
            'Remove files': self.remove_files,
            'Generator Blacklist': self.manage_generator_blacklist,
            'Reset Workspace': self.reset_workspace,
            save_option_label: self.save_workspace,
            'Save Workspace As...': self.save_workspace_as,
            auto_save_toggle_label: self.toggle_auto_save,
        }
    

    def main_loop(self):
        """
        The main loop for the MenuManager, now establishing and managing
        the client-side socket connection if backend is "socket".
        """
        if self.backend == "socket-client":
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.connect((self.host, self.port))
                    self.socket_conn = s
                    logging.info(f"[MenuManager Client] Connected to server on {self.host}:{self.port}")

                    # --- IMPORTANT: COMMUNICATION PROTOCOL ---
                    # You need a clear protocol for how the server sends menu data
                    # and how the client sends selections back.
                    # For example, the server might send a JSON string,
                    # and the client might send a simple string.

                    # Example of receiving menu data from the server:
                    # This is a basic example; you'd likely need a loop
                    # and more robust handling for incomplete messages.
                    received_data = s.recv(4096).decode('utf-8') # Adjust buffer size as needed
                    logging.info(f"Received raw data from server: {received_data}")

                    # Assuming server sends entries as a comma-separated string for simplicity
                    # In a real app, use JSON or a structured format.
                    menu_entries_from_server = received_data.split(',') if received_data else []


                    # Now navigate the menu using the received data
                    args = json.loads(received_data) 
                    logging.debug(f"Args: {args}")
                    while True: 
                        selection = self.run_selector(
                            args['entries'],
                            args['prompt'],
                            args['multi_select'],
                            args['text_input']
                        )
                        try:
                            response = json.dumps({"selection": selection})
                            s.sendall(response.encode('utf-8'))
                            logging.info(f"[MenuManager Client] Sent selection: {selection}")
                        except Exception as e:
                            logging.info(f"[MenuManager Client] Failed to send selection: {e}")
                            break

                except ConnectionRefusedError:
                    print(f"Connection refused. Server on {self.host}:{self.port} not running or inaccessible.")
                except Exception as e:
                    logging.error(f"An error occurred in client main_loop: {e}")
                finally:
                    self.socket_conn = None # Clear connection after use
                    print("[MenuManager Client] Socket connection closed.")
        elif self.backend == "socket":
            # Create a socket object
            # socket.AF_INET refers to the address family (IPv4)
            # socket.SOCK_STREAM refers to the socket type (TCP)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind((self.host, self.port)) # Bind the socket to the host and port
                    s.listen() # Enable the server to accept connections
                    logging.info(f"[MenuManager Server] Listening on {self.host}:{self.port}")

                    # Accept an incoming connection
                    conn, addr = s.accept() # This blocks until a client connects
                    with conn: # 'conn' is the new socket object used to communicate with the client
                        self.socket_conn = conn # Store the client connection
                        print(f"[MenuManager Server] Connected by {addr}")

                        # Now you would typically handle communication with the client here
                        # For example, sending menu data and receiving choices
                        menu = self.menu_structure_callable()
                        menu_data = {
                            "entries": list(menu.keys()),
                            "prompt": "Select an option",
                            "multi_select": False,
                            "text_input": False
                        }
                        conn.sendall(json.dumps(menu_data).encode("utf-8"))

                        received = conn.recv(4096).decode("utf-8")
                        selected = json.loads(received)["selection"][0]
                        action = menu.get(selected) # You'd need to adapt this for server-client communication

                except OSError as e:
                    logging.error(f"Server error: {e}. Address already in use or permission denied.")
                except Exception as e:
                    logging.error(f"An error occurred in server main_loop: {e}")
                finally:
                    self.socket_conn = None # Clear connection after use
                    print("[MenuManager Server] Socket server stopped.")
        else:
            # Fallback for local fzf/rofi usage if backend is not "socket"
            print(f"[MenuManager Local] Running in local mode with backend: {self.backend}")
            self.navigate_menu(self.menu_structure_callable)

    def navigate_menu(self, menu_source):
        while True:
            current_menu_dict = menu_source() if callable(menu_source) else menu_source
            if not current_menu_dict: return

            choice = self.run_selector(list(current_menu_dict.keys()), prompt="Select an option")
            
            if not choice:
                logging.info("[MenuManager] User cancelled selector or received empty choice. Exiting current menu level.")
                return 'CANCELLED' # Propagate cancellation

            selected_option_key = choice[0]
            action = current_menu_dict.get(selected_option_key)

            # Handle explicit signals first
            if action == 'EXIT_SIGNAL':
                logging.info("[MenuManager] 'Exit Application' selected. Signaling application exit.")
                return 'EXIT_SIGNAL'
            elif action == 'BACK_SIGNAL':
                logging.info("[MenuManager] 'Back to Main Menu' selected. Signaling return to parent.")
                return 'BACK_SIGNAL'

            if callable(action) and not isinstance(action, type(self._get_main_menu_structure)) \
                                and not (hasattr(action, '__name__') and action.__name__ in ['_get_main_menu_structure', '_get_workspace_management_menu', 'run_menu']):
                action() # Execute the command
            elif isinstance(action, dict) or callable(action):
                result = self.navigate_menu(action)
                if result in ['EXIT_SIGNAL', 'BACK_SIGNAL', 'CANCELLED']:
                    return result # Propagate signals from sub-menus
            elif action is None:
                logging.info(f"[MenuManager] Warning: No action found for selected key: '{selected_option_key}'")

  
    def search_workspace(self):
        entries = get_entries(self.state)
        entries_str = [str(e) for e in entries]
        tree = build_tree(entries_str)
        choices = flatten_tree(tree)

        while True:
            selection = self.run_selector(choices, prompt="Workspace Files")
            if not selection:
                return
            edit_files([Path(s) for s in selection])

    def get_root_dir(self) -> Path:
        root = self.state.root_dir
        if not root:
            root = Path(".")
        elif isinstance(root, str):
            root = Path(root)
        self.state.root_dir = root.resolve()
        return self.state.root_dir

    def traverse_directory(self):
        while True:
            root_dir = self.get_root_dir()
            dirs = list_directories(root_dir)
            selection = self.run_selector([str(d) for d in dirs], prompt="Select Directory")
            if not selection:
                return
            self.state.root_dir = dirs[[str(d) for d in dirs].index(selection[0])]

    def add_files(self):
        while True:
            root_dir = self.get_root_dir()
            entries = list_files(root_dir)
            selection = self.run_selector([str(e) for e in entries], prompt="Select Files to Add", multi_select=True)
            if not selection:
                return
            selected = [entries[[str(e) for e in entries].index(s)] for s in selection]
            self.state.workspace.add(selected, root_dir=root_dir)

    def remove_files(self):
        while True:
            entries = self.state.workspace.list()
            selection = self.run_selector([str(p) for p in entries], prompt="Select Files to Remove", multi_select=True)
            if not selection:
                return
            selected = [entries[[str(e) for e in entries].index(s)] for s in selection]
            self.state.workspace.remove(selected)

    def add_workspace_to_clipboard(self):
        while True:
            entries = self.state.workspace.list()
            selection = self.run_selector([str(p) for p in entries], prompt="Select Workspace Paths", multi_select=True)
            if not selection:
                return
            selected = [entries[[str(e) for e in entries].index(s)] for s in selection]
            self.state.clipboard.add_files(selected)

    def add_cwd_to_clipboard(self):
        while True:
            root_dir = self.get_root_dir()
            entries = list_files(root_dir)
            selection = self.run_selector([str(e) for e in entries], prompt="Select CWD Files", multi_select=True)
            if not selection:
                return
            selected = [entries[[str(e) for e in entries].index(s)] for s in selection]
            self.state.clipboard.add_files(selected)

    def remove_from_clipboard(self):
        while True:
            entries = self.state.clipboard.get_files()
            selection = self.run_selector([str(p) for p in entries], prompt="Select Clipboard Paths to Remove", multi_select=True)
            if not selection:
                return
            selected = [entries[[str(e) for e in entries].index(s)] for s in selection]
            self.state.clipboard.remove_files(selected)

    def browse_workspace(self):
        while True:
            entries = sorted(str(p) for p in self.state.workspace.list())
            choice = self.run_selector(entries, prompt="Select Root")
            if not choice:
                return
            selected_path = Path(choice[0])
            if selected_path.is_file():
                edit_files([selected_path])
            else:
                self._browse_tree(choice[0])

    def _browse_tree(self, current_dir):
        cur_path = Path(current_dir).resolve()
        stack = []

        while True:
            try:
                entries = sorted(cur_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            except Exception:
                entries = []

            display = [f"{e.name}/" if e.is_dir() else e.name for e in entries]
            choice = self.run_selector(display, prompt=str(cur_path))
            if not choice:
                if stack:
                    cur_path = stack.pop()
                    continue
                return

            name = choice[0].rstrip("/")
            next_path = cur_path / name
            logging.info(next_path)
            if next_path.is_dir():
                stack.append(cur_path)
                cur_path = next_path
            else:
                edit_files([next_path])


    def manage_generator_blacklist(self):
        blacklist_menu = {
            'View current patterns': self._view_blacklist_patterns,
            'Add new pattern': self._add_blacklist_pattern,
            'Remove pattern': self._remove_blacklist_pattern,
        }
        self.navigate_menu(blacklist_menu)

    def _view_blacklist_patterns(self):
        patterns = self.state.workspace.get_generator_blacklist_patterns()
        if not patterns:
            self.run_selector(["No blacklist patterns configured."], prompt="Generator Blacklist (Read-Only)")
            return
        display_patterns = [f"{i+1}. {p}" for i, p in enumerate(patterns)]
        self.run_selector(display_patterns, prompt="Generator Blacklist (Read-Only)")

    def _add_blacklist_pattern(self):
        prompt_text = "Enter new regex pattern (e.g., .*/__pycache__.*)"
        new_pattern_result = self.run_selector([], prompt=prompt_text)
        
        if not new_pattern_result or not new_pattern_result[0]:
            logging.debug("No new pattern entered.")
            return
        
        new_pattern = new_pattern_result[0].strip()
        if not new_pattern:
            self.run_selector(["Pattern cannot be empty."], prompt="Error")
            return

        try:
            re.compile(new_pattern)
        except re.error as e:
            self.run_selector([f"Invalid Regex: {e}"], prompt="Error")
            print(f"[ERROR] Invalid regex pattern entered: '{new_pattern}' - {e}")
            return

        self.state.workspace.add_generator_blacklist_pattern(new_pattern)
        # Manually set dirty flag for now.
        self.state.is_dirty = True
        self.run_selector([f"Pattern '{new_pattern}' added. Status updated."], prompt="Success")


    def _remove_blacklist_pattern(self):
        patterns = self.state.workspace.get_generator_blacklist_patterns()
        if not patterns:
            self.run_selector(["No blacklist patterns to remove."], prompt="Generator Blacklist")
            return
        
        display_patterns = [f"{i+1}. {p}" for i, p in enumerate(patterns)]
        selection_list = self.run_selector(display_patterns, prompt="Select pattern(s) to remove", multi_select=True)
        if not selection_list:
            logging.debug("No pattern selected for removal.")
            return

        removed_any = False
        for sel_str in selection_list:
            try:
                parts = sel_str.split(' ', 1)
                if len(parts) > 1:
                    pattern_to_remove = parts[1]
                    self.state.workspace.remove_generator_blacklist_pattern(pattern_to_remove)
                    removed_any = True
                    logging.info(f"Removed generator blacklist pattern: '{pattern_to_remove}'")
                else:
                    logging.warning(f"Could not parse selection string '{sel_str}', skipping.")
            except Exception as e:
                print(f"[ERROR] Error removing pattern '{sel_str}': {e}")
        
        if removed_any:
            # Manually set dirty flag for now.
            self.state.is_dirty = True
            self.run_selector([f"Removed pattern(s). Status updated."], prompt="Success")
        else:
            self.run_selector(["No patterns removed."], prompt="Info")

    def reset_workspace(self):
        confirm_options = ["Yes, reset it", "No, keep it"]
        confirmation = self.run_selector(confirm_options, prompt="Are you sure you want to reset workspace? This will clear all user-added paths and custom ignored paths.")
        if confirmation and confirmation[0] == "Yes, reset it":
            self.state.workspace.reset()
            # Manually set dirty flag for now.
            self.state.is_dirty = True
            self.run_selector(["Workspace reset to generated defaults. Status updated."], prompt="Success")
            logging.info("[INFO] Workspace reset performed.")
        else:
            self.run_selector(["Workspace reset cancelled."], prompt="Cancelled")
            logging.info("[INFO] Workspace reset cancelled by user.")

    def save_workspace(self):
        """Conditionally saves workspace or indicates status."""
        current_path = self.state.workspace.get_current_json_file_path()

        if self.state.auto_save_enabled:
            self.run_selector([f"Auto-Save is ON. Workspace is automatically saved to {current_path}."], prompt="Auto-Save Status")
        elif self.state.is_dirty:
            confirm_options = [f"Yes, save to {current_path}", "No, cancel"]
            confirmation = self.run_selector(confirm_options, prompt="Confirm Save")
            if confirmation and confirmation[0].startswith("Yes"):
                self.state.workspace.save()
                self.state.is_dirty = False # Clear dirty flag after explicit save
                self.run_selector([f"Workspace saved to {current_path}"], prompt="Success")
            else:
                self.run_selector(["Save cancelled."], prompt="Cancelled")
        else: # No unsaved changes and auto-save is off
            self.run_selector([f"Workspace is currently saved to {current_path} (No unsaved changes)."], prompt="Save Status")

    def save_workspace_as(self):
        """Prompts user for a new path and saves the workspace there."""
        current_path = self.state.workspace.get_current_json_file_path()
        prompt_text = f"Enter new workspace file path (Current: {current_path})"
        
        new_path_result = self.run_selector([], prompt=prompt_text)
        
        if not new_path_result or not new_path_result[0]:
            self.run_selector(["No path entered. Save cancelled."], prompt="Cancelled")
            return
        
        new_path_str = new_path_result[0].strip()
        if not new_path_str:
            self.run_selector(["Empty path entered. Save cancelled."], prompt="Cancelled")
            return

        new_path = Path(new_path_str).resolve()

        self.state.workspace.save(new_path)
        self.state.is_dirty = False # Clear dirty flag after explicit save as
        self.run_selector([f"Workspace saved to new path: {new_path}"], prompt="Success")
        logging.info(f"Workspace file path changed to: {new_path}")

    def toggle_auto_save(self):
        self.state.auto_save_enabled = not self.state.auto_save_enabled
        status = "On" if self.state.auto_save_enabled else "Off"
        # self.run_selector([f"Auto-Save turned {status}."], prompt="Auto-Save Status")
        logging.info(f"Auto-Save toggled to: {status}")
        # Note: We are not auto-saving here yet. That will be the next step.
    def run_selector(self, entries, prompt, multi_select=False, text_input=True):
        """
        This method now determines the UI backend.
        If backend is "socket", it handles the network communication.
        """
        if self.interface == "socket":
            if not self.socket_conn:
                print("Error: Socket connection not established for 'socket' backend.")
                return [] # Simulate cancellation on error

            menu_data_to_send = {
                "prompt": prompt,
                "entries": [str(e) for e in entries],
                "multi_select": multi_select,
                "text_input": text_input
            }
            
            print(f"[MenuManager Client Socket] Sending menu to server: '{prompt}' with {len(entries)} entries...")

            try:
                # Send the menu data to the server
                menu_json = json.dumps(menu_data_to_send)
                self.socket_conn.sendall(menu_json.encode('utf-8'))

                # Receive the selection from the server
                data = self.socket_conn.recv(4096)
                if not data:
                    print("Server disconnected during selection reception.")
                    return [] # Simulate user cancelling or server closing

                selection = data.decode('utf-8')
                print(f"[MenuManager Client Socket] Received selection from server: '{selection}'")
                return [selection] if selection else []
            except Exception as e:
                print(f"Error during socket communication in run_selector: {e}")
                return [] # Simulate user cancelling on error
            
        if self.backend == "socket-client":
            logging.debug("Socket Client")
            if self.frontend == "fzf":
                logging.debug("Frontend: fzf")
                return run_fzf(entries, prompt, multi_select, text_input)
            elif self.frontend == "rofi":
                logging.debug("Frontend: rofi")
                return run_rofi(entries, prompt, multi_select, text_input)
            else:
                raise ValueError(f"Unknown selector backend: {self.backend}")
        elif self.backend == "fzf":
            return run_fzf(entries, prompt, multi_select, text_input)
        elif self.backend == "rofi":
            return run_rofi(entries, prompt, multi_select, text_input)
        else:
            raise ValueError(f"Unknown selector backend: {self.backend}")
