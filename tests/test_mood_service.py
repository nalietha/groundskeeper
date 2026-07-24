import unittest
from datetime import datetime, timedelta

from core.mood_service import MoodService
from models.mood import Mood
from tests.support import make_theme


MOOD_TIERS = [
    {"name": "Fresh", "threshold_minutes": 0, "emoji": "🌱"},
    {"name": "Warm", "threshold_minutes": 10, "emoji": "☕"},
    {"name": "Stale", "threshold_minutes": 60, "emoji": "🥶"},
]

SAYINGS = {
    "Fresh": [{"catcher": "Just brewed!", "descriptor": "Enjoy it now."}],
    "Warm": [{"catcher": "Still good.", "descriptor": "Drink up."}],
    "Stale": [{"catcher": "It's stale.", "descriptor": "Time for a refill."}],
}


class MoodServiceTests(unittest.TestCase):
    def setUp(self):
        self.theme = make_theme(mood_tiers=MOOD_TIERS, sayings=SAYINGS)

    def test_returns_tuple_of_mood_and_tier_name(self):
        mood, tier = MoodService.get_mood_for_theme(self.theme, datetime.now())
        self.assertIsInstance(mood, Mood)

    def test_welcome_when_no_start_time(self):
        mood, tier = MoodService.get_mood_for_theme(self.theme, None)
        self.assertEqual(mood.catcher, "Welcome!")
        self.assertIsNone(tier)

    def test_fresh_tier_immediately(self):
        mood, tier = MoodService.get_mood_for_theme(self.theme, datetime.now())
        self.assertEqual(tier, "Fresh")
        self.assertEqual(mood.catcher, "Just brewed!")
        self.assertEqual(mood.emoji, "🌱")

    def test_warm_tier_after_threshold(self):
        start = datetime.now() - timedelta(minutes=15)
        mood, tier = MoodService.get_mood_for_theme(self.theme, start)
        self.assertEqual(tier, "Warm")
        self.assertEqual(mood.catcher, "Still good.")

    def test_stale_tier_after_long_time(self):
        start = datetime.now() - timedelta(minutes=90)
        mood, tier = MoodService.get_mood_for_theme(self.theme, start)
        self.assertEqual(tier, "Stale")
        self.assertEqual(mood.catcher, "It's stale.")

    def test_deterministic_within_the_same_day(self):
        start = datetime.now() - timedelta(minutes=90)
        first = MoodService.get_mood_for_theme(self.theme, start)[0]
        second = MoodService.get_mood_for_theme(self.theme, start)[0]
        self.assertEqual(first.catcher, second.catcher)

    def test_tier_matched_but_no_sayings(self):
        theme = make_theme(mood_tiers=MOOD_TIERS, sayings={})
        mood, tier = MoodService.get_mood_for_theme(theme, datetime.now())
        self.assertEqual(mood.catcher, "Hmm...")
        self.assertIsNone(tier)


if __name__ == "__main__":
    unittest.main()
