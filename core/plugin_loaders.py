# Path: core/plugin_loaders.py
# Last Modified: 2025-06-11

import importlib
import os
import sys

# Assume PluginLoaderHelper is in plugin_loader_helper.py as before
# from plugin_loader_helper import PluginLoaderHelper

class PluginLoaderHelper:
    """
    A helper class for scanning plugin directories and loading plugin modules.
    """
    def __init__(self, plugin_base_dir="plugins"):
        self.plugin_base_dir = plugin_base_dir
        # Add the plugin base directory to the system path to allow direct imports
        if self.plugin_base_dir not in sys.path:
            sys.path.insert(0, self.plugin_base_dir)

    def _discover_plugin_paths(self):
        """
        Discovers all 'plugin.py' files within subdirectories of the plugin base directory.
        """
        plugin_paths = []
        if not os.path.exists(self.plugin_base_dir):
            print(f"Warning: Plugin base directory '{self.plugin_base_dir}' does not exist.")
            return []

        for item_name in os.listdir(self.plugin_base_dir):
            item_path = os.path.join(self.plugin_base_dir, item_name)
            if os.path.isdir(item_path):
                plugin_file = os.path.join(item_path, "plugin.py")
                if os.path.exists(plugin_file):
                    plugin_paths.append(plugin_file)
        return plugin_paths

    def load_plugin_modules(self):
        """
        Loads all plugin modules found in the plugin directory.
        Returns a dictionary where keys are module names and values are the loaded modules.
        """
        loaded_modules = {}
        plugin_paths = self._discover_plugin_paths()

        for plugin_path in plugin_paths:
            # Construct a module name relative to the plugin_base_dir
            # e.g., plugins/example_menu_plugin/plugin.py -> example_menu_plugin.plugin
            relative_path = os.path.relpath(plugin_path, self.plugin_base_dir)
            module_name = relative_path.replace(os.sep, ".")[:-len(".py")]

            try:
                module = importlib.import_module(module_name)
                loaded_modules[module_name] = module
                print(f"Successfully loaded plugin module: {module_name}")
            except Exception as e:
                print(f"Error loading plugin module '{module_name}': {e}")
        return loaded_modules

    @staticmethod
    def get_plugin_class(module, class_name):
        """
        Attempts to retrieve a specific class from a loaded module.
        """
        if hasattr(module, class_name):
            plugin_class = getattr(module, class_name)
            if isinstance(plugin_class, type): # Ensure it's actually a class
                return plugin_class
            else:
                print(f"Warning: '{class_name}' in module '{module.__name__}' is not a class.")
        return None

# Define the base plugin types for clarity (optional, but good practice)
# Make sure these are the same as defined in your actual project
class InterfacePlugin:
    name: str = ""
    priority: int = 0
    interface_type: str = "stateless" # Example default for validation
    def interface(self, *args, **kwargs):
        raise NotImplementedError

class MenuPlugin:
    name: str = ""
    priority: int = 0
    def __init__(self, menu, state):
        self.menu = menu
        self.state = state
        # raise NotImplementedError # Remove this in base class if not abstract

class SelectorPlugin:
    name: str = ""
    priority: int = 0
    def selector(self):
        raise NotImplementedError


class MenuPluginLoader:
    _loaded_plugins = None  # Class-level cache for loaded MenuPlugin instances

    def __init__(self, menu_context=None, state_context=None):
        self.loader_helper = PluginLoaderHelper()
        self.menu_context = menu_context
        self.state_context = state_context
        # Note: If menu_context or state_context can change between calls,
        # you might need to re-evaluate caching behavior for MenuPlugin.
        # For simplicity here, we assume if plugins are loaded, they are based on
        # the *initial* context. If context changes, you might need a way to clear the cache.

    def load_plugins(self):
        if MenuPluginLoader._loaded_plugins is not None:
            # If already loaded, return the cached instances
            # print("MenuPluginLoader: Returning cached plugins.")
            return MenuPluginLoader._loaded_plugins

        print("MenuPluginLoader: Loading plugins for the first time...")
        plugins = []
        loaded_modules = self.loader_helper.load_plugin_modules()
        for module_name, module in loaded_modules.items():
            menu_plugin_class = self.loader_helper.get_plugin_class(module, "MenuPlugin")
            if menu_plugin_class:
                try:
                    # Instantiate with required arguments
                    # IMPORTANT: If menu_context/state_context change, the cached instances
                    # might not have the correct context. Consider how you handle this.
                    if self.menu_context is None or self.state_context is None:
                        print(f"Warning: MenuPlugin '{menu_plugin_class.name}' requires menu/state context but not provided on first load. Instantiating without (may cause errors).", file=sys.stderr)
                        plugin_instance = menu_plugin_class(None, None) # Or raise error
                    else:
                        plugin_instance = menu_plugin_class(self.menu_context, self.state_context)
                    plugins.append(plugin_instance)
                    print(f"Loaded MenuPlugin: {plugin_instance.name} from {module_name}")
                except Exception as e:
                    print(f"Error instantiating MenuPlugin from {module_name}: {e}")

        plugins.sort(key=lambda p: p.priority, reverse=True)
        MenuPluginLoader._loaded_plugins = plugins # Cache the loaded plugins
        return plugins

