import json
class Config:
    """Loads global configuration from appsettings.json."""
    def __init__(self, filename="appsettings.json"):
        # Default values
        self.SCREEN_WIDTH = 320
        self.SCREEN_HEIGHT = 240
        self.BASE_WIDTH = 320
        self.FONT_SIZES = {"title": 26, "subtitle": 18, "body": 14, "small": 12, "button": 16}
        self.INACTIVITY_TIMEOUT_MS = 5000
        self.DEFAULT_THEME = "Coffee"
        self.USE_24H_CLOCK = False

        try:
            with open(filename, 'r') as f:
                config_data = json.load(f)
            
            screen = config_data.get("screen", {})
            fonts = config_data.get("fonts", {})
            timing = config_data.get("timing", {})
            app = config_data.get("app", {})

            self.SCREEN_WIDTH = screen.get("width", self.SCREEN_WIDTH)
            self.SCREEN_HEIGHT = screen.get("height", self.SCREEN_HEIGHT)
            self.BASE_WIDTH = screen.get("base_width_for_scaling", self.BASE_WIDTH)
            self.FONT_SIZES = fonts or self.FONT_SIZES
            self.INACTIVITY_TIMEOUT_MS = timing.get("inactivity_timeout_ms", self.INACTIVITY_TIMEOUT_MS)
            self.USE_24H_CLOCK = timing.get("use_24h_clock", self.USE_24H_CLOCK)
            self.DEFAULT_THEME = app.get("default_theme", self.DEFAULT_THEME)
            print(f"Successfully loaded global settings from {filename}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load '{filename}' ({e}). Using default settings.")
