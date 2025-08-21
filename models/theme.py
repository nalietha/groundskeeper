

class Theme:
    def __init__(self, data):
        self.name = data.get("name", "Unknown")
        self.action_text = data.get("action_text", "Start")
        self.timer_ms = data.get("timer_ms", 60000)
        colors = data.get("colors", {})
        self.colors = {
            "dim_bg": colors.get("dim_bg", "#1e1e1e"), "dim_fg": colors.get("dim_fg", "#a9a9a9"),
            "bright_bg": colors.get("bright_bg", "#add8e6"), "bright_fg": colors.get("bright_fg", "#000000"),
        }
        self.mood_sayings_file = data.get("mood_sayings_file", "")
        self.mood_tiers = data.get("mood_tiers", [])
        self.sayings = {}