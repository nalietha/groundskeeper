import pygame
import os
from games.snake import SnakeGame

class GameService:
    def __init__(self, config):
        self.config = config

    def load_theme_assets(self, theme):
        assets = {}
        theme_path = os.path.join('themes', theme.name.lower())
        asset_path = os.path.join(theme_path, 'assets')
        
        # Load food asset
        food_image_path = os.path.join(asset_path, 'food.png')
        if os.path.exists(food_image_path):
            assets['food'] = pygame.image.load(food_image_path)
            
        # Load theme-specific colors, if any
        # This part is a placeholder for future color customization
        # assets['colors'] = { "snake": (r,g,b), ... }

        return assets

    def start_snake(self, theme):
        print(f"Starting Snake with {theme.name} theme...")
        theme_assets = self.load_theme_assets(theme)
        game = SnakeGame(self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT, theme_assets)
        game.game_loop()