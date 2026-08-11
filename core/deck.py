# groundskeeper/core/deck.py
"""Draws newsletter filler without repeating until the pool is exhausted.

`random.sample` is memoryless -- it can hand back the same quote two mornings
running, which is what makes a small pool feel far smaller than it is. This
deals from a shuffled deck instead: an item can't come up again until every
other item has. With the pools sized as they are, that's the difference between
"repeats most weeks" and "repeats once a quarter".

State is per-category and persisted, so a Pi reboot doesn't reshuffle the deck
mid-pass.
"""
import json
import random
from pathlib import Path


def default_key(item):
    """Identifies an item across restarts. Ads are dicts keyed by name; the
    one-liners are plain strings and stand for themselves."""
    if isinstance(item, dict):
        return item.get("name") or item.get("text") or json.dumps(item, sort_keys=True)
    return str(item)


class Deck:
    def __init__(self, state_file=None, key=default_key):
        self.state_file = Path(state_file) if state_file else None
        self.key = key
        self._state = self._load()

    # --- Persistence -------------------------------------------------------
    def _load(self):
        if not self.state_file or not self.state_file.exists():
            return {}
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            # A corrupt deck file costs a little repetition, not a crash.
            print(f"Warning: could not read deck state ({e}). Starting fresh.")
            return {}

        state = {}
        for category, entry in data.items():
            if isinstance(entry, dict):
                state[category] = {
                    "seen": list(entry.get("seen", [])),
                    "recent": list(entry.get("recent", [])),
                }
        return state

    def _save(self):
        if not self.state_file:
            return
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"Warning: could not save deck state ({e}).")

    # --- Drawing -----------------------------------------------------------
    def draw(self, category, items, count):
        """Returns up to `count` items not yet drawn this pass.

        When the remaining items can't cover the request the pass ends: the
        leftovers are dealt first, then the deck reshuffles to make up the
        shortfall. The reshuffle excludes both those leftovers *and* the
        previous draw -- without the latter, an item could come straight back
        out of the new deck, which is exactly the repeat a reader would notice.
        """
        if not items or count <= 0:
            return []

        entry = self._state.get(category, {})
        seen = set(entry.get("seen", []))
        recent = set(entry.get("recent", []))

        available = [item for item in items if self.key(item) not in seen]

        if len(available) >= count:
            drawn = random.sample(available, count)
            new_seen = seen | {self.key(item) for item in drawn}
        else:
            drawn = list(available)
            random.shuffle(drawn)
            drawn.extend(self._reshuffle_fill(items, drawn, recent, count - len(drawn)))
            new_seen = {self.key(item) for item in drawn}

        self._state[category] = {
            "seen": sorted(new_seen),
            "recent": sorted(self.key(item) for item in drawn),
        }
        self._save()
        return drawn

    def _reshuffle_fill(self, items, drawn, recent, shortfall):
        """Picks `shortfall` items from a freshly shuffled deck, avoiding what
        was just dealt and what came out last time."""
        if shortfall <= 0:
            return []

        blocked = {self.key(item) for item in drawn} | recent
        pool = [item for item in items if self.key(item) not in blocked]
        fill = random.sample(pool, min(shortfall, len(pool)))

        # A pool barely larger than the draw size can't honour the seam rule;
        # fill the rest from anything not already in this draw.
        if len(fill) < shortfall:
            taken = {self.key(item) for item in drawn + fill}
            rest = [item for item in items if self.key(item) not in taken]
            fill.extend(random.sample(rest, min(shortfall - len(fill), len(rest))))
        return fill

    def draw_one(self, category, items):
        drawn = self.draw(category, items, 1)
        return drawn[0] if drawn else None

    def reset(self, category=None):
        """Clears deck state, for one category or all of it."""
        if category is None:
            self._state = {}
        else:
            self._state.pop(category, None)
        self._save()
