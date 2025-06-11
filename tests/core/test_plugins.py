# Path: tests/core/test_plugins.py
# Last Modified: 2025-06-11

# tests/test_plugins.py
import os
import tempfile
import shutil
import types
import pytest
from core.plugins import load_plugins
from core.plugin_base import WorkspacePlugin


class DummyMenu:
    pass

class DummyState:
    pass


def create_dummy_plugin(path, class_name="TestPlugin", priority=100):
    with open(path, "w") as f:
        f.write(f"""
from core.plugin_base import WorkspacePlugin

class {class_name}(WorkspacePlugin):
    def __init__(self, menu, state):
        super().__init__(menu, state)
        self.priority = {priority}
""")


@pytest.fixture
def plugin_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_load_plugins(plugin_dir):
    plugin_path = os.path.join(plugin_dir, "plugin_a.py")
    create_dummy_plugin(plugin_path, class_name="PluginA", priority=50)

    plugin_path_2 = os.path.join(plugin_dir, "plugin_b.py")
    create_dummy_plugin(plugin_path_2, class_name="PluginB", priority=10)

    menu = DummyMenu()
    state = DummyState()
    plugins = load_plugins(menu, state, plugin_dir=plugin_dir)

    assert len(plugins) == 2
    assert all(isinstance(p, WorkspacePlugin) for p in plugins)
    assert type(plugins[0]).__name__ == "PluginB"  # lower priority value first
    assert type(plugins[1]).__name__ == "PluginA"
