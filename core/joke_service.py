import json
import random

class JokeService:
    """
    Loads and provides jokes.
    """
    def __init__(self, filename="assets/jokes.json"):
        self.jokes = []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.jokes = json.load(f)
            print(f"Successfully loaded {len(self.jokes)} jokes.")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load jokes file '{filename}' ({e}).")
            self.jokes = ["I tried to tell a joke, but I forgot the punchline."]

    def get_joke(self, theme=None):
        """
        Gets a random joke, either general or theme-specific.
        """
        all_jokes = self.jokes[:] # Create a copy
        if theme and hasattr(theme, 'jokes') and theme.jokes:
            all_jokes.extend(theme.jokes)
        
        if not all_jokes:
            return "No jokes found!"

        return random.choice(all_jokes)