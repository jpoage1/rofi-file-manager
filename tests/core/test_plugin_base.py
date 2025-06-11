# Path: tests/core/test_plugin_base.py
# Last Modified: 2025-06-11

# tests/core/test_plugins.py

import os
from core.plugins import load_plugins
from core.plugin_base import WorkspacePlugin

def test_load_plugins(tmp_path, monkeypatch):
    # Write a dummy plugin to the temporary directory
    plugin_code = """
from core.plugin_base import WorkspacePlugin

class TestPlugin(WorkspacePlugin):
    priority = 10
    def _build_options(self):
        return ["Option"]
"""
    plugin_file = tmp_path / "test_plugin.py"
    plugin_file.write_text(plugin_code)

    # Monkeypatch os.listdir to return the dummy plugin file
    monkeypatch.setattr("core.plugins.os.listdir", lambda _: [plugin_file.name])

    # Monkeypatch os.path.join to handle variable arguments correctly
    real_join = os.path.join
    monkeypatch.setattr("core.plugins.os.path.join", lambda *args: real_join(*args))

    # Dummy menu and state objects
    menu = object()
    state = object()

    # Call the plugin loader
    plugins = load_plugins(menu, state, plugin_dir=str(tmp_path))

    # Assert plugin was loaded correctly
    assert len(plugins) == 1
    plugin = plugins[0]
    assert isinstance(plugin, WorkspacePlugin)
    assert plugin.priority == 10
    assert plugin.menu is menu
    assert plugin.state is state
