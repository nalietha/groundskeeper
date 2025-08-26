# groundskeeper/views/mainmenu.py
import tkinter as tk
from .bases import SingleButtonScreen

class MainMenuView(SingleButtonScreen):
    def setup_ui(self):
        menu_label = tk.Label(self.content_frame, text="Main Menu", font=self.fonts["title"])
        menu_label.pack(pady=(10, 5))
        
        theme_frame = tk.LabelFrame(self.content_frame, text="Select Item to View", font=self.fonts["small"], pady=5)
        theme_frame.pack(pady=5, fill="x", expand=True)
        
        all_themes = self.callbacks['get_all_themes']()
        theme_buttons = []
        for theme in all_themes:
            btn = tk.Button(theme_frame, text=theme.name, font=self.fonts["small"], command=lambda t=theme.name: self.callbacks['set_active_theme'](t))
            btn.pack(side="top", expand=True, fill="x", pady=2)
            theme_buttons.append(btn)
            
        # --- Simplified Menu Buttons ---
        menu_button_frame = tk.Frame(self.content_frame)
        menu_button_frame.pack(expand=True, fill="x", pady=5)
        menu_button_frame.columnconfigure(0, weight=1)

        extras_button = tk.Button(menu_button_frame, text="Extras & Fun", font=self.fonts["body"], command=self.callbacks['show_extras'])
        extras_button.pack(fill="x", pady=5, padx=10)

        settings_button = tk.Button(menu_button_frame, text="Settings", font=self.fonts["body"], command=self.callbacks['show_settings'])
        settings_button.pack(fill="x", pady=5, padx=10)
        # --------------------------------

        menu_buttons = [extras_button, settings_button]
            
        self.navigable_widgets = theme_buttons + menu_buttons + self.navigable_widgets
        self.setup_navigation()

    def go_back(self):
        # Override the default "go_back" to go to the standby screen
        if 'show_standby' in self.callbacks:
            self.callbacks['show_standby']()