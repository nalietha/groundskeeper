# groundskeeper/views/view.py
import tkinter as tk
from tkinter import font as tkfont

from views.affirmation import AffirmationView
from views.joke import JokeView
from views.update import UpdateView
from views.settings import SettingsView
from views.games import GamesView
from views.loading import LoadingView
from views.extras import ExtrasView
from views.leaderboard import LeaderboardView
from views.name_entry import NameEntryView
from views.splash import SplashView
from views.title import TitleView
from views.statusbar import StatusBar
from views.mainmenu import MainMenuView
from views.standby import StandbyView

class View:
    def __init__(self, root, callbacks, config, control_service, extra_screens=None):
        self.root = root
        self.callbacks = callbacks
        self.config = config
        self.control_service = control_service
        self.root.title("Groundskeeper")
        self.root.geometry(f"{config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}")
        scale_factor = config.SCREEN_WIDTH / config.BASE_WIDTH

        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.status_bar = StatusBar(root, config)
        self.status_bar.grid(row=0, column=0, sticky="ew")

        self.container = tk.Frame(root, borderwidth=0, highlightthickness=0)
        self.container.grid(row=1, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

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
        
        self.screens = {}
        all_screens = [
            SplashView, TitleView, StandbyView, MainMenuView, AffirmationView, 
            JokeView, UpdateView, SettingsView, GamesView, ExtrasView, 
            LoadingView, LeaderboardView, NameEntryView
        ]
        if extra_screens: all_screens.extend(extra_screens)

        for F in all_screens:
            screen_name = F.__name__
            frame = F(self.container, callbacks, self.fonts, config)
            self.screens[screen_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

    def show_screen(self, screen_name):
        screen = self.screens[screen_name]
        screen.tkraise()
        self.control_service.activate_ui_controls(screen) 

    def set_theme_colors(self, bg_color, fg_color):
        self.root.configure(bg=bg_color)
        self._apply_theme_recursive(self.status_bar, bg_color, fg_color)
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
    
    def update_score(self, score):
        """Passes the score to the status bar."""
        self.status_bar.update_score(score)
        self.root.update() # Force UI to refresh

    def set_score_visibility(self, is_visible):
        """Passes the visibility command to the status bar."""
        self.status_bar.set_score_visibility(is_visible)