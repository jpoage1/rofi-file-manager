# core/plugins.py
import importlib.util
import os
import importlib.util
import pathlib

from core.plugin_base import WorkspacePlugin

# def load_menu_plugins(menu, state):
#     plugin_dir = pathlib.Path(__file__).parent.parent / "plugins/menu"
#     plugins = []
#     for file in os.listdir(plugin_dir):
#         if file.endswith(".py") and not file.startswith("_"):
#             module_path = os.path.join(plugin_dir, file)
#             spec = importlib.util.spec_from_file_location(file[:-3], module_path)
#             module = importlib.util.module_from_spec(spec)
#             spec.loader.exec_module(module)

#             for obj in module.__dict__.values():
#                 if isinstance(obj, type) and issubclass(obj, WorkspacePlugin) and obj is not WorkspacePlugin:
#                     plugin_instance = obj(menu, state)
#                     # print(plugin_instance)
#                     plugins.append(plugin_instance)
#     # print(sorted(plugins, key=lambda p: p.priority or 1000))
#     # exit(0)
#     return sorted(plugins, key=lambda p: p.priority or 1000)

# def load_interface_plugins():
#     plugin_dir = pathlib.Path(__file__).parent.parent / "plugins/interface"
#     plugins = {}
#     for path in plugin_dir.glob("*.py"):
#         if path.name.startswith("_"):
#             continue
#         spec = importlib.util.spec_from_file_location(path.stem, path)
#         mod = importlib.util.module_from_spec(spec)
#         spec.loader.exec_module(mod)
#         if hasattr(mod, "name") and hasattr(mod, "interface"):
#             plugins[mod.name] = mod
#     return plugins

# def load_selector_plugins():
#     plugin_dir = pathlib.Path(__file__).parent.parent / "plugins/selector"
#     plugins = {}
#     for path in plugin_dir.glob("*.py"):
#         if path.name.startswith("_"):
#             continue
#         spec = importlib.util.spec_from_file_location(path.stem, path)
#         mod = importlib.util.module_from_spec(spec)
#         spec.loader.exec_module(mod)
#         if hasattr(mod, "name") and hasattr(mod, "selector"):
#             plugins[mod.name] = mod.selector
#     return plugins
import importlib.util
import pathlib
import os
from typing import List, Dict

PLUGIN_ROOT = pathlib.Path(__file__).parent.parent / "plugins"

def load_plugins(plugin: str, class_check=None, attr_checks=None, construct_args=()):
    plugins = []
    path_root = PLUGIN_ROOT / plugin

    for plugin_dir in path_root.iterdir():
        if not plugin_dir.is_dir():
            continue

        entry_point = plugin_dir / f"{plugin}/plugin.py"
        if not entry_point.exists():
            continue

        spec = importlib.util.spec_from_file_location(plugin_dir.name, entry_point)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        if class_check:
            for obj in mod.__dict__.values():
                if isinstance(obj, type) and issubclass(obj, class_check) and obj is not class_check:
                    plugins.append(obj(*construct_args))
        elif attr_checks:
            if all(hasattr(mod, attr) for attr in attr_checks):
                plugins.append(mod)
    return plugins

def load_menu_plugins(menu, state):
    from core.plugins_base import WorkspacePlugin
    return sorted(
        load_plugins("menu", class_check=WorkspacePlugin, construct_args=(menu, state)),
        key=lambda p: p.priority or 1000
    )

def load_interface_plugins() -> Dict[str, object]:
    mods = load_plugins("interface", attr_checks=("name", "interface"))
    return {mod.name: mod for mod in mods}

def load_selector_plugins() -> Dict[str, object]:
    mods = load_plugins("selector", attr_checks=("name", "selector"))
    return {mod.name: mod.selector for mod in mods}
