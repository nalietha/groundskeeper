import urllib.request
import json
import random
from datetime import datetime
from pathlib import Path

from core.deck import Deck
from core.utils import load_json

# The paper is dated from a fixed epoch so the volume number climbs by one a
# year and the issue number matches the day -- the masthead then reads as a
# real back-catalogue rather than random digits.
PAPER_EPOCH_YEAR = 2024

CLASSIFIEDS_FILE = "assets/lists/classifieds.json"


def to_roman(number):
    """Renders a small positive integer as a Roman numeral for the masthead."""
    if number < 1:
        return "I"
    numerals = (
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"),
        (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"),
        (5, "V"), (4, "IV"), (1, "I"),
    )
    result = []
    for value, symbol in numerals:
        count, number = divmod(number, value)
        result.append(symbol * count)
    return "".join(result)


class NewsletterService:
    def __init__(self, joke_service, affirmation_service, game_service, deck_file=None):
        """`deck_file` persists the no-repeat rotation. It defaults to None so
        tests and previews run in-memory; the app passes a real path."""
        self.joke_service = joke_service
        self.affirmation_service = affirmation_service
        self.game_service = game_service

        # Anchored to the project root so the filler still loads when the app
        # is started from outside the source directory.
        classifieds_path = Path(__file__).parent.parent / CLASSIFIEDS_FILE
        filler = load_json(classifieds_path, default={}) or {}
        self.advertisements = filler.get("advertisements", [])
        self.classified_ads = filler.get("classifieds", [])
        self.quotable_quotes = filler.get("quotes", [])
        self.forecasts = filler.get("forecasts", [])

        if deck_file and not Path(deck_file).is_absolute():
            deck_file = Path(__file__).parent.parent / deck_file
        self.deck = Deck(deck_file)

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

    # --- Newspaper furniture -------------------------------------------------
    # The email is laid out as a free break-room newspaper, so every send needs
    # a masthead, and the filler below is what sells the format: small-business
    # ads with star-rated testimonials, a classifieds column, and a forecast.
    # All of it is invented -- see the note at the top of classifieds.json.

    def get_masthead(self, theme, today=None):
        """Builds the masthead: paper name, volume/issue, and dateline."""
        today = today or datetime.now()
        paper_name = getattr(theme, 'paper_name', None) or f"THE {theme.name.upper()} GAZETTE"

        return {
            'paper_name': paper_name,
            'volume': to_roman(max(1, today.year - PAPER_EPOCH_YEAR + 1)),
            'issue_number': today.timetuple().tm_yday,
            'dateline': today.strftime("%A, %B %d, %Y").upper(),
            'edition_price': "COMPLIMENTARY · TAKE ONE",
        }

    @staticmethod
    def _render_stars(rating):
        """Turns a 0-5 rating into filled/hollow stars for the review blurbs."""
        filled = max(0, min(5, int(rating)))
        return "★" * filled + "☆" * (5 - filled)

    def get_advertisements(self, count=1):
        """Draws distinct fake business ads, each with its star-rated review."""
        if not self.advertisements:
            return []

        chosen = self.deck.draw('advertisements', self.advertisements, count)
        ads = []
        for ad in chosen:
            ad = dict(ad)
            review = dict(ad.get('review') or {})
            if review:
                review['stars_display'] = self._render_stars(review.get('stars', 5))
            ad['review'] = review
            ads.append(ad)
        return ads

    def get_classified_ads(self, count=4):
        """Draws distinct one-line small ads for the classifieds column."""
        return self.deck.draw('classifieds', self.classified_ads, count)

    def get_quotable_quote(self):
        return self.deck.draw_one('quotes', self.quotable_quotes)

    def get_forecast(self):
        return self.deck.draw_one('forecasts', self.forecasts)

    def get_basic_content(self, theme):
        """A minimal joke + affirmation pairing, used for one-off notifications
        (e.g. the 'ready' alert) that don't warrant the full morning newsletter.

        Still carries a masthead and a single ad so the short sends read as a
        one-page special edition rather than a different email entirely."""
        content = {
            'joke': self.joke_service.get_joke(theme=theme),
            'affirmation': self.affirmation_service.get_daily_affirmation(),
            'edition_label': "SPECIAL EDITION",
        }
        content.update(self.get_masthead(theme))

        ads = self.get_advertisements(1)
        if ads:
            content['advertisements'] = ads
        return content

    def generate_morning_newsletter(self, theme):
        """Builds a randomized dictionary of content for the morning email."""
        content = {'edition_label': "MORNING EDITION"}

        # 0. Masthead and newspaper filler. The ads, classifieds, quote and
        #    forecast are always present -- in a real free paper the ads are
        #    the reason the thing exists, so they never rotate out.
        content.update(self.get_masthead(theme))
        content['advertisements'] = self.get_advertisements(2)
        content['classifieds'] = self.get_classified_ads(5)

        quote = self.get_quotable_quote()
        if quote:
            content['quotable_quote'] = quote

        forecast = self.get_forecast()
        if forecast:
            content['forecast'] = forecast

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
            content['horoscope'] = self.deck.draw_one('horoscopes', self.pointless_horoscopes)

        if 'goal' in chosen_extras:
            content['mindful_goal'] = self.deck.draw_one('goals', self.mindful_goals)

        # 3. NEW: Always include the Top 3 Leaderboard if anyone has played!
        all_scores = self.game_service.get_scores()
        if all_scores:
            leaderboard_data = {}
            for entry in all_scores:
                game_name = entry.get('game', 'Unknown').replace('_', ' ').title()
                if game_name not in leaderboard_data:
                    leaderboard_data[game_name] = []
                # Only keep the top 3 for the email so it doesn't get too long
                if len(leaderboard_data[game_name]) < 3:
                    leaderboard_data[game_name].append(entry)
            
            content['leaderboard'] = leaderboard_data

        return content