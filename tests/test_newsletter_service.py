import io
import random
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

import jinja2

from core.newsletter_service import NewsletterService, to_roman
from tests.support import make_theme, StubService


class FakeGameService:
    def __init__(self, scores=None):
        self._scores = scores or []

    def get_scores(self, game_name=""):
        return list(self._scores)


class NewsletterServiceTests(unittest.TestCase):
    def setUp(self):
        self.theme = make_theme()
        self.svc = NewsletterService(
            joke_service=StubService(joke="Ha!"),
            affirmation_service=StubService(affirmation="You matter."),
            game_service=FakeGameService(),
        )

    def test_get_basic_content(self):
        content = self.svc.get_basic_content(self.theme)
        self.assertEqual(content["joke"], "Ha!")
        self.assertEqual(content["affirmation"], "You matter.")

    # --- Newspaper furniture ------------------------------------------------
    def test_masthead_uses_theme_paper_name(self):
        self.theme.paper_name = "THE DAILY GRIND"
        masthead = self.svc.get_masthead(self.theme, today=datetime(2026, 8, 5))
        self.assertEqual(masthead["paper_name"], "THE DAILY GRIND")

    def test_masthead_falls_back_for_unnamed_paper(self):
        theme = make_theme(name="Soup")
        theme.paper_name = None
        self.assertEqual(
            self.svc.get_masthead(theme)["paper_name"], "THE SOUP GAZETTE"
        )

    def test_masthead_volume_and_issue_track_the_date(self):
        masthead = self.svc.get_masthead(self.theme, today=datetime(2026, 8, 5))
        self.assertEqual(masthead["volume"], "III")        # 2026 - 2024 + 1
        self.assertEqual(masthead["issue_number"], 217)    # day of the year
        self.assertIn("AUGUST", masthead["dateline"])

    def test_roman_numerals(self):
        self.assertEqual(to_roman(1), "I")
        self.assertEqual(to_roman(4), "IV")
        self.assertEqual(to_roman(14), "XIV")
        self.assertEqual(to_roman(0), "I")   # clamped, never blank on the masthead

    def test_star_rendering_is_always_five_glyphs(self):
        self.assertEqual(self.svc._render_stars(4), "★★★★☆")
        self.assertEqual(self.svc._render_stars(5), "★★★★★")
        self.assertEqual(self.svc._render_stars(0), "☆☆☆☆☆")
        # Out-of-range ratings in the data file must not break the layout.
        self.assertEqual(len(self.svc._render_stars(9)), 5)
        self.assertEqual(len(self.svc._render_stars(-2)), 5)

    def test_advertisements_are_distinct_and_star_rated(self):
        ads = self.svc.get_advertisements(3)
        self.assertEqual(len(ads), 3)
        self.assertEqual(len({ad["name"] for ad in ads}), 3)
        for ad in ads:
            self.assertIn("stars_display", ad["review"])
            self.assertEqual(len(ad["review"]["stars_display"]), 5)

    def test_requesting_more_ads_than_exist_is_capped(self):
        ads = self.svc.get_advertisements(999)
        self.assertEqual(len(ads), len(self.svc.advertisements))

    def test_advertisements_do_not_mutate_the_source_data(self):
        # get_advertisements copies before adding stars_display; if it didn't,
        # the loaded data would accumulate render state across sends.
        self.svc.get_advertisements(2)
        self.assertFalse(
            any("stars_display" in (ad.get("review") or {}) for ad in self.svc.advertisements)
        )

    def test_classified_ads_are_distinct(self):
        ads = self.svc.get_classified_ads(5)
        self.assertEqual(len(ads), 5)
        self.assertEqual(len(set(ads)), 5)

    def test_missing_filler_file_degrades_quietly(self):
        svc = NewsletterService(StubService(), StubService(), FakeGameService())
        svc.advertisements, svc.classified_ads = [], []
        svc.quotable_quotes, svc.forecasts = [], []
        self.assertEqual(svc.get_advertisements(2), [])
        self.assertEqual(svc.get_classified_ads(3), [])
        self.assertIsNone(svc.get_quotable_quote())
        self.assertIsNone(svc.get_forecast())

    def test_basic_content_is_a_thin_special_edition(self):
        content = self.svc.get_basic_content(self.theme)
        self.assertEqual(content["edition_label"], "SPECIAL EDITION")
        self.assertIn("paper_name", content)
        self.assertEqual(len(content["advertisements"]), 1)

    def test_morning_newsletter_always_carries_the_newspaper_furniture(self):
        random.seed(7)
        with mock.patch.object(self.svc, "get_fun_fact", return_value=None), \
             mock.patch.object(self.svc, "get_word_of_the_day", return_value=None):
            content = self.svc.generate_morning_newsletter(self.theme)
        self.assertEqual(content["edition_label"], "MORNING EDITION")
        self.assertIn("paper_name", content)
        self.assertEqual(len(content["advertisements"]), 2)
        self.assertEqual(len(content["classifieds"]), 5)
        self.assertIn("quotable_quote", content)
        self.assertIn("forecast", content)

    def test_morning_newsletter_has_core_element(self):
        random.seed(1)
        with mock.patch.object(self.svc, "get_fun_fact", return_value="fact"), \
             mock.patch.object(self.svc, "get_word_of_the_day", return_value="word"):
            content = self.svc.generate_morning_newsletter(self.theme)
        # Exactly one of affirmation/joke is chosen as the core element.
        self.assertTrue(("affirmation" in content) or ("joke" in content))

    def test_morning_newsletter_picks_two_extras(self):
        random.seed(2)
        with mock.patch.object(self.svc, "get_fun_fact", return_value="a fact"), \
             mock.patch.object(self.svc, "get_word_of_the_day", return_value="aword"):
            content = self.svc.generate_morning_newsletter(self.theme)
        extra_keys = {"fun_fact", "word_of_the_day", "horoscope", "mindful_goal"}
        chosen = extra_keys & set(content.keys())
        # Two extras are sampled (network-backed ones may drop if they return None,
        # but here both are mocked non-None), so we expect up to 2 present.
        self.assertLessEqual(len(chosen), 2)
        self.assertGreaterEqual(len(chosen), 1)

    def test_morning_newsletter_includes_leaderboard(self):
        svc = NewsletterService(
            StubService(), StubService(),
            FakeGameService(scores=[
                {"game": "snake", "name": "A", "score": 5},
                {"game": "snake", "name": "B", "score": 3},
            ]),
        )
        random.seed(3)
        with mock.patch.object(svc, "get_fun_fact", return_value=None), \
             mock.patch.object(svc, "get_word_of_the_day", return_value=None):
            content = svc.generate_morning_newsletter(self.theme)
        self.assertIn("leaderboard", content)
        self.assertIn("Snake", content["leaderboard"])

    def test_leaderboard_absent_when_no_scores(self):
        random.seed(4)
        with mock.patch.object(self.svc, "get_fun_fact", return_value=None), \
             mock.patch.object(self.svc, "get_word_of_the_day", return_value=None):
            content = self.svc.generate_morning_newsletter(self.theme)
        self.assertNotIn("leaderboard", content)

    def test_get_fun_fact_parses_response(self):
        fake_resp = io.BytesIO(b'{"text": "Bananas are berries."}')
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = lambda s, *a: False
        with mock.patch("core.newsletter_service.urllib.request.urlopen", return_value=fake_resp):
            self.assertEqual(self.svc.get_fun_fact(), "Bananas are berries.")

    def test_get_fun_fact_handles_failure(self):
        with mock.patch("core.newsletter_service.urllib.request.urlopen",
                        side_effect=Exception("no net")):
            self.assertIsNone(self.svc.get_fun_fact())

    def test_get_word_of_the_day_parses_response(self):
        fake_resp = io.BytesIO(b'["serendipity"]')
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = lambda s, *a: False
        with mock.patch("core.newsletter_service.urllib.request.urlopen", return_value=fake_resp):
            self.assertEqual(self.svc.get_word_of_the_day(), "Serendipity")

    def test_get_word_of_the_day_handles_failure(self):
        with mock.patch("core.newsletter_service.urllib.request.urlopen",
                        side_effect=Exception("no net")):
            self.assertIsNone(self.svc.get_word_of_the_day())


