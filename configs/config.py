import json
class Config:
    """Loads global configuration from appsettings.json."""
    def __init__(self, filename="appsettings.json"):
        # Default values
        self.SCREEN_WIDTH = 240
        self.SCREEN_HEIGHT = 320
        self.BASE_WIDTH = 320
        self.FONT_SIZES = {"title": 22, "subtitle": 18, "body": 15, "small": 12, "button": 16}
        self.INACTIVITY_TIMEOUT_MS = 5000
        self.DEFAULT_THEME = "Coffee"
        self.USE_24H_CLOCK = False
        self.GPIO_PINS = {}
        self.LATENCY_MS = 500 # Default latency
        self.LOADING_IMAGE_INTERVAL_MS = 250 # Time each loading image is shown

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            screen = config_data.get("screen", {})
            fonts = config_data.get("fonts", {})
            timing = config_data.get("timing", {})
            app = config_data.get("app", {})
            latency = config_data.get("latency", {})


            self.SCREEN_WIDTH = screen.get("width", self.SCREEN_WIDTH)
            self.SCREEN_HEIGHT = screen.get("height", self.SCREEN_HEIGHT)
            self.BASE_WIDTH = screen.get("base_width_for_scaling", self.BASE_WIDTH)
            self.FONT_SIZES = fonts or self.FONT_SIZES
            self.INACTIVITY_TIMEOUT_MS = timing.get("inactivity_timeout_ms", self.INACTIVITY_TIMEOUT_MS)
            self.USE_24H_CLOCK = timing.get("use_24h_clock", self.USE_24H_CLOCK)
            self.DEFAULT_THEME = app.get("default_theme", self.DEFAULT_THEME)
            self.GPIO_PINS = config_data.get("gpio_pins", self.GPIO_PINS)
            self.LATENCY_MS = latency.get("menu_load_ms", self.LATENCY_MS)
            self.LOADING_IMAGE_INTERVAL_MS = latency.get("loading_image_interval_ms", self.LOADING_IMAGE_INTERVAL_MS)
            print(f"Successfully loaded global settings from {filename}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load '{filename}' ({e}). Using default settings.")