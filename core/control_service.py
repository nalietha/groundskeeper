class ControlService:
    def __init__(self, root):
        self.root = root
        self.active_bindings = {}
        self.active_screen = None
        self.ui_context_active = False

    def activate_ui_controls(self, screen):
        self.deactivate_all_controls()
        self.active_screen = screen
        self.ui_context_active = True
        
        # Define UI navigation bindings
        self.add_binding("<Up>", self.navigate_up)
        self.add_binding("<Down>", self.navigate_down)
        self.add_binding("<Return>", self.invoke_widget)
        self.add_binding("<BackSpace>", self.go_back)
        
        print("UI controls ACTIVATED")

    def deactivate_all_controls(self):
        for event, binding_id in self.active_bindings.items():
            self.root.unbind(event, binding_id)
        self.active_bindings = {}
        self.active_screen = None
        self.ui_context_active = False
        print("All controls DEACTIVATED")

    def add_binding(self, event, callback):
        binding_id = self.root.bind(event, callback)
        self.active_bindings[event] = binding_id

    def navigate_up(self, event):
        if self.ui_context_active and self.active_screen:
            self.active_screen.navigate(-1)
        return "break"

    def navigate_down(self, event):
        if self.ui_context_active and self.active_screen:
            self.active_screen.navigate(1)
        return "break"
        
    def invoke_widget(self, event):
        if self.ui_context_active and self.active_screen:
            self.active_screen.invoke_widget()
        return "break"

    def go_back(self, event):
        if self.ui_context_active and self.active_screen:
            self.active_screen.go_back()
        return "break"