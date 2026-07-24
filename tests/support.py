"""Shared fixtures, fakes, and helpers for the Groundskeeper test suite."""
import tkinter as tk

from models.theme import Theme


# --------------------------------------------------------------------------
# Tk availability probe — GUI-dependent tests skip cleanly on headless boxes.
# --------------------------------------------------------------------------
def tk_available():
    try:
        root = tk.Tk()
        root.destroy()
        return True
    except Exception:
        return False


TK_AVAILABLE = tk_available()


# --------------------------------------------------------------------------
# Model factories
# --------------------------------------------------------------------------
def make_theme(name="Coffee", timer_ms=60000, mood_tiers=None, sayings=None,
               jokes=None, colors=None):
    """Builds a Theme with sensible test defaults."""
    theme = Theme({
        "name": name,
        "timer_ms": timer_ms,
        "mood_tiers": mood_tiers or [],
        "colors": colors or {},
    })
    theme.sayings = sayings or {}
    theme.jokes = jokes or []
    return theme


# --------------------------------------------------------------------------
# Service test doubles
# --------------------------------------------------------------------------
class FakeThemeService:
    def __init__(self, themes=()):
        self._themes = {t.name: t for t in themes}

    def get_theme(self, name):
        return self._themes.get(name)

    def get_all_themes(self):
        return list(self._themes.values())


class RecordingNotificationService:
    """Captures send_notification calls instead of sending email."""
    def __init__(self):
        self.calls = []

    def send_notification(self, theme_name, context, test_mode=False):
        # Store a copy so later mutation of context doesn't corrupt the record.
        self.calls.append({
            "theme_name": theme_name,
            "context": dict(context),
            "test_mode": test_mode,
        })


class StubService:
    """Minimal stand-in for joke/affirmation services."""
    def __init__(self, joke="A joke.", affirmation="Be well."):
        self._joke = joke
        self._affirmation = affirmation

    def get_joke(self, theme=None):
        return self._joke

    def get_daily_affirmation(self):
        return self._affirmation


class ConfigStub:
    SCREEN_WIDTH = 240
    SCREEN_HEIGHT = 320
    DEFAULT_THEME = "Coffee"
