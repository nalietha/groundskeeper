import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

# Important: You might need to adjust the import path 
# depending on how you run your tests.
from core.mood_service import MoodService
from models.theme import Theme
from models.mood import Mood

class TestMoodService(unittest.TestCase):

    def setUp(self):
        """Set up a mock theme object that can be used in all tests."""
        # Create a fake theme settings dictionary
        mock_theme_data = {
            "name": "Test Coffee",
            "mood_tiers": [
                { "name": "fresh", "threshold_minutes": 0 },
                { "name": "stale", "threshold_minutes": 60 },
                { "name": "moldy", "threshold_minutes": 120 }
            ]
        }
        self.mock_theme = Theme(mock_theme_data)
        
        # Add fake sayings to the theme object
        self.mock_theme.sayings = {
            "fresh": [{"catcher": "It's fresh!", "descriptor": ""}],
            "stale": [{"catcher": "It's stale.", "descriptor": ""}],
            "moldy": [{"catcher": "It's moldy...", "descriptor": ""}]
        }

    def test_get_mood_fresh(self):
        """Test if the mood is 'fresh' when 30 minutes have passed."""
        start_time = datetime.now() - timedelta(minutes=30)
        mood = MoodService.get_mood_for_theme(self.mock_theme, start_time)
        self.assertEqual(mood.catcher, "It's fresh!")

    def test_get_mood_stale(self):
        """Test if the mood is 'stale' when 90 minutes have passed."""
        start_time = datetime.now() - timedelta(minutes=90)
        mood = MoodService.get_mood_for_theme(self.mock_theme, start_time)
        self.assertEqual(mood.catcher, "It's stale.")

    def test_get_mood_moldy(self):
        """Test if the mood is 'moldy' when 150 minutes have passed."""
        start_time = datetime.now() - timedelta(minutes=150)
        mood = MoodService.get_mood_for_theme(self.mock_theme, start_time)
        self.assertEqual(mood.catcher, "It's moldy...")

    def test_no_start_time(self):
        """Test the initial state before any action has started."""
        mood = MoodService.get_mood_for_theme(self.mock_theme, None)
        self.assertEqual(mood.catcher, "Welcome!")

if __name__ == '__main__':
    unittest.main()

