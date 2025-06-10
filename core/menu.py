# core/menu.py
from pathlib import Path
from core.utils import edit_files
import logging

from core.plugins import load_menu_plugins

# logging.basicConfig(level=logging.DEBUG)

from core.plugin_base import SubMenu

class MenuManager():
    def __init__(self, state, args):
        self.state = state
        self.interface = getattr(args, 'interface', 'cli')
        self.frontend = getattr(args, 'frontend', 'fzf')
        self.args = args
        self.plugins = None
        # self.search_options = SearchOptions(self, state)

    def load_plugins(self):
        self.plugins = load_menu_plugins(self, self.state)

    def main_menu(self):
        from core.plugin_base import MenuEntry, MenuEntries
        if not self.plugins:
            self.load_plugins()
        entries = []
        for plugin in self.plugins:
            entry = plugin._build_menu()
            if not isinstance(entry, MenuEntry):
                raise TypeError(MenuEntry)
            entries.append(entry)
        return MenuEntries(entries)
    def main_loop(self):
        from core.plugin_base import MenuEntry, PathEntry, MenuEntries
        stack = [self.main_menu()]
        i = 1
        while 0 < len(stack):
            current_stack = stack[-1]
            indexed_entries = []
            if isinstance(current_stack, MenuEntries):
                for entry in current_stack.children:
                    indexed_entries.append(entry.indexedLabel(len(indexed_entries)+1))
                choice = self.run_selector(indexed_entries, "Main Menu")
            elif isinstance(current_stack, MenuEntry):
                choice = current_stack.action()
                
                pass
            # No choice made
            if not choice:
                stack.pop()
                continue
            indices = [int(line.split(":", 1)[0]) for line in choice]
            info = [(int(line.split(":", 1)[0]), line.split(":", 1)[1].strip()) for line in choice]
            # Invalid selection
            if len(indices) < 1:
                continue
            index = indices[0]-1
            next_stack = current_stack.get(index)
            if not isinstance(next_stack, MenuEntry):
                raise AttributeError(MenuEntry)
            if isinstance(next_stack, PathEntry):
                pass
            stack.append(next_stack)
            
            # result = indexed_entries[indices[0]].action()
        # End While

    def run_selector(self, entries, prompt, multi_select=False, text_input=True):
        from core.selector import selector
        return selector(self.frontend, entries, prompt, multi_select, text_input)
        
    def navigate_menu(self, menu_source):
        while True:
            current_menu_dict = menu_source() if callable(menu_source) else menu_source
            if not current_menu_dict: return

            choice = self.run_selector(list(current_menu_dict.keys()), prompt="Select an option")
            
            if not choice:
                # logging.info("[MenuManager] User cancelled selector or received empty choice. Exiting current menu level.")
                return '' # Propagate cancellation

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
        entries = self.state.workspace.cache

        entries_str = [str(e) for e in entries]
        # These are redundant, but may become useful if future features require it
        # tree = build_tree(entries_str) # Create a directory tree
        # choices = flatten_tree(tree)
        choices = sorted(entries_str)

        while True:
            selection = self.run_selector(choices, prompt="Workspace Files")
            if not selection:
                return
            edit_files([Path(s) for s in selection])
    def navigate_menu_by_index(self, menu_source):
        while True:
            current_menu = menu_source() if callable(menu_source) else menu_source
            if not current_menu:
                return
            # Detect format: list-based (with dicts) or dict-based
            print(isinstance(current_menu, SubMenu))
            if isinstance(current_menu, SubMenu):
                entries = [item["name"] for item in current_menu if isinstance(item, dict) and "name" in item]
            elif isinstance(current_menu, dict):
                entries = list(current_menu.keys())
            else:
                logging.warning("[MenuManager] Unsupported menu structure.")
                return

            choice = self.run_selector(entries, prompt="Select an option")
            if not choice:
                return 'CANCELLED'

            selected_index = entries.index(choice[0])

            if isinstance(current_menu, list):
                selected_action = current_menu[selected_index]["action"]
            else:
                selected_key = entries[selected_index]
                selected_action = current_menu.get(selected_key)

            if selected_action == 'EXIT_SIGNAL':
                logging.info("[MenuManager] 'Exit Application' selected. Signaling application exit.")
                return 'EXIT_SIGNAL'
            elif selected_action == 'BACK_SIGNAL':
                logging.info("[MenuManager] 'Back to Main Menu' selected. Signaling return to parent.")
                return 'BACK_SIGNAL'

            if callable(selected_action) and not isinstance(selected_action, type(self._get_main_menu_structure)) \
                                        and not (hasattr(selected_action, '__name__') and selected_action.__name__ in ['_get_main_menu_structure', '_get_workspace_management_menu', 'run_menu']):
                selected_action()
            elif isinstance(selected_action, (dict, list)) or callable(selected_action):
                result = self.navigate_menu(selected_action)
                if result in ['EXIT_SIGNAL', 'BACK_SIGNAL', 'CANCELLED']:
                    return result
            elif selected_action is None:
                logging.info(f"[MenuManager] Warning: No action found for selected entry: '{choice[0]}'")
