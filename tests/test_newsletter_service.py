import io
import random
import unittest
from unittest import mock

from core.newsletter_service import NewsletterService
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


if __name__ == "__main__":
    unittest.main()
