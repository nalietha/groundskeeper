import random
from datetime import datetime

from models.mood import Mood

class MoodService:
    @staticmethod
    def get_mood_for_theme(theme, start_time):
        if not isinstance(start_time, datetime):
            return Mood("Welcome!", "Select an action to begin."), None
        
        sorted_tiers = sorted(theme.mood_tiers, key=lambda x: x['threshold_minutes'], reverse=True)
        elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60
        
        for tier in sorted_tiers:
            if elapsed_minutes >= tier['threshold_minutes']:
                tier_name = tier['name']
                sayings_list = theme.sayings.get(tier_name, [])
                if sayings_list:
                    chosen_saying = random.choice(sayings_list)
                    return Mood(chosen_saying.get('catcher'), chosen_saying.get('descriptor')), tier_name
                break
        return Mood("Hmm...", "No sayings found for this state."), None

