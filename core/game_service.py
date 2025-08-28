# groundskeeper/core/game_service.py
import os
import json
import importlib.util
import pygame

class GameService:
    def __init__(self, config):
        self.config = config
        self.leaderboard_file = "leaderboard.json"
        self.games = self._discover_games()
        print(f"Discovered {len(self.games)} games.")

    def _discover_games(self):
        """Scans for and validates games based on their manifest.json file."""
        games = {}
        # Get the absolute path to the directory containing this script (core/)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to the project root (groundskeeper/)
        project_root = os.path.dirname(script_dir)
        games_dir = os.path.join(project_root, "games")

        if not os.path.isdir(games_dir):
            return games

        for game_name in os.listdir(games_dir):
            game_path = os.path.join(games_dir, game_name)
            manifest_path = os.path.join(game_path, "manifest.json")
            if os.path.isfile(manifest_path):
                try:
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)

                    # If the game is not marked as active, skip it.
                    if not manifest.get("active", False):
                        continue
                    
                    manifest['root_path'] = game_path
                    manifest['card_path'] = os.path.join(game_path, "game_card.png")
                    manifest['module_path'] = os.path.join(game_path, "game.py")
                    games[game_name] = manifest
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Warning: Could not load manifest for '{game_name}': {e}")
        return games

    def get_available_games(self):
        return self.games

    def start_game(self, game_name, theme):
        """Loads assets, resizes them according to the manifest, and starts the game."""
        manifest = self.games.get(game_name)
        if not manifest:
            print(f"Error: Game '{game_name}' not found.")
            return 0
            
        game_assets = self._load_assets_from_manifest(manifest)
        theme_styles = theme.game_styles.get(game_name, {})
        
        # --- FIX: Resilient Theme Asset Override ---
        for asset_key, theme_value in theme_styles.items():
            if asset_key in manifest.get("assets", {}):
                asset_data = manifest["assets"][asset_key]
                if asset_data.get("themeable"):
                    if "path" in asset_data:
                        dims = (asset_data.get("width"), asset_data.get("height"))
                        # Attempt to load the theme's asset
                        themed_asset = self._load_image(theme_value, dims)
                        # ONLY replace the default if the themed asset loaded successfully
                        if themed_asset:
                            game_assets[asset_key] = themed_asset
                    else:
                        game_assets[asset_key] = theme_value
        # ---------------------------------------------

        try:
            spec = importlib.util.spec_from_file_location(game_name, manifest["module_path"])
            game_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(game_module)
            game_class = getattr(game_module, manifest["entry_point"])
            
            game_instance = game_class(self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT, game_assets)
            score = game_instance.game_loop()
            return score
        except Exception as e:
            print(f"Error starting game '{game_name}': {e}")
            return 0

    def _load_assets_from_manifest(self, manifest):
        """Loads all default assets defined in the manifest, resizing them as specified."""
        assets = {}
        game_root = manifest['root_path']
        
        for key, data in manifest.get("assets", {}).items():
            if "path" in data:
                full_path = os.path.join(game_root, data["path"])
                dims = (data.get("width"), data.get("height"))
                assets[key] = self._load_image(full_path, dims)
            elif "default" in data:
                assets[key] = data["default"]
        return assets

    def _load_image(self, path, dimensions=(None, None)):
        """
        Helper to load a pygame image and resize it.
        Returns None on failure.
        """
        if not os.path.exists(path):
            print(f"Warning: Asset not found at path: {path}")
            return None
        
        try:
            image = pygame.image.load(path)
            width, height = dimensions
            if width is not None and height is not None:
                return pygame.transform.scale(image, (width, height))
            return image
        except pygame.error as e:
            print(f"Error loading or scaling image at {path}: {e}")
            return None
            
    def is_high_score(self, game_name, score):
        """Checks if a score is in the top 5 for a given game."""
        if score <= 0: return False
        scores = self.get_scores(game_name)
        if len(scores) < 5: return True
        return score > scores[4].get("score", 0)
            
    def get_scores(self, game_name=""):
        """Loads and sorts scores from the leaderboard file."""
        try:
            with open(self.leaderboard_file, 'r') as f:
                scores = json.load(f)
            if game_name:
                scores = [s for s in scores if s.get("game") == game_name]
            scores.sort(key=lambda x: x.get("score", 0), reverse=True)
            return scores
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_score(self, game_name, player_name, score):
        """Adds a new score to the leaderboard."""
        scores = self.get_scores()
        new_entry = {"game": game_name, "name": player_name, "score": score}
        scores.append(new_entry)
        
        scores.sort(key=lambda x: x.get("score", 0), reverse=True)
        with open(self.leaderboard_file, 'w') as f:
            json.dump(scores[:100], f, indent=4)
        print(f"Saved score for {player_name}: {score}")