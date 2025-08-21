import tkinter as tk

from views.standby import StandbyView
from views.mainmenu import MainMenuView

class View:
    def __init__(self, root, callbacks, config):
        self.root, self.callbacks, self.config = root, callbacks, config
        self.root.title("Standby Screen Demo")
        self.root.geometry(f"{config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}")
        
        # --- Dynamic Font Scaling ---
        scale_factor = config.SCREEN_WIDTH / config.BASE_WIDTH
        self.fonts = {
            name: ("Helvetica", int(size * scale_factor), style)
            for name, size, style in [
                ("title", config.FONT_SIZES["title"], "bold"),
                ("subtitle", config.FONT_SIZES["subtitle"], "bold"),
                ("body", config.FONT_SIZES["body"], "italic"),
                ("small", config.FONT_SIZES["small"], ""),
                ("button", config.FONT_SIZES["button"], ""),
            ]
        }
        
        self.container = tk.Frame(root)
        self.container.pack(expand=True, fill="both")
        self.screens = {}
        for F in (StandbyView, MainMenuView):
            screen_name = F.__name__
            frame = F(self.container, callbacks, self.fonts) # Pass fonts to screens
            self.screens[screen_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

    def show_screen(self, screen_name): self.screens[screen_name].tkraise()
    def set_theme_colors(self, bg_color, fg_color):
        self.root.configure(bg=bg_color)
        for screen in self.screens.values():
            self._apply_theme_recursive(screen, bg_color, fg_color)
    def _apply_theme_recursive(self, widget, bg, fg):
        try:
            widget.configure(bg=bg)
            if not isinstance(widget, (tk.Frame, tk.LabelFrame)): widget.configure(fg=fg)
        except tk.TclError: pass
        for child in widget.winfo_children():
            self._apply_theme_recursive(child, bg, fg)
