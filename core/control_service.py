# groundskeeper/core/control_service.py
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
        
        self.add_binding("<Up>", self.navigate_up)
        self.add_binding("<Down>", self.navigate_down)
        self.add_binding("<Left>", self.navigate_left)
        self.add_binding("<Right>", self.navigate_right)
        self.add_binding("<Return>", self.invoke_widget)
        self.add_binding("<BackSpace>", self.go_back)
        
        print(f"UI controls ACTIVATED for {screen.__class__.__name__}")

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

    def navigate_left(self, event):
        if not self.ui_context_active or not self.active_screen: return "break"
        
        if self.active_screen.__class__.__name__ == 'NameEntryView':
            self.active_screen.move_cursor(-1)
        elif hasattr(self.active_screen, 'carousel'):
            self.active_screen.carousel.go_previous()
        elif hasattr(self.active_screen, 'navigate'):
            self.active_screen.navigate(-1)
        return "break"

    def navigate_right(self, event):
        if not self.ui_context_active or not self.active_screen: return "break"

        if self.active_screen.__class__.__name__ == 'NameEntryView':
            self.active_screen.move_cursor(1)
        elif hasattr(self.active_screen, 'carousel'):
            self.active_screen.carousel.go_next()
        elif hasattr(self.active_screen, 'navigate'):
            self.active_screen.navigate(1)
        return "break"
        
    def navigate_up(self, event):
        if not self.ui_context_active or not self.active_screen: return "break"

        if self.active_screen.__class__.__name__ == 'NameEntryView':
            self.active_screen.change_char(1) # Go up the character list
        elif hasattr(self.active_screen, 'navigate') and not hasattr(self.active_screen, 'carousel'):
            self.active_screen.navigate(-1)
        return "break"

    def navigate_down(self, event):
        if not self.ui_context_active or not self.active_screen: return "break"

        if self.active_screen.__class__.__name__ == 'NameEntryView':
            self.active_screen.change_char(-1) # Go down the character list
        elif hasattr(self.active_screen, 'navigate') and not hasattr(self.active_screen, 'carousel'):
            self.active_screen.navigate(1)
        return "break"
        
    def invoke_widget(self, event):
        if not self.ui_context_active or not self.active_screen: return "break"

        if self.active_screen.__class__.__name__ == 'NameEntryView':
            self.active_screen.advance_or_submit()
        elif hasattr(self.active_screen, 'carousel'):
            callback = self.active_screen.carousel.get_current_callback()
            if callback: callback()
        elif hasattr(self.active_screen, 'invoke_widget'):
            self.active_screen.invoke_widget()
            
        return "break"

    def go_back(self, event):
        if self.ui_context_active and hasattr(self.active_screen, 'go_back'):
            self.active_screen.go_back()
        return "break"