class InterfacePluginLoader:
    _loaded_plugins = None  # Class-level cache for loaded InterfacePlugin instances
    _plugin_map = None      # Class-level cache for name-to-instance map
    _plugin_list = None     # Class-level cache for list of names

    def __init__(self):
        self.loader_helper = PluginLoaderHelper()

    def load_plugins(self):
        if InterfacePluginLoader._loaded_plugins is not None:
            # print("InterfacePluginLoader: Returning cached plugins.")
            return InterfacePluginLoader._loaded_plugins

        print("InterfacePluginLoader: Loading plugins for the first time...")
        plugins = []
        loaded_modules = self.loader_helper.load_plugin_modules()
        for module_name, module in loaded_modules.items():
            interface_plugin_class = self.loader_helper.get_plugin_class(module, "InterfacePlugin")
            if interface_plugin_class:
                try:
                    plugin_instance = interface_plugin_class()
                    plugins.append(plugin_instance)
                    print(f"Loaded InterfacePlugin: {plugin_instance.name} from {module_name}")
                except Exception as e:
                    print(f"Error instantiating InterfacePlugin from {module_name}: {e}")
        plugins.sort(key=lambda p: p.priority, reverse=True)
        InterfacePluginLoader._loaded_plugins = plugins # Cache the loaded plugins
        InterfacePluginLoader._plugin_map = {p.name: p for p in plugins}
        InterfacePluginLoader._plugin_list = [p.name for p in plugins]
        return plugins

    def get_plugin_map(self):
        # Ensure plugins are loaded before returning map
        if InterfacePluginLoader._loaded_plugins is None:
            self.load_plugins()
        return InterfacePluginLoader._plugin_map

    def get_plugin_list(self):
        # Ensure plugins are loaded before returning list
        if InterfacePluginLoader._loaded_plugins is None:
            self.load_plugins()
        return InterfacePluginLoader._plugin_list

class SelectorPluginLoader:
    _loaded_plugins = None  # Class-level cache for loaded SelectorPlugin instances
    _plugin_map = None
    _plugin_list = None

    def __init__(self):
        self.loader_helper = PluginLoaderHelper()

    def load_plugins(self):
        if SelectorPluginLoader._loaded_plugins is not None:
            # print("SelectorPluginLoader: Returning cached plugins.")
            return SelectorPluginLoader._loaded_plugins

        print("SelectorPluginLoader: Loading plugins for the first time...")
        plugins = []
        loaded_modules = self.loader_helper.load_plugin_modules()
        for module_name, module in loaded_modules.items():
            selector_plugin_class = self.loader_helper.get_plugin_class(module, "SelectorPlugin")
            if selector_plugin_class:
                try:
                    plugin_instance = selector_plugin_class()
                    plugins.append(plugin_instance)
                    print(f"Loaded SelectorPlugin: {plugin_instance.name} from {module_name}")
                except Exception as e:
                    print(f"Error instantiating SelectorPlugin from {module_name}: {e}")
        plugins.sort(key=lambda p: p.priority, reverse=True)
        SelectorPluginLoader._loaded_plugins = plugins # Cache the loaded plugins
        SelectorPluginLoader._plugin_map = {p.name: p for p in plugins}
        SelectorPluginLoader._plugin_list = [p.name for p in plugins]
        return plugins

    def get_plugin_map(self):
        if SelectorPluginLoader._loaded_plugins is None:
            self.load_plugins()
        return SelectorPluginLoader._plugin_map

    def get_plugin_list(self):
        if SelectorPluginLoader._loaded_plugins is None:
            self.load_plugins()
        return SelectorPluginLoader._plugin_list
