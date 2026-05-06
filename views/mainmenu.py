# groundskeeper/views/mainmenu.py
import tkinter as tk
from .bases import MenuScreen
from .carousel import Carousel

class MainMenuView(MenuScreen):
    def setup_ui(self):
        # 1. Brass Plaque Title
        plaque_border = tk.Frame(self.content_frame, bg="#5a3a22", bd=4, relief=tk.RIDGE)
        plaque_border.pack(pady=(15, 10), padx=20, fill="x")

        title_label = tk.Label(
            plaque_border, 
            text="- SYSTEM SELECT -", 
            font=self.fonts["title"],
            bg="#2d1b11",  # Dark boiler brown
            fg="#d4a373",  # Light brass text
            bd=3,
            relief=tk.SUNKEN,
            pady=5
        )
        title_label.pack(fill="x", padx=3, pady=3)
        
        # 2. Boiler Viewport for the Carousel
        # The outer frame acts as the thick pipe/bronze casing
        viewport_border = tk.Frame(self.content_frame, bg="#5a3a22", bd=6, relief=tk.RIDGE)
        viewport_border.pack(expand=True, fill="both", padx=15, pady=(0, 15))
        
        # The inner frame acts as the dark, recessed inside of the machine
        viewport_inner = tk.Frame(viewport_border, bg="#1a0f0a", bd=4, relief=tk.SUNKEN)
        viewport_inner.pack(expand=True, fill="both")

        all_themes = self.callbacks['get_all_themes']()
        menu_items = []

        for theme in all_themes:
            if theme.theme_card:
                menu_items.append({
                    'text': theme.name,
                    'image_path': theme.theme_card,
                    'callback': lambda t=theme.name: self.callbacks['set_active_theme'](t)
                })

        menu_items.extend([
            {'text': 'Extras & Fun', 'image_path': 'assets/icons/extras.png', 'callback': self.callbacks['show_extras']},
            {'text': 'Settings', 'image_path': 'assets/icons/settings.png', 'callback': self.callbacks['show_settings']},
        ])
        
        self.carousel = Carousel(viewport_inner, menu_items, self.fonts, self.config)
        self.carousel.pack(expand=True, fill="both", padx=2, pady=2)

        # Force the carousel to match the dark inside of the viewport
        self.carousel.configure(bg="#1a0f0a")
        self.carousel.canvas.configure(bg="#1a0f0a")
        self.carousel.label.configure(bg="#1a0f0a", fg="#e07a5f") # Copper glowing text

        self.navigable_widgets = []
 
    def go_back(self):
        if 'show_standby' in self.callbacks:
            self.callbacks['show_standby']()