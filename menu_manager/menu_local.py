def run_local_menu(manager):
    print(f"[MenuManager Local] Running in local mode with backend: {manager.backend}")
    manager.navigate_menu(manager.menu_structure_callable)
