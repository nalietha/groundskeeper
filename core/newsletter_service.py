import urllib.request
import json
import random
from datetime import datetime

class NewsletterService:
    def __init__(self, joke_service, affirmation_service):
        self.joke_service = joke_service
        self.affirmation_service = affirmation_service
        
        self.mindful_goals = [
            "Take 3 deep breaths before opening your email inbox.",
            "Drink a glass of water while your coffee cools.",
            "Stretch your arms above your head for 10 seconds.",
            "Find one small thing on your desk to throw away or organize.",
            "Look out a window and find something you hadn't noticed before."
        ]
        
        self.pointless_horoscopes = [
            "Taurus: You will encounter a door today. It may be a push or a pull. Be prepared.",
            "Gemini: The stars align to tell you that today is indeed a day.",
            "Leo: Beware of rectangular objects. They are plotting.",
            "Virgo: You will breathe air at least 500 times today.",
            "Scorpio: The moon is in retrograde, which means absolutely nothing for your spreadsheet.",
            "Capricorn: You will experience a mild craving for a snack around 2:30 PM."
        ]

    def get_fun_fact(self):
        """Fetches a random fun fact from a free public API."""
        try:
            req = urllib.request.Request('https://uselessfacts.jsph.pl/api/v2/facts/random', headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
                return data.get('text')
        except Exception:
            return None

    def get_word_of_the_day(self):
        """Fetches a random word from a free API."""
        try:
            with urllib.request.urlopen('https://random-word-api.herokuapp.com/word', timeout=3) as response:
                word = json.loads(response.read().decode())[0]
                return f"{word.capitalize()}"
        except Exception:
            return None

    def generate_morning_newsletter(self, theme):
        """Builds a randomized dictionary of content for the morning email."""
        content = {}
        
        # 1. Core Element: Flip a coin between an Affirmation or a Joke
        if random.choice([True, False]):
            content['affirmation'] = self.affirmation_service.get_daily_affirmation()
        else:
            content['joke'] = self.joke_service.get_joke(theme=theme)
        
        # 2. Rotating Extras: Pick exactly 2 random extra widgets so it's always fresh
        extras_pool = ['fact', 'word', 'horoscope', 'goal']
        chosen_extras = random.sample(extras_pool, 2)

        if 'fact' in chosen_extras:
            fact = self.get_fun_fact()
            if fact: content['fun_fact'] = fact
            
        if 'word' in chosen_extras:
            word = self.get_word_of_the_day()
            if word: content['word_of_the_day'] = f"Today's word is '{word}'. See if you can use it in a meeting."
            
        if 'horoscope' in chosen_extras:
            content['horoscope'] = random.choice(self.pointless_horoscopes)
            
        if 'goal' in chosen_extras:
            content['mindful_goal'] = random.choice(self.mindful_goals)

        return content