# core/menu.py
from pathlib import Path
from core.utils import edit_files
import logging

# from core.plugins import load_menu_plugins

# logging.basicConfig(level=logging.DEBUG)

from core.plugin_base import SubMenu
from core.plugins import MenuPluginLoader

class MenuManager():
    def __init__(self, state, args):
        self.state = state
        self.interface = getattr(args, 'interface', 'cli')
        self.frontend = getattr(args, 'frontend', 'fzf')
        self.args = args
        self.plugins = []
        self.plugin_manager = None
        self.interfaces = {}
        self.selectors = {}
        # self.search_options = SearchOptions(self, state)

    # def load_plugins(self):
    #     self.plugins = load_menu_plugins(self, self.state)

    # def load_plugins(self):
    #     # Instantiate MenuPluginLoader, passing self (the MenuManager instance)
    #     # as the 'menu' context and self.state as the 'state' context.
    #     menu_plugin_loader = MenuPluginLoader(menu_context=self, state_context=self.state)

    #     # Call load_plugins to get the list of instantiated MenuPlugin instances.
    #     # This will either load them for the first time (and cache) or return cached ones.
    #     self.plugins = menu_plugin_loader.load_plugins()

    #     print(f"MenuManager: Loaded {len(self.plugins)} menu plugins.")
    #     # You can now iterate self.plugins to interact with them, e.g.:
    #     # for plugin in self.plugins:
    #     #     plugin.do_something_with_menu() # Assuming your MenuPlugin has such a method

    def register_menu_plugins(self, menu_plugin_loader):
        """
        Registers menu plugins with the MenuManager.
        This method is expected to be called with an initialized MenuPluginLoader.
        It retrieves the sorted list of MenuPlugin instances from the loader.
        """
        if not hasattr(menu_plugin_loader, 'load_plugins'):
            raise ValueError("Provided menu_plugin_loader must have a 'load_plugins' method.")

        # Get the sorted list of instantiated MenuPlugin objects from the loader
        self.plugins = menu_plugin_loader.load_plugins()
        logging.info(f"MenuManager: Registered {len(self.plugins)} menu plugins.")

        # You can now iterate through self.plugins to integrate them into your menu logic
        # Example:
        # for plugin in self.plugins:
        #     print(f"Menu Plugin '{plugin.name}' ready.")
            # plugin.add_menu_items(self.menu_system) # if your menu plugins have this

    def register_plugin_manager(self, plugin_manager):
        self.plugin_manager = plugin_manager

    def run_selector(self, entries, prompt, multi_select=False, text_input=True):
        """
        Executes the selector plugin identified by self.frontend.
        """
        # Access the selector plugins via the PluginManager
        selector_plugin_map = self.plugin_manager.get_plugin_map("selectors")

        # Get the specific selector plugin instance for the chosen frontend
        selected_selector_plugin = selector_plugin_map.get(self.frontend)

        if not selected_selector_plugin:
            import sys # Import sys if not already at the top of core/menu.py
            logging.error(f"Error: No selector plugin found for frontend '{self.frontend}'.")
            sys.exit(1) # Or raise a custom exception

        # Call the 'selector' method on the retrieved plugin instance
        return selected_selector_plugin.selector(entries, prompt, multi_select, text_input)

    def main_menu(self):
        from core.plugin_base import MenuEntry, MenuEntries
        if not self.plugins:
            self.load_plugins()
        entries = []
        for plugin in self.plugins:
            entry = plugin._build_menu
            entries.append(entry)
        return MenuEntries(entries)
    def main_loop(self):
        from core.plugin_base import MenuEntry, PathEntry, MenuEntries
        stack = [self.main_menu()]
        i = 1
        while 0 < len(stack):
            current_stack = stack[-1]
            
            # Regenerate dynamic menus
            if callable(current_stack):
                current_stack = current_stack()
            loader_fn = getattr(current_stack, 'load', None)
            if callable(loader_fn):
                loader_fn()

            indexed_entries = []
            if isinstance(current_stack, MenuEntries):
                # Handle both root and submenu
                for child in current_stack.children:
                    entry = child() if callable(child) else child
                    indexed_entries.append(entry.indexedLabel(len(indexed_entries) + 1))
                choice = self.run_selector(indexed_entries, "Menu")
            elif isinstance(current_stack, MenuEntry):
                choice = current_stack.action()
            else:
                raise AttributeError(f"Expected MenuEntry or MenuEntries, got {type(current_stack)}")
            # No choice made
            if not choice:
                stack.pop()
                continue
            indices = [int(line.split(":", 1)[0]) for line in choice]
            # info = [(int(line.split(":", 1)[0]), line.split(":", 1)[1].strip()) for line in choice]
            # Invalid selection
            if len(indices) < 1:
                continue
            index = indices[0]-1
            next_stack = current_stack.get(index)
            stack.append(next_stack)
            
            # result = indexed_entries[indices[0]].action()
        # End While

    # def navigate_menu(self, menu_source):
    #     while True:
    #         current_menu_dict = menu_source() if callable(menu_source) else menu_source
    #         if not current_menu_dict: return

    #         choice = self.run_selector(list(current_menu_dict.keys()), prompt="Select an option")
            
    #         if not choice:
    #             # logging.info("[MenuManager] User cancelled selector or received empty choice. Exiting current menu level.")
    #             return '' # Propagate cancellation

    #         selected_option_key = choice[0]
    #         action = current_menu_dict.get(selected_option_key)

    #         # Handle explicit signals first
    #         if action == 'EXIT_SIGNAL':
    #             logging.info("[MenuManager] 'Exit Application' selected. Signaling application exit.")
    #             return 'EXIT_SIGNAL'
    #         elif action == 'BACK_SIGNAL':
    #             logging.info("[MenuManager] 'Back to Main Menu' selected. Signaling return to parent.")
    #             return 'BACK_SIGNAL'

    #         if callable(action) and not isinstance(action, type(self._get_main_menu_structure)) \
    #                             and not (hasattr(action, '__name__') and action.__name__ in ['_get_main_menu_structure', '_get_workspace_management_menu', 'run_menu']):
    #             action() # Execute the command
    #         elif isinstance(action, dict) or callable(action):
    #             result = self.navigate_menu(action)
    #             if result in ['EXIT_SIGNAL', 'BACK_SIGNAL', 'CANCELLED']:
    #                 return result # Propagate signals from sub-menus
    #         elif action is None:
    #             logging.info(f"[MenuManager] Warning: No action found for selected key: '{selected_option_key}'")

    # def search_workspace(self):
    #     entries = self.state.workspace.cache

    #     entries_str = [str(e) for e in entries]
    #     # These are redundant, but may become useful if future features require it
    #     # tree = build_tree(entries_str) # Create a directory tree
    #     # choices = flatten_tree(tree)
    #     choices = sorted(entries_str)

    #     while True:
    #         selection = self.run_selector(choices, prompt="Workspace Files")
    #         if not selection:
    #             return
    #         edit_files([Path(s) for s in selection])
    # def navigate_menu_by_index(self, menu_source):
    #     while True:
    #         current_menu = menu_source() if callable(menu_source) else menu_source
    #         if not current_menu:
    #             return
    #         # Detect format: list-based (with dicts) or dict-based
    #         print(isinstance(current_menu, SubMenu))
    #         if isinstance(current_menu, SubMenu):
    #             entries = [item["name"] for item in current_menu if isinstance(item, dict) and "name" in item]
    #         elif isinstance(current_menu, dict):
    #             entries = list(current_menu.keys())
    #         else:
    #             logging.warning("[MenuManager] Unsupported menu structure.")
    #             return

    #         choice = self.run_selector(entries, prompt="Select an option")
    #         if not choice:
    #             return 'CANCELLED'

    #         selected_index = entries.index(choice[0])

    #         if isinstance(current_menu, list):
    #             selected_action = current_menu[selected_index]["action"]
    #         else:
    #             selected_key = entries[selected_index]
    #             selected_action = current_menu.get(selected_key)

    #         if selected_action == 'EXIT_SIGNAL':
    #             logging.info("[MenuManager] 'Exit Application' selected. Signaling application exit.")
    #             return 'EXIT_SIGNAL'
    #         elif selected_action == 'BACK_SIGNAL':
    #             logging.info("[MenuManager] 'Back to Main Menu' selected. Signaling return to parent.")
    #             return 'BACK_SIGNAL'

    #         if callable(selected_action) and not isinstance(selected_action, type(self._get_main_menu_structure)) \
    #                                     and not (hasattr(selected_action, '__name__') and selected_action.__name__ in ['_get_main_menu_structure', '_get_workspace_management_menu', 'run_menu']):
    #             selected_action()
    #         elif isinstance(selected_action, (dict, list)) or callable(selected_action):
    #             result = self.navigate_menu(selected_action)
    #             if result in ['EXIT_SIGNAL', 'BACK_SIGNAL', 'CANCELLED']:
    #                 return result
    #         elif selected_action is None:
    #             logging.info(f"[MenuManager] Warning: No action found for selected entry: '{choice[0]}'")
