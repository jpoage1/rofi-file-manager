# Path: core/selector.py
# Last Modified: 2025-06-11

# core/selector.py

# Import the PluginManager from its new location
from core.plugin_manager import PluginManager

def selector(frontend, entries, prompt, multi_select=False, text_input=True):
    """
    Selects and invokes the appropriate selector plugin based on the 'frontend' argument.

    Args:
        frontend (str): The name of the selector plugin to use (e.g., 'fzf').
        entries (list): The list of items to select from.
        prompt (str): The prompt message to display to the user.
        multi_select (bool): Whether to allow multiple selections.
        text_input (bool): Whether to allow free-form text input.

    Returns:
        The result of the selected selector plugin's operation.
    """
    # Get the singleton instance of the PluginManager
    plugin_manager = PluginManager()

    # Get the map of selector plugin instances from the PluginManager
    # This will internally ensure the SelectorPluginLoader has loaded and cached the plugins.
    selector_plugin_map = plugin_manager.get_plugin_map("selectors")

    # Retrieve the specific selector plugin instance
    selected_selector_plugin = selector_plugin_map.get(frontend)

    if not selected_selector_plugin:
        print(f"Error: No selector plugin found for frontend '{frontend}'.", file=sys.stderr)
        # It's better to raise an exception or return a clear error value
        # instead of exiting directly, as this function might be called
        # from various parts of the application.
        # For now, matching old behavior:
        exit(1)

    # Call the 'selector' method on the retrieved plugin instance.
    # Note: Ensure your SelectorPlugin classes have a method named 'selector'
    # that matches this signature.
    return selected_selector_plugin.selector(entries, prompt, multi_select, text_input)
