import json
import os
import tempfile
import unittest
from datetime import datetime

from core.affirmation_service import AffirmationService


class AffirmationServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _write(self, name, data):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def test_loads_categorized_format(self):
        path = self._write("aff.json", {
            "affirmations": {"calm": ["A", "B"], "energy": ["C"]}
        })
        svc = AffirmationService(filename=path)
        self.assertEqual(sorted(svc.affirmations), ["A", "B", "C"])

    def test_loads_flat_list_format(self):
        path = self._write("flat.json", ["One", "Two"])
        svc = AffirmationService(filename=path)
        self.assertEqual(svc.affirmations, ["One", "Two"])

    def test_missing_file_uses_fallback(self):
        svc = AffirmationService(filename=os.path.join(self.tmp, "nope.json"))
        self.assertEqual(svc.affirmations, ["Today is a good day to have a good day."])

    def test_daily_affirmation_is_deterministic(self):
        path = self._write("aff.json", {"affirmations": {"x": ["A", "B", "C"]}})
        svc = AffirmationService(filename=path)
        self.assertEqual(svc.get_daily_affirmation(), svc.get_daily_affirmation())

    def test_daily_affirmation_indexes_by_day_of_year(self):
        items = [f"aff-{i}" for i in range(400)]
        path = self._write("big.json", items)
        svc = AffirmationService(filename=path)
        expected = items[(datetime.now().timetuple().tm_yday - 1) % len(items)]
        self.assertEqual(svc.get_daily_affirmation(), expected)

    def test_empty_affirmations_returns_generic(self):
        path = self._write("flat.json", ["Only"])
        svc = AffirmationService(filename=path)
        svc.affirmations = []
        self.assertEqual(svc.get_daily_affirmation(), "You are doing great!")


if __name__ == "__main__":
    unittest.main()
