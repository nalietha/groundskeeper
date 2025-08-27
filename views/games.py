# groundskeeper/views/games.py
import tkinter as tk
from .bases import GameMenuScreen
from .carousel import Carousel

class GamesView(GameMenuScreen):
    def setup_ui(self):
        title_label = tk.Label(self.content_frame, text="Select Game", font=self.fonts["title"])
        title_label.pack(pady=20)

        available_games = self.callbacks['get_available_games']()
        game_items = []
        # Use .items() to get both the key (game_name) and the value (game_data)
        for game_name, game_data in available_games.items():
            game_items.append({
                'text': game_data['name'],
                'image_path': game_data['card_path'],
                'key': game_name, 
                'callback': lambda g=game_name: self.callbacks['start_game'](g)
            })

        if not game_items:
            no_games_label = tk.Label(self.content_frame, text="No Games Found!", font=self.fonts["body"])
            no_games_label.pack(expand=True)
        else:
            self.carousel = Carousel(self.content_frame, game_items, self.fonts, self.config)
            self.carousel.pack(expand=True, fill="both")

        # The buttons are in the base class. The carousel handles navigation.
        self.navigable_widgets = []

    def go_back(self):
        # This screen should go back to the "Extras" menu
        if 'show_extras' in self.callbacks:
            self.callbacks['show_extras']()