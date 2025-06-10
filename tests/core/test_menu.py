# tests/test_manager.py
import pytest
from unittest.mock import patch, MagicMock
from core.menu import MenuManager


class DummyState:
    pass


@pytest.fixture
def dummy_state():
    return DummyState()


@patch("core.menu.load_plugins")
def test_menu_manager_initialization(mock_load_plugins, dummy_state):
    mock_plugin_instance = MagicMock()
    mock_load_plugins.return_value = [mock_plugin_instance]

    manager = MenuManager(
        state=dummy_state,
        interface="cli",
        frontend="test_frontend",
        host="192.168.1.100",
        port=12345
    )

    assert manager.state is dummy_state
    assert manager.interface == "cli"
    assert manager.frontend == "test_frontend"
    assert manager.host == "192.168.1.100"
    assert manager.port == 12345
    assert manager.plugins == [mock_plugin_instance]
    mock_load_plugins.assert_called_once_with(manager, dummy_state)


@patch("core.menu.load_plugins", return_value=[])
def test_menu_defaults(mock_load_plugins, dummy_state):
    menu = MenuManager(state=dummy_state)

    assert menu.interface == "cli"
    assert menu.frontend == "fzf"
    assert menu.host == "127.0.0.1"
    assert menu.port == 65432
