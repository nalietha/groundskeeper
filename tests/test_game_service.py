import json
import os
import tempfile
import unittest

from core.game_service import GameService
from tests.support import ConfigStub


class GameServiceLeaderboardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.leaderboard = os.path.join(self.tmp, "leaderboard.json")
        self.svc = GameService(ConfigStub())
        # Redirect persistence to a temp file so tests never touch real data.
        self.svc.leaderboard_file = self.leaderboard

    def _seed(self, entries):
        with open(self.leaderboard, "w", encoding="utf-8") as f:
            json.dump(entries, f)

    def test_get_scores_missing_file(self):
        self.assertEqual(self.svc.get_scores(), [])

    def test_get_scores_sorted_descending(self):
        self._seed([
            {"game": "snake", "name": "A", "score": 10},
            {"game": "snake", "name": "B", "score": 50},
            {"game": "snake", "name": "C", "score": 30},
        ])
        scores = self.svc.get_scores()
        self.assertEqual([s["score"] for s in scores], [50, 30, 10])

    def test_get_scores_filtered_by_game(self):
        self._seed([
            {"game": "snake", "name": "A", "score": 10},
            {"game": "tetris", "name": "B", "score": 99},
        ])
        scores = self.svc.get_scores("snake")
        self.assertEqual(len(scores), 1)
        self.assertEqual(scores[0]["name"], "A")

    def test_save_score_appends_and_sorts(self):
        self.svc.save_score("snake", "Alice", 100)
        self.svc.save_score("snake", "Bob", 200)
        scores = self.svc.get_scores("snake")
        self.assertEqual([s["name"] for s in scores], ["Bob", "Alice"])

    def test_save_score_caps_at_100_entries(self):
        for i in range(120):
            self.svc.save_score("snake", f"P{i}", i)
        with open(self.leaderboard, encoding="utf-8") as f:
            stored = json.load(f)
        self.assertEqual(len(stored), 100)
        # The highest scores are the ones retained.
        self.assertEqual(stored[0]["score"], 119)

    def test_is_high_score_rejects_non_positive(self):
        self.assertFalse(self.svc.is_high_score("snake", 0))
        self.assertFalse(self.svc.is_high_score("snake", -5))

    def test_is_high_score_true_when_board_not_full(self):
        self._seed([{"game": "snake", "name": "A", "score": 10}])
        self.assertTrue(self.svc.is_high_score("snake", 1))

    def test_is_high_score_compares_against_fifth_place(self):
        self._seed([{"game": "snake", "name": f"P{i}", "score": s}
                    for i, s in enumerate([50, 40, 30, 20, 10])])
        self.assertTrue(self.svc.is_high_score("snake", 15))   # beats 5th (10)
        self.assertFalse(self.svc.is_high_score("snake", 5))   # below 5th (10)


class GameServiceDiscoveryTests(unittest.TestCase):
    def test_discovery_returns_dict_with_expected_shape(self):
        svc = GameService(ConfigStub())
        games = svc.get_available_games()
        self.assertIsInstance(games, dict)
        # Whatever games ship in the repo, each discovered entry is annotated
        # with resolved paths by the discovery step.
        for manifest in games.values():
            self.assertIn("root_path", manifest)
            self.assertIn("card_path", manifest)
            self.assertIn("module_path", manifest)


if __name__ == "__main__":
    unittest.main()
