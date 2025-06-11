# Path: old/menu_manager/menu_local.py
# Last Modified: 2025-06-11

# menu_manager/menu_local
def run_local_menu(manager):
    print(f"[MenuManager Local] Running in local mode with backend: {manager.backend}")
    manager.navigate_menu(manager.menu_structure_callable)
