# groundskeeper/core/theme_service.py
import os
import json
from pathlib import Path # Use pathlib for robust path handling
from models.theme import Theme


class ThemeService:
    def __init__(self, themes_dir="themes"):
        self.themes = {}
        project_root = Path(__file__).parent.parent # Navigate up from core/ to groundskeeper/
        abs_themes_dir = project_root / themes_dir

        if not abs_themes_dir.is_dir():
            print(f"Error: Themes directory '{abs_themes_dir}' not found.")
            return
        
        for theme_dir in abs_themes_dir.iterdir():
            settings_file = theme_dir / "settings.json"
            if theme_dir.is_dir() and settings_file.is_file():
                try:
                    with open(settings_file, 'r', encoding='utf-8') as f:
                        theme_data = json.load(f)
                        
                        if not theme_data.get("active", False):
                            continue
                        
                        theme = Theme(theme_data)
                        
                        self._load_standard_assets(theme, theme_dir)
                        self._load_sayings_for_theme(theme, theme_dir)
                        self._load_jokes_for_theme(theme, theme_dir)
                        self.themes[theme.name] = theme

                except json.JSONDecodeError:
                    print(f"Warning: Could not parse settings for theme '{theme_dir.name}'.")
        print(f"Discovered and loaded {len(self.themes)} active themes.")

    def _load_standard_assets(self, theme, theme_path):
        """Finds and attaches standardized asset paths and data to the theme object."""
        assets_path = theme_path / "assets"
        
        icon_path = assets_path / "icon.png"
        if icon_path.exists(): theme.icon = str(icon_path)
        
        card_path = assets_path / "theme_card.png"
        if card_path.exists(): theme.theme_card = str(card_path)
        
        standby_bg_path = assets_path / "standby_bg.png"
        if standby_bg_path.exists(): theme.standby_bg = str(standby_bg_path)

        symbol_path = assets_path / "symbol.png"
        if symbol_path.exists(): theme.symbol = str(symbol_path)

        loading_path = assets_path / "loading"
        if loading_path.is_dir():
            theme.loading_images = sorted([
                str(f) for f in loading_path.iterdir()
                if f.suffix.lower() in ['.png', '.jpg', '.jpeg']
            ])
            
        game_styles_path = assets_path / "styled_games.json"
        if game_styles_path.exists():
            try:
                with open(game_styles_path, 'r', encoding='utf-8') as f:
                    styles_data = json.load(f)
                    for game, assets in styles_data.items():
                        for key, value in assets.items():
                            if isinstance(value, str) and Path(value).suffix.lower() in ['.png', '.jpg', '.jpeg']:
                                # Resolve the path relative to the theme's assets directory
                                full_path = assets_path / value
                                styles_data[game][key] = str(full_path)
                    theme.game_styles = styles_data
            except json.JSONDecodeError:
                print(f"Warning: Could not parse styled_games.json for theme '{theme.name}'.")

    def _load_sayings_for_theme(self, theme, theme_path):
        sayings_filename = f"list_{theme.name.lower()}.json"
        sayings_path = theme_path / sayings_filename
        try:
            with open(sayings_path, 'r', encoding='utf-8') as f:
                theme.sayings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass 

    def _load_jokes_for_theme(self, theme, theme_path):
        jokes_filename = f"jokes_{theme.name.lower()}.json"
        jokes_path = theme_path / jokes_filename
        try:
            with open(jokes_path, 'r', encoding='utf-8') as f:
                theme.jokes = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def get_theme(self, name): return self.themes.get(name)
    def get_all_themes(self): return list(self.themes.values())