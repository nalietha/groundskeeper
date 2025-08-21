import json
from datetime import datetime

class AffirmationService:
    """
    Loads and provides a unique affirmation for each day of the year.
    """
    def __init__(self, filename="resources/affirmation.json"):
        self.affirmations = []
        try:
            with open(filename, 'r') as f:
                self.affirmations = json.load(f)
            print(f"Successfully loaded {len(self.affirmations)} affirmations.")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load affirmations file '{filename}' ({e}).")
            # Provide a fallback affirmation if the file is missing or invalid
            self.affirmations = ["Today is a good day to have a good day."]

    def get_daily_affirmation(self):
        """
        Selects a deterministic affirmation based on the day of the year.
        """
        if not self.affirmations:
            return "You are doing great!"

        # Use the day of the year to get a consistent daily affirmation
        day_of_year = datetime.now().timetuple().tm_yday
        # Use modulo to loop through affirmations if there are more days than affirmations
        index = (day_of_year - 1) % len(self.affirmations)
        
        return self.affirmations[index]
