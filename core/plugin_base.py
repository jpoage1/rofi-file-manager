class WorkspacePlugin:
    priority = None
    def __init__(self, menu, state):
        self.menu = menu
        self.state = state

    def _build_options(self):
        pass
