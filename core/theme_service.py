# groundskeeper/core/theme_service.py
import os
import json
from models.theme import Theme

class ThemeService:
    def __init__(self, themes_dir="themes"):
        self.themes = {}
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        abs_themes_dir = os.path.join(project_root, themes_dir)

        if not os.path.isdir(abs_themes_dir):
            print(f"Error: Themes directory '{abs_themes_dir}' not found.")
            return
        
        for theme_name in os.listdir(abs_themes_dir):
            theme_path = os.path.join(abs_themes_dir, theme_name)
            settings_file = os.path.join(theme_path, "settings.json")
            if os.path.isdir(theme_path) and os.path.isfile(settings_file):
                try:
                    with open(settings_file, 'r', encoding='utf-8') as f:
                        theme_data = json.load(f)
                        theme = Theme(theme_data)
                        
                        self._load_standard_assets(theme, theme_path)
                        self._load_sayings_for_theme(theme, theme_path)
                        self._load_jokes_for_theme(theme, theme_path)
                        self.themes[theme.name] = theme

                except json.JSONDecodeError:
                    print(f"Warning: Could not parse settings for theme '{theme_name}'.")
        print(f"Discovered and loaded {len(self.themes)} themes.")

    def _load_standard_assets(self, theme, theme_path):
        """Finds and attaches standardized asset paths and data to the theme object."""
        assets_path = os.path.join(theme_path, "assets")
        
        # Icon, Theme Card, Loading Images... (this part is correct)
        icon_path = os.path.join(assets_path, "icon.png")
        if os.path.exists(icon_path): theme.icon = icon_path
        card_path = os.path.join(assets_path, "theme_card.png")
        if os.path.exists(card_path): theme.theme_card = card_path
        loading_path = os.path.join(assets_path, "loading")
        if os.path.isdir(loading_path):
            theme.loading_images = sorted([
                os.path.join(loading_path, f) for f in os.listdir(loading_path)
                if f.lower().endswith(('.png', '.jpg', '.jpeg'))
            ])
            
        # Game Styles
        game_styles_path = os.path.join(assets_path, "styled_games.json")
        if os.path.exists(game_styles_path):
            try:
                with open(game_styles_path, 'r', encoding='utf-8') as f:
                    styles_data = json.load(f)
                    # --- FIX: Correctly resolve relative paths ---
                    for game, assets in styles_data.items():
                        for key, value in assets.items():
                            if isinstance(value, str) and value.lower().endswith('.png'):
                                # Create the full, absolute path by joining the theme's assets dir with the relative path
                                full_path = os.path.join(assets_path, value)
                                styles_data[game][key] = os.path.normpath(full_path)
                    theme.game_styles = styles_data
                    # ---------------------------------------------
            except json.JSONDecodeError:
                print(f"Warning: Could not parse styled_games.json for theme '{theme.name}'.")

    def _load_sayings_for_theme(self, theme, theme_path):
        sayings_filename = f"list_{theme.name.lower()}.json"
        sayings_path = os.path.join(theme_path, sayings_filename)
        try:
            with open(sayings_path, 'r', encoding='utf-8') as f:
                theme.sayings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass # It's okay if a theme doesn't have sayings

    def _load_jokes_for_theme(self, theme, theme_path):
        jokes_filename = f"jokes_{theme.name.lower()}.json"
        jokes_path = os.path.join(theme_path, jokes_filename)
        try:
            with open(jokes_path, 'r', encoding='utf-8') as f:
                theme.jokes = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass # It's okay if a theme doesn't have jokes

    def get_theme(self, name): return self.themes.get(name)
    def get_all_themes(self): return list(self.themes.values())