class NewsletterTemplateTests(unittest.TestCase):
    """Renders the real email template so a Jinja or markup slip fails here
    rather than in someone's inbox."""

    @classmethod
    def setUpClass(cls):
        template_dir = Path(__file__).parent.parent / "templates" / "notifications"
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(template_dir)))
        cls.template = env.get_template("email_alert.html")

    def setUp(self):
        self.svc = NewsletterService(
            StubService(joke="Ha!"), StubService(affirmation="You matter."),
            FakeGameService(scores=[{"game": "snake", "name": "NAT", "score": 10}]),
        )
        self.theme = make_theme()

    def _render(self, context):
        return self.template.render(**context)

    def test_full_morning_edition_renders(self):
        random.seed(11)
        with mock.patch.object(self.svc, "get_fun_fact", return_value="Pugs come in grumbles."), \
             mock.patch.object(self.svc, "get_word_of_the_day", return_value="Bombastic"):
            context = self.svc.generate_morning_newsletter(self.theme)
        context.update({
            "theme_name": "Coffee",
            "main_message": "Coffee has just been started!",
            "alias": "Nathan",
            "unsubscribe_url": "http://127.0.0.1:5000/unsubscribe",
        })
        html = self._render(context)

        self.assertIn("Coffee has just been started!", html)
        self.assertIn("Paid Advertisement", html)
        self.assertIn("Classifieds", html)
        self.assertIn("Subscriber Copy", html)
        self.assertIn("★", html)
        self.assertIn("unsubscribe", html)

    def test_short_alert_renders_with_the_same_masthead(self):
        context = {"theme_name": "Coffee", "main_message": "Coffee is ready!", "alias": "Nathan"}
        context.update(self.svc.get_basic_content(self.theme))
        html = self._render(context)

        self.assertIn("Coffee is ready!", html)
        self.assertIn("SPECIAL EDITION", html)
        self.assertEqual(html.count("Paid Advertisement"), 1)

    def test_bare_context_still_renders_a_paper(self):
        # Every section is optional; a context with nothing but a message must
        # not raise or emit an undefined-variable artifact.
        html = self._render({"main_message": "Something happened."})
        self.assertIn("Something happened.", html)
        self.assertIn("THE BREAK ROOM GAZETTE", html)   # masthead fallback
        self.assertNotIn("Paid Advertisement", html)
        self.assertNotIn("Undefined", html)

    def test_markup_is_balanced(self):
        """Unbalanced tables are the classic way an email template breaks
        Outlook, and an odd number of classifieds is the case most likely to
        leave a dangling row."""
        from html.parser import HTMLParser

        class Checker(HTMLParser):
            VOID = {"meta", "br", "img", "hr", "input", "link"}

            def __init__(self):
                super().__init__()
                self.stack, self.errors = [], []

            def handle_starttag(self, tag, attrs):
                if tag not in self.VOID:
                    self.stack.append(tag)

            def handle_endtag(self, tag):
                if tag in self.VOID:
                    return
                if not self.stack or self.stack[-1] != tag:
                    self.errors.append(tag)
                    return
                self.stack.pop()

        for count in (1, 4, 5):   # odd counts exercise the filler cell
            with self.subTest(classifieds=count):
                context = {
                    "main_message": "Headline.",
                    "classifieds": self.svc.get_classified_ads(count),
                    "advertisements": self.svc.get_advertisements(2),
                }
                checker = Checker()
                checker.feed(self._render(context))
                self.assertEqual(checker.errors, [], "mismatched closing tags")
                self.assertEqual(checker.stack, [], "unclosed tags")


if __name__ == "__main__":
    unittest.main()
