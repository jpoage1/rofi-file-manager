class MenuApp:
    def __init__(self):
        self.state_stack = []
        self.current_state = MenuState()

    def push_state(self):
        self.state_stack.append(copy.deepcopy(self.current_state))

    def pop_state(self):
        self.current_state = self.state_stack.pop()
