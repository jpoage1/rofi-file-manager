# menu/menu_options.py
menu = {
    'Workspace Manager': {
        'Browse Workspace': [
            MenuOption(label='Search Filters Menu option', action='filters'),
            MenuOption(label='Edit only mode', action='edit_only'),
            MenuOption(label='List all files', action='list_all_files', filter_files=True),
            MenuOption(label='Expand all directories', action='expand_all', recursive=True)
        ],
        'Workspace Management': {
            'Traverse to a new directory': [
                MenuOption(label='Only list directories', action='list_dirs', filter_dirs=True),
                MenuOption(label='Changes the cwd', action='change_cwd')
            ],
            'Add files': [
                MenuOption(label='Show files in cwd', action='list_files', filter_files=True),
                MenuOption(label='Show directories in cwd', action='list_dirs', filter_dirs=True)
            ],
            'Remove files': [
                MenuOption(label='Show files in workspace', action='workspace_files', filter_files=True),
                MenuOption(label='Show directories in workspace', action='workspace_dirs', filter_dirs=True)
            ]
        },
        'Clipboard Management': {
            'Add to workspace paths to clipboard queue': [
                MenuOption(label='List files in workspace', action='workspace_files', filter_files=True),
                MenuOption(label='List directories in workspace', action='workspace_dirs', filter_dirs=True)
            ],
            'Add cwd paths to clipboard queue': [
                MenuOption(label='List files in cwd', action='cwd_files', filter_files=True),
                MenuOption(label='List directories in cwd', action='cwd_dirs', filter_dirs=True)
            ],
            'Remove from clipboard queue': [
                MenuOption(label='List files in clipboard queue', action='clipboard_files', filter_files=True),
                MenuOption(label='List directories in clipboard queue', action='clipboard_dirs', filter_dirs=True)
            ]
        }
    }
}
