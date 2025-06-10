# core/plugins.py
import importlib.util
import os
import importlib.util
import pathlib

from core.plugin_base import WorkspacePlugin

def load_menu_plugins(menu, state):
    plugin_dir = pathlib.Path(__file__).parent.parent / "plugins/menu"
    plugins = []
    for file in os.listdir(plugin_dir):
        if file.endswith(".py") and not file.startswith("_"):
            module_path = os.path.join(plugin_dir, file)
            spec = importlib.util.spec_from_file_location(file[:-3], module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for obj in module.__dict__.values():
                if isinstance(obj, type) and issubclass(obj, WorkspacePlugin) and obj is not WorkspacePlugin:
                    plugin_instance = obj(menu, state)
                    # print(plugin_instance)
                    plugins.append(plugin_instance)
    # print(sorted(plugins, key=lambda p: p.priority or 1000))
    # exit(0)
    return sorted(plugins, key=lambda p: p.priority or 1000)

def load_interface_plugins():
    plugin_dir = pathlib.Path(__file__).parent.parent / "plugins/interface"
    plugins = {}
    for path in plugin_dir.glob("*.py"):
        if path.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(path.stem, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "name") and hasattr(mod, "interface"):
            plugins[mod.name] = mod
    return plugins

def load_selector_plugins():
    plugin_dir = pathlib.Path(__file__).parent.parent / "plugins/selector"
    plugins = {}
    for path in plugin_dir.glob("*.py"):
        if path.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(path.stem, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "name") and hasattr(mod, "selector"):
            plugins[mod.name] = mod.selector
    return plugins
