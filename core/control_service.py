# groundskeeper/core/control_service.py
class ControlService:
    def __init__(self, app):
        """
        Initializes the service with a reference to the main application instance.
        """
        self.app = app
        self.root = app.root
        self.active_bindings = {}
        self.global_bindings = {}
        self.active_screen = None
        self.ui_context_active = False

        # --- Secret Code Logic ---
        self.input_sequence = []
        # The Konami Code, mapped to our GPIO/keyboard inputs
        # Up, Up, Down, Down, Left, Right, Left, Right, B, A
        self.konami_code = ['up', 'up', 'down', 'down', 'left', 'right', 'left', 'right', 'b', 'a']
        # -------------------------
        self._setup_global_controls()

    def _setup_global_controls(self):
        """Binds keys that should work on any screen and are never deactivated."""
        self.add_global_binding("<space>", self.handle_coin_press)
        self.add_global_binding("r", self.handle_brew_press)

    def add_global_binding(self, event, callback):
        """Adds a binding that is not cleared on screen change."""
        binding_id = self.root.bind(event, callback)
        self.global_bindings[event] = binding_id

    def handle_coin_press(self, event):
        """Callback for the global coin/games button."""
        print("Coin button pressed!")
        self.app.show_games() # Call the existing show_games method
        return "break"

    def handle_brew_press(self, event):
        """Callback for the global brew button (resets current theme timer)."""
        print("Brew button pressed!")
        # Automatically confirm and start the item for the currently active theme
        self.app.confirm_and_start_item(self.app.active_theme_name)
        return "break"
    
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
        # --- Add bindings for the 'A' and 'B' action buttons ---
        self.add_binding("<KeyPress-a>", self.handle_action_a)
        self.add_binding("<KeyPress-b>", self.handle_action_b)
        
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

    def _record_key(self, key_name):
        """Records a key press and checks if it completes a secret code."""
        self.input_sequence.append(key_name)
        # Keep the sequence list the same size as the code we're checking for
        if len(self.input_sequence) > len(self.konami_code):
            self.input_sequence.pop(0)

        if self.input_sequence == self.konami_code:
            print("Konami Code Entered!")
            self.app.toggle_turbo_mode() # Trigger the action in the main app
            self.input_sequence = [] # Reset the sequence

    # --- Update navigation methods to record key presses ---
    def navigate_up(self, event):
        self._record_key('up')
        if not self.ui_context_active or not self.active_screen: return "break"
        if self.active_screen.__class__.__name__ == 'NameEntryView':
            self.active_screen.change_char(1)
        elif hasattr(self.active_screen, 'navigate') and not hasattr(self.active_screen, 'carousel'):
            self.active_screen.navigate(-1)
        return "break"

    def navigate_down(self, event):
        self._record_key('down')
        if not self.ui_context_active or not self.active_screen: return "break"
        if self.active_screen.__class__.__name__ == 'NameEntryView':
            self.active_screen.change_char(-1)
        elif hasattr(self.active_screen, 'navigate') and not hasattr(self.active_screen, 'carousel'):
            self.active_screen.navigate(1)
        return "break"

    def navigate_left(self, event):
        self._record_key('left')
        if not self.ui_context_active or not self.active_screen: return "break"
        if self.active_screen.__class__.__name__ == 'NameEntryView':
            self.active_screen.move_cursor(-1)
        elif hasattr(self.active_screen, 'carousel'):
            self.active_screen.carousel.go_previous()
        elif hasattr(self.active_screen, 'navigate'):
            self.active_screen.navigate(-1)
        return "break"

    def navigate_right(self, event):
        self._record_key('right')
        if not self.ui_context_active or not self.active_screen: return "break"
        if self.active_screen.__class__.__name__ == 'NameEntryView':
            self.active_screen.move_cursor(1)
        elif hasattr(self.active_screen, 'carousel'):
            self.active_screen.carousel.go_next()
        elif hasattr(self.active_screen, 'navigate'):
            self.active_screen.navigate(1)
        return "break"

    # --- New handlers for A and B buttons ---
    def handle_action_a(self, event):
        self._record_key('a')
        self.invoke_widget(event) # Also perform the normal action
        return "break"

    def handle_action_b(self, event):
        self._record_key('b')
        self.go_back(event) # Also perform the normal action
        return "break"

    def invoke_widget(self, event):
        # This function is now called by handle_action_a, so we don't record the key here
        if not self.ui_context_active or not self.active_screen: return "break"
        
        if self.active_screen.__class__.__name__ == 'TitleView':
            self.app.show_main_menu()
        elif self.active_screen.__class__.__name__ == 'NameEntryView':
            self.active_screen.advance_or_submit()
        elif hasattr(self.active_screen, 'carousel'):
            callback = self.active_screen.carousel.get_current_callback()
            if callback: callback()
        elif hasattr(self.active_screen, 'invoke_widget'):
            self.active_screen.invoke_widget()
        return "break"

    def go_back(self, event):
        # This function is now called by handle_action_b, so we don't record the key here
        if self.ui_context_active and hasattr(self.active_screen, 'go_back'):
            self.active_screen.go_back()
        return "break"