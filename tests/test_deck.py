import json
import tempfile
import unittest
from pathlib import Path

from core.deck import Deck, default_key


class DeckDrawTests(unittest.TestCase):
    """The point of the deck is that nothing repeats until the pool is spent,
    so most of these assert on what does NOT come up."""

    def setUp(self):
        self.items = [f"item-{i}" for i in range(10)]
        self.deck = Deck()   # no state file -> in-memory

    def test_draw_returns_requested_count(self):
        self.assertEqual(len(self.deck.draw("c", self.items, 3)), 3)

    def test_consecutive_draws_never_repeat(self):
        seen = []
        for _ in range(5):
            seen.extend(self.deck.draw("c", self.items, 2))
        self.assertEqual(len(seen), 10)
        self.assertEqual(len(set(seen)), 10, "an item repeated before the pool was exhausted")

    def test_full_pass_covers_every_item(self):
        drawn = []
        for _ in range(5):
            drawn.extend(self.deck.draw("c", self.items, 2))
        self.assertEqual(set(drawn), set(self.items))

    def test_deck_reshuffles_after_exhaustion(self):
        for _ in range(5):
            self.deck.draw("c", self.items, 2)
        # Pool spent; the next draw must still return items.
        self.assertEqual(len(self.deck.draw("c", self.items, 2)), 2)

    def test_no_repeat_across_the_reshuffle_seam(self):
        """The items drawn last before a reshuffle must not come straight back
        out of the new deck -- otherwise the one repeat a reader would actually
        notice is the one the deck fails to prevent.

        Repeated because a single pass can pass on luck: with 2 drawn from 10,
        a naive reshuffle still avoids collision ~62% of the time."""
        for trial in range(50):
            deck = Deck()
            for _ in range(4):
                deck.draw("c", self.items, 2)
            last_of_pass = deck.draw("c", self.items, 2)
            first_of_next = deck.draw("c", self.items, 2)
            overlap = set(last_of_pass) & set(first_of_next)
            self.assertFalse(overlap, f"trial {trial}: {overlap} repeated across the seam")

    def test_partial_pass_is_topped_up_from_the_reshuffle(self):
        # 10 items, draw 4 at a time: the third draw has only 2 left.
        self.deck.draw("c", self.items, 4)
        self.deck.draw("c", self.items, 4)
        third = self.deck.draw("c", self.items, 4)
        self.assertEqual(len(third), 4)
        self.assertEqual(len(set(third)), 4)

    def test_categories_are_independent(self):
        a = self.deck.draw("quotes", self.items, 10)
        b = self.deck.draw("forecasts", self.items, 10)
        # Exhausting one category must not affect another.
        self.assertEqual(set(a), set(b))

    def test_empty_pool_and_zero_count(self):
        self.assertEqual(self.deck.draw("c", [], 3), [])
        self.assertEqual(self.deck.draw("c", self.items, 0), [])

    def test_count_larger_than_pool_returns_whole_pool(self):
        drawn = self.deck.draw("c", self.items, 99)
        self.assertEqual(len(drawn), 10)
        self.assertEqual(len(set(drawn)), 10)

    def test_draw_one(self):
        self.assertIn(self.deck.draw_one("c", self.items), self.items)
        self.assertIsNone(self.deck.draw_one("c", []))

    def test_reset_clears_state(self):
        self.deck.draw("c", self.items, 10)
        self.deck.reset("c")
        drawn = self.deck.draw("c", self.items, 10)
        self.assertEqual(len(set(drawn)), 10)


class DeckKeyTests(unittest.TestCase):
    def test_dicts_key_on_name_then_text(self):
        self.assertEqual(default_key({"name": "ACME"}), "ACME")
        self.assertEqual(default_key({"text": "a quote", "author": "x"}), "a quote")

    def test_strings_key_on_themselves(self):
        self.assertEqual(default_key("FOR SALE: chair"), "FOR SALE: chair")

    def test_dict_without_name_or_text_is_still_keyable(self):
        self.assertTrue(default_key({"a": 1, "b": 2}))

    def test_dicts_are_deduped_by_name_not_identity(self):
        """Re-reading classifieds.json yields new dict objects every boot, so
        identity-based dedup would silently never match. Keying on name is what
        makes the persisted state mean anything."""
        deck = Deck()
        ads = [{"name": "A"}, {"name": "B"}]
        first = deck.draw("ads", ads, 1)
        second = deck.draw("ads", [dict(a) for a in ads], 1)   # fresh dict objects
        self.assertEqual(len(second), 1)
        self.assertNotEqual(second[0]["name"], first[0]["name"])


class DeckPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "sub" / "deck.json"
        self.items = [f"item-{i}" for i in range(10)]

    def tearDown(self):
        self.tmp.cleanup()

    def test_state_survives_a_restart(self):
        first = Deck(self.path).draw("c", self.items, 4)
        # A fresh Deck stands in for the app restarting on the Pi.
        second = Deck(self.path).draw("c", self.items, 4)
        self.assertFalse(set(first) & set(second), "restart reshuffled the deck")

    def test_state_file_and_parent_directory_are_created(self):
        Deck(self.path).draw("c", self.items, 2)
        self.assertTrue(self.path.exists())
        state = json.loads(self.path.read_text(encoding="utf-8"))["c"]
        self.assertEqual(len(state["seen"]), 2)
        self.assertEqual(len(state["recent"]), 2)

    def test_corrupt_state_file_does_not_raise(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{not json", encoding="utf-8")
        self.assertEqual(len(Deck(self.path).draw("c", self.items, 3)), 3)

    def test_missing_state_file_starts_clean(self):
        self.assertEqual(len(Deck(self.path).draw("c", self.items, 3)), 3)

    def test_entries_dropped_from_the_pool_are_tolerated(self):
        """Editing classifieds.json shouldn't wedge a deck whose state still
        names removed entries."""
        Deck(self.path).draw("c", self.items, 6)
        shrunk = self.items[:3]
        drawn = Deck(self.path).draw("c", shrunk, 2)
        self.assertEqual(len(drawn), 2)
        self.assertTrue(set(drawn) <= set(shrunk))

    def test_new_entries_are_available_immediately(self):
        Deck(self.path).draw("c", self.items, 10)   # exhaust the pool
        grown = self.items + ["item-new"]
        # The new entry is unseen, so it should be reachable without a reshuffle.
        drawn = Deck(self.path).draw("c", grown, 1)
        self.assertEqual(drawn, ["item-new"])


if __name__ == "__main__":
    unittest.main()
