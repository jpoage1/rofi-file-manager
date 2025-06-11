# Path: core/plugin_manager.py
# Last Modified: 2025-06-11


class PluginManager:
    """
    Manages and provides access to different types of plugin loaders.
    This acts as a central registry for your application's plugins.
    """
    _instance = None # For singleton pattern (optional, but good for managers)

    def __new__(cls):
        # Implement a basic singleton pattern to ensure only one PluginManager exists
        if cls._instance is None:
            cls._instance = super(PluginManager, cls).__new__(cls)
            cls._instance._loaders = {} # Dictionary to hold loader instances
        return cls._instance

    def register_loader(self, plugin_type: str, loader_instance):
        """
        Registers a plugin loader instance for a specific plugin type.
        Args:
            plugin_type (str): A string identifier for the plugin type (e.g., "interface", "selector", "menu").
            loader_instance: An instance of a plugin loader (e.g., InterfacePluginLoader).
        """
        if not hasattr(loader_instance, 'load_plugins') or \
           not (hasattr(loader_instance, 'get_plugin_map') and hasattr(loader_instance, 'get_plugin_list')):
            raise ValueError(f"Loader for '{plugin_type}' must have load_plugins(), get_plugin_map(), and get_plugin_list() methods.")
        self._loaders[plugin_type] = loader_instance
        print(f"PluginManager: Registered loader for type '{plugin_type}'.")


    def get_loader(self, plugin_type: str):
        """
        Retrieves a registered loader for a given plugin type.
        Args:
            plugin_type (str): The identifier for the plugin type.
        Returns:
            An instance of the plugin loader, or None if not registered.
        """
        return self._loaders.get(plugin_type)

    def get_plugins(self, plugin_type: str):
        """
        Retrieves all loaded plugin instances for a given type.
        Internally calls the loader's load_plugins() method.
        Args:
            plugin_type (str): The identifier for the plugin type.
        Returns:
            A list of plugin instances.
        """
        loader = self.get_loader(plugin_type)
        if loader:
            return loader.load_plugins() # load_plugins triggers caching if not already loaded
        print(f"Warning: No loader registered for plugin type '{plugin_type}'. Returning empty list.")
        return []

    def get_plugin_map(self, plugin_type: str):
        """
        Retrieves the name-to-plugin-instance map for a given plugin type.
        Internally calls the loader's get_plugin_map() method.
        Args:
            plugin_type (str): The identifier for the plugin type.
        Returns:
            A dictionary mapping plugin names to plugin instances.
        """
        loader = self.get_loader(plugin_type)
        if loader and hasattr(loader, 'get_plugin_map'):
            return loader.get_plugin_map()
        print(f"Warning: No valid loader or get_plugin_map method for plugin type '{plugin_type}'. Returning empty map.")
        return {}

    def get_plugin_list(self, plugin_type: str):
        """
        Retrieves a list of plugin names for a given plugin type.
        Internally calls the loader's get_plugin_list() method.
        Args:
            plugin_type (str): The identifier for the plugin type.
        Returns:
            A list of plugin names (strings).
        """
        loader = self.get_loader(plugin_type)
        if loader and hasattr(loader, 'get_plugin_list'):
            return loader.get_plugin_list()
        print(f"Warning: No valid loader or get_plugin_list method for plugin type '{plugin_type}'. Returning empty list.")
        return []
