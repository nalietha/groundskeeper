# groundskeeper/views/bases.py
import tkinter as tk

class BaseScreen(tk.Frame):
    """A minimal base class that handles shared functionality but no layout."""
    def __init__(self, parent, callbacks, fonts, config, **kwargs):
        super().__init__(parent, borderwidth=0, highlightthickness=0)
        self.callbacks = callbacks
        self.fonts = fonts
        self.config = config
        self.navigable_widgets = []
        self.current_focus_index = 0

    def setup_ui(self):
        raise NotImplementedError

    def setup_navigation(self):
        for widget in self.navigable_widgets:
            widget.configure(takefocus=1, highlightthickness=2, highlightcolor="yellow", highlightbackground=widget.cget('bg'))
        if self.navigable_widgets:
            self.navigable_widgets[0].focus_set()

    def tkraise(self, aboveThis=None):
        super().tkraise(aboveThis)
        if self.navigable_widgets:
            self.navigable_widgets[self.current_focus_index].focus_set()

    def navigate(self, direction):
        if not self.navigable_widgets: return
        self.current_focus_index = (self.current_focus_index + direction) % len(self.navigable_widgets)
        new_widget = self.navigable_widgets[self.current_focus_index]
        new_widget.focus_set()

    def invoke_widget(self):
        if self.navigable_widgets:
            focused_widget = self.focus_get()
            if focused_widget in self.navigable_widgets:
                focused_widget.invoke()

    def go_back(self):
        if 'show_main_menu' in self.callbacks:
            self.callbacks['show_main_menu']()

class TwoButtonScreen(BaseScreen):
    """The base for the StandbyView, which has a centered content area and two buttons."""
    def __init__(self, parent, callbacks, fonts, config, **kwargs):
        super().__init__(parent, callbacks, fonts, config, **kwargs)
        self.grid_rowconfigure(0, weight=1)    # Top spacer
        self.grid_rowconfigure(1, weight=0)    # Content
        self.grid_rowconfigure(2, weight=1)    # Bottom spacer
        self.grid_rowconfigure(3, weight=0)    # Buttons
        self.grid_columnconfigure(0, weight=1)

        self.content_frame = tk.Frame(self, borderwidth=0, highlightthickness=0)
        self.content_frame.grid(row=1, column=0)

        button_frame = tk.Frame(self, borderwidth=0, highlightthickness=0)
        button_frame.grid(row=3, column=0, sticky="ew")
        button_frame.columnconfigure((0, 1), weight=1)

        self.menu_button = tk.Button(button_frame, text="Menu", font=self.fonts["button"], command=self.callbacks['show_main_menu'])
        self.menu_button.grid(row=0, column=0, sticky="ew", pady=5, padx=5)
        
        self.action_button = tk.Button(button_frame, text="Action", font=self.fonts["button"])
        self.action_button.grid(row=0, column=1, sticky="ew", pady=5, padx=5)

        self.navigable_widgets = [self.menu_button, self.action_button]
        self.setup_ui()

class MenuScreen(BaseScreen):
    """
    The NEW base for any screen that is a list of buttons (MainMenu, Extras, Settings, Games).
    The content area expands, and the single 'Back' button is always visible at the bottom.
    """
    def __init__(self, parent, callbacks, fonts, config, **kwargs):
        super().__init__(parent, callbacks, fonts, config, **kwargs)
        self.grid_rowconfigure(0, weight=1) # Let the content row expand
        self.grid_rowconfigure(1, weight=0) # Keep the button row fixed
        self.grid_columnconfigure(0, weight=1)

        self.content_frame = tk.Frame(self, borderwidth=0, highlightthickness=0)
        self.content_frame.grid(row=0, column=0, sticky="nsew")

        button_frame = tk.Frame(self, borderwidth=0, highlightthickness=0)
        button_frame.grid(row=1, column=0, sticky="ew")
        button_frame.columnconfigure(0, weight=1)

        back_button = tk.Button(button_frame, text="Back", font=self.fonts["button"], command=self.go_back)
        back_button.grid(row=0, column=0, sticky="ew", pady=5)
        
        self.navigable_widgets = [back_button]
        self.setup_ui()

class GameMenuScreen(BaseScreen):
    """A base for the game selection screen with a carousel and two bottom buttons."""
    def __init__(self, parent, callbacks, fonts, config, **kwargs):
        super().__init__(parent, callbacks, fonts, config, **kwargs)
        self.grid_rowconfigure(0, weight=1) # Carousel content
        self.grid_rowconfigure(1, weight=0) # Buttons
        self.grid_columnconfigure(0, weight=1)

        self.content_frame = tk.Frame(self, borderwidth=0, highlightthickness=0)
        self.content_frame.grid(row=0, column=0, sticky="nsew")

        button_frame = tk.Frame(self, borderwidth=0, highlightthickness=0)
        button_frame.grid(row=1, column=0, sticky="ew")
        button_frame.columnconfigure((0, 1), weight=1)

        back_button = tk.Button(
            button_frame, 
            text="BACK", 
            font=self.fonts["button"], 
            command=self.go_back,
            bg="#2d1b11",              # Dark bronze resting state
            fg="#d4a373",              # Brass text
            activebackground="#1a0f0a", # Very dark when pushed
            activeforeground="#e07a5f", # Text glows copper when pushed
            bd=5,                      # Thick 3D border
            relief=tk.RAISED           # Pops out from the screen
        )
        back_button.grid(row=0, column=0, sticky="ew", pady=5, padx=5)

        leaderboard_button = tk.Button(button_frame, text="Leaderboard", font=self.fonts["button"], command=self.callbacks['show_leaderboard'])
        leaderboard_button.grid(row=0, column=1, sticky="ew", pady=5, padx=5)

        self.navigable_widgets = [back_button, leaderboard_button]
        self.setup_ui()