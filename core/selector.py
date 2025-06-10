# core/selector.py
def selector(frontend, entries, prompt, multi_select=False, text_input=True):
    from core.plugins import load_selector_plugins
    interface_plugins = load_selector_plugins()
    select_fn = interface_plugins.get(frontend)
    if not select_fn:
        print(f"No selector plugin found for {frontend}")
        exit(1)
    return select_fn(entries, prompt, multi_select, text_input)
