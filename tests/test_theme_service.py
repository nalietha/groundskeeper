import json
import os
import shutil
import tempfile
import unittest

from core.theme_service import ThemeService


class ThemeServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.themes_dir = os.path.join(self.tmp, "themes")
        os.makedirs(self.themes_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _make_theme_dir(self, folder, settings, sayings=None, jokes=None):
        theme_path = os.path.join(self.themes_dir, folder)
        os.makedirs(os.path.join(theme_path, "assets"), exist_ok=True)
        with open(os.path.join(theme_path, "settings.json"), "w", encoding="utf-8") as f:
            json.dump(settings, f)
        name = settings.get("name", "").lower()
        if sayings is not None:
            with open(os.path.join(theme_path, f"list_{name}.json"), "w", encoding="utf-8") as f:
                json.dump(sayings, f)
        if jokes is not None:
            with open(os.path.join(theme_path, f"jokes_{name}.json"), "w", encoding="utf-8") as f:
                json.dump(jokes, f)
        return theme_path

    def test_loads_active_theme(self):
        self._make_theme_dir("coffee", {"name": "Coffee", "active": True, "timer_ms": 5000})
        svc = ThemeService(themes_dir=self.themes_dir)
        self.assertIsNotNone(svc.get_theme("Coffee"))
        self.assertEqual(svc.get_theme("Coffee").timer_ms, 5000)

    def test_skips_inactive_theme(self):
        self._make_theme_dir("coffee", {"name": "Coffee", "active": True})
        self._make_theme_dir("tea", {"name": "Tea", "active": False})
        svc = ThemeService(themes_dir=self.themes_dir)
        self.assertIsNotNone(svc.get_theme("Coffee"))
        self.assertIsNone(svc.get_theme("Tea"))

    def test_missing_active_flag_defaults_to_skipped(self):
        self._make_theme_dir("plain", {"name": "Plain"})
        svc = ThemeService(themes_dir=self.themes_dir)
        self.assertIsNone(svc.get_theme("Plain"))

    def test_get_all_themes(self):
        self._make_theme_dir("coffee", {"name": "Coffee", "active": True})
        self._make_theme_dir("tea", {"name": "Tea", "active": True})
        svc = ThemeService(themes_dir=self.themes_dir)
        names = sorted(t.name for t in svc.get_all_themes())
        self.assertEqual(names, ["Coffee", "Tea"])

    def test_loads_sayings_and_jokes(self):
        self._make_theme_dir(
            "coffee",
            {"name": "Coffee", "active": True},
            sayings={"Fresh": [{"catcher": "hi", "descriptor": "there"}]},
            jokes=["knock knock"],
        )
        svc = ThemeService(themes_dir=self.themes_dir)
        theme = svc.get_theme("Coffee")
        self.assertIn("Fresh", theme.sayings)
        self.assertEqual(theme.jokes, ["knock knock"])

    def test_detects_standard_assets(self):
        theme_path = self._make_theme_dir("coffee", {"name": "Coffee", "active": True})
        icon = os.path.join(theme_path, "assets", "icon.png")
        with open(icon, "wb") as f:
            f.write(b"\x89PNG")
        svc = ThemeService(themes_dir=self.themes_dir)
        self.assertEqual(svc.get_theme("Coffee").icon, icon)

    def test_malformed_settings_is_skipped_gracefully(self):
        theme_path = os.path.join(self.themes_dir, "broken")
        os.makedirs(theme_path)
        with open(os.path.join(theme_path, "settings.json"), "w", encoding="utf-8") as f:
            f.write("{ not json")
        # Should not raise; simply loads zero themes.
        svc = ThemeService(themes_dir=self.themes_dir)
        self.assertEqual(svc.get_all_themes(), [])

    def test_nonexistent_dir_is_safe(self):
        svc = ThemeService(themes_dir=os.path.join(self.tmp, "does_not_exist"))
        self.assertEqual(svc.get_all_themes(), [])


if __name__ == "__main__":
    unittest.main()
