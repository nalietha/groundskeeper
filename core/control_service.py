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
        self.app.callbacks['show_games']()
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
        self.add_binding("<Return>", self.select)
        self.add_binding("<BackSpace>", self.back)
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

    # --- Navigation methods: record the key, then forward the intent to the
    #     active screen. Screens decide what each intent means (see BaseScreen),
    #     so adding a screen never requires editing this service. ---
    def _dispatch(self, intent):
        """Forwards an input intent (e.g. 'on_up') to the active screen."""
        if not self.ui_context_active or not self.active_screen:
            return
        handler = getattr(self.active_screen, intent, None)
        if callable(handler):
            handler()

    def navigate_up(self, event):
        self._record_key('up')
        self._dispatch('on_up')
        return "break"

    def navigate_down(self, event):
        self._record_key('down')
        self._dispatch('on_down')
        return "break"

    def navigate_left(self, event):
        self._record_key('left')
        self._dispatch('on_left')
        return "break"

    def navigate_right(self, event):
        self._record_key('right')
        self._dispatch('on_right')
        return "break"

    # --- Select / Back, shared by <Return>/<BackSpace> and the A/B buttons ---
    def select(self, event=None):
        self._dispatch('on_select')
        return "break"

    def back(self, event=None):
        self._dispatch('on_back')
        return "break"

    def handle_action_a(self, event):
        self._record_key('a')
        self.select() # Also perform the normal action
        return "break"

    def handle_action_b(self, event):
        self._record_key('b')
        self.back() # Also perform the normal action
        return "break"