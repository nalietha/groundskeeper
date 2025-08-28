# groundskeeper/views/mainmenu.py
import tkinter as tk
from .bases import MenuScreen
from .carousel import Carousel

class MainMenuView(MenuScreen):
    def setup_ui(self):
        # title_label = tk.Label(self.content_frame, text="Main Menu", font=self.fonts["title"])
        # title_label.pack(pady=20)
        
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
        
        self.carousel = Carousel(self.content_frame, menu_items, self.fonts, self.config)
        self.carousel.pack(expand=True, fill="both")

        # Carousel screens don't have navigable widgets in the traditional sense
        self.navigable_widgets = []
 
    def go_back(self):
        # FIX: Explicitly define the back action for the main menu
        if 'show_standby' in self.callbacks:
            self.callbacks['show_standby']()