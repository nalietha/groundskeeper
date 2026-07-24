from datetime import datetime

from core.utils import load_json

class AffirmationService:
    """
    Loads and provides a unique affirmation for each day of the year.
    """
    def __init__(self, filename="assets/affirmation.json"):
        self.affirmations = []
        data = load_json(filename)

        if data is None:
            print(f"Warning: Could not load affirmations file '{filename}'.")
            # Provide a fallback affirmation if the file is missing or invalid
            self.affirmations = ["Today is a good day to have a good day."]
            return

        # Check if it's using the new categorized format
        if isinstance(data, dict) and "affirmations" in data:
            # Loop through each category and merge them into one flat list
            for _category, aff_list in data["affirmations"].items():
                self.affirmations.extend(aff_list)
        else:
            # Fallback just in case it ever reverts to a flat list
            self.affirmations = data

        print(f"Successfully loaded {len(self.affirmations)} affirmations.")

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