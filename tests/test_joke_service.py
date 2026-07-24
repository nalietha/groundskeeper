import json
import os
import tempfile
import unittest

from core.joke_service import JokeService
from tests.support import make_theme


class JokeServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _write(self, name, data):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def test_loads_jokes(self):
        path = self._write("jokes.json", ["j1", "j2", "j3"])
        svc = JokeService(filename=path)
        self.assertEqual(len(svc.jokes), 3)

    def test_missing_file_uses_fallback(self):
        svc = JokeService(filename=os.path.join(self.tmp, "nope.json"))
        self.assertEqual(svc.jokes, ["I tried to tell a joke, but I forgot the punchline."])

    def test_get_joke_returns_from_pool(self):
        path = self._write("jokes.json", ["only-joke"])
        svc = JokeService(filename=path)
        self.assertEqual(svc.get_joke(), "only-joke")

    def test_get_joke_includes_theme_jokes(self):
        path = self._write("jokes.json", [])
        svc = JokeService(filename=path)
        svc.jokes = []  # force empty base pool
        theme = make_theme(jokes=["theme-joke"])
        self.assertEqual(svc.get_joke(theme=theme), "theme-joke")

    def test_get_joke_with_no_jokes_returns_placeholder(self):
        path = self._write("jokes.json", [])
        svc = JokeService(filename=path)
        svc.jokes = []
        self.assertEqual(svc.get_joke(), "No jokes found!")

    def test_base_pool_is_not_mutated_by_theme_jokes(self):
        path = self._write("jokes.json", ["base"])
        svc = JokeService(filename=path)
        theme = make_theme(jokes=["extra"])
        svc.get_joke(theme=theme)
        self.assertEqual(svc.jokes, ["base"])


if __name__ == "__main__":
    unittest.main()
