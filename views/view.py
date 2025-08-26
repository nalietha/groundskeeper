# groundskeeper/views/view.py
import tkinter as tk
from tkinter import font as tkfont

from views.standby import StandbyView
from views.mainmenu import MainMenuView
from views.affirmation import AffirmationView
from views.joke import JokeView
from views.update import UpdateView
from views.settings import SettingsView
from views.games import GamesView
# Remove the old screen.py import and bases.py if you created it

class View:
    def __init__(self, root, callbacks, config, control_service, extra_screens=None):
        self.root = root
        self.callbacks = callbacks
        self.config = config
        self.control_service = control_service
        self.root.title("Groundskeeper")
        self.root.geometry(f"{config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}")
        scale_factor = config.SCREEN_WIDTH / config.BASE_WIDTH

        available_fonts = tkfont.families()
        font_family = "Press Start 2P" if "Press Start 2P" in available_fonts else "Courier"

        self.fonts = {
            name: (font_family, int(size * scale_factor), style)
            for name, size, style in [
                ("title", config.FONT_SIZES["title"], "bold"),
                ("subtitle", config.FONT_SIZES["subtitle"], "bold"),
                ("body", config.FONT_SIZES["body"], "italic"),
                ("small", config.FONT_SIZES["small"], ""),
                ("button", config.FONT_SIZES["button"], ""),
            ]
        }
        
        # --- Main Container Setup ---
        self.container = tk.Frame(root)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        # ---------------------------

        self.screens = {}
        all_screens = [StandbyView, MainMenuView, AffirmationView, JokeView, UpdateView, SettingsView, GamesView]
        if extra_screens: all_screens.extend(extra_screens)

        for F in all_screens:
            screen_name = F.__name__
            # Pass the container as the parent to each screen
            frame = F(self.container, callbacks, self.fonts, config)
            self.screens[screen_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

    def show_screen(self, screen_name):
        screen = self.screens[screen_name]
        screen.tkraise()
        # self.control_service.activate_ui_controls(screen) # We'll re-enable this later if needed

    def set_theme_colors(self, bg_color, fg_color):
        self.root.configure(bg=bg_color)
        for screen in self.screens.values():
            self._apply_theme_recursive(screen, bg_color, fg_color)

    def _apply_theme_recursive(self, widget, bg, fg):
        try:
            widget.configure(bg=bg, highlightbackground=bg)
            if isinstance(widget, (tk.Label, tk.Button, tk.LabelFrame)):
                widget.configure(fg=fg)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._apply_theme_recursive(child, bg, fg)