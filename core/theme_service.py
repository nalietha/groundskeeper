import os
import json

from models.theme import Theme

class ThemeService:
    def __init__(self, themes_dir="themes"):
        self.themes = {}
        if not os.path.isdir(themes_dir):
            print(f"Error: Themes directory '{themes_dir}' not found.")
            return
        for theme_name in os.listdir(themes_dir):
            theme_path = os.path.join(themes_dir, theme_name)
            settings_file = os.path.join(theme_path, "settings.json")
            if os.path.isdir(theme_path) and os.path.isfile(settings_file):
                try:
                    with open(settings_file, 'r', encoding='utf-8') as f:
                        theme_data = json.load(f)
                        theme = Theme(theme_data)
                        self._load_sayings_for_theme(theme, theme_path)
                        self._load_jokes_for_theme(theme, theme_path)
                        self.themes[theme.name] = theme
                except json.JSONDecodeError:
                    print(f"Warning: Could not parse settings for theme '{theme_name}'.")
        print(f"Discovered and loaded {len(self.themes)} themes.")

    def _load_sayings_for_theme(self, theme, theme_path):
        """Loads all mood sayings for a theme from a single file named after the theme."""
        sayings_filename = f"list_{theme.name.lower()}.json"
        sayings_path = os.path.join(theme_path, sayings_filename)

        try:
            with open(sayings_path, 'r', encoding='utf-8') as f:
                theme.sayings = json.load(f)
        except FileNotFoundError:
            print(f"Info: No sayings file found for theme '{theme.name}' at {sayings_path}")
        except json.JSONDecodeError:
            print(f"Warning: Could not parse sayings file for theme '{theme.name}' at {sayings_path}")

    def _load_jokes_for_theme(self, theme, theme_path):
        """Loads all jokes for a theme from a single file named after the theme."""
        jokes_filename = f"jokes_{theme.name.lower()}.json"
        jokes_path = os.path.join(theme_path, jokes_filename)

        try:
            with open(jokes_path, 'r', encoding='utf-8') as f:
                theme.jokes = json.load(f)
        except FileNotFoundError:
            print(f"Info: No jokes file found for theme '{theme.name}' at {jokes_path}")
        except json.JSONDecodeError:
            print(f"Warning: Could not parse jokes file for theme '{theme.name}' at {jokes_path}")


    def get_theme(self, name): return self.themes.get(name)
    def get_all_themes(self): return list(self.themes.values())