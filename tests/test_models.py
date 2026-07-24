import unittest

from models.theme import Theme
from models.mood import Mood


class ThemeTests(unittest.TestCase):
    def test_defaults_when_data_empty(self):
        theme = Theme({})
        self.assertEqual(theme.name, "Unknown")
        self.assertEqual(theme.action_text, "Start")
        self.assertEqual(theme.start_phrase, "Last Start:")
        self.assertEqual(theme.not_started_text, "Not Started")
        self.assertEqual(theme.timer_ms, 60000)
        self.assertEqual(theme.mood_tiers, [])
        self.assertEqual(theme.jokes, [])
        self.assertEqual(theme.sayings, {})

    def test_placeholders_start_empty(self):
        theme = Theme({})
        self.assertIsNone(theme.icon)
        self.assertIsNone(theme.theme_card)
        self.assertIsNone(theme.standby_bg)
        self.assertIsNone(theme.symbol)
        self.assertEqual(theme.loading_images, [])
        self.assertEqual(theme.game_styles, {})

    def test_parses_supplied_values(self):
        theme = Theme({
            "name": "Tea",
            "timer_ms": 90000,
            "mood_tiers": [{"name": "Fresh", "threshold_minutes": 0}],
        })
        self.assertEqual(theme.name, "Tea")
        self.assertEqual(theme.timer_ms, 90000)
        self.assertEqual(len(theme.mood_tiers), 1)

    def test_colors_merge_with_defaults(self):
        theme = Theme({"colors": {"bright_bg": "#ffffff"}})
        self.assertEqual(theme.colors["bright_bg"], "#ffffff")
        # Unsupplied color keys still fall back to defaults.
        self.assertEqual(theme.colors["dim_bg"], "#1e1e1e")
        self.assertIn("dim_fg", theme.colors)
        self.assertIn("bright_fg", theme.colors)


class MoodTests(unittest.TestCase):
    def test_stores_fields(self):
        mood = Mood("Catcher", "Descriptor", "🔥")
        self.assertEqual(mood.catcher, "Catcher")
        self.assertEqual(mood.descriptor, "Descriptor")
        self.assertEqual(mood.emoji, "🔥")

    def test_emoji_defaults_empty(self):
        mood = Mood("c", "d")
        self.assertEqual(mood.emoji, "")


if __name__ == "__main__":
    unittest.main()
