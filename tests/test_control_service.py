import unittest
from unittest import mock

from tests.support import TK_AVAILABLE

if TK_AVAILABLE:
    import tkinter as tk
    from core.control_service import ControlService

    class FakeApp:
        def __init__(self, root):
            self.root = root
            self.callbacks = {"show_games": mock.Mock()}
            self.active_theme_name = "Coffee"
            self.toggle_turbo_mode = mock.Mock()
            self.confirm_and_start_item = mock.Mock()


@unittest.skipUnless(TK_AVAILABLE, "Tk display not available")
class ControlServiceTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.app = FakeApp(self.root)
        self.cs = ControlService(self.app)
        self.screen = mock.MagicMock()
        self.cs.active_screen = self.screen
        self.cs.ui_context_active = True

    def tearDown(self):
        self.root.destroy()

    # --- Intent forwarding --------------------------------------------------
    def test_navigate_up_forwards_to_screen(self):
        self.cs.navigate_up(None)
        self.screen.on_up.assert_called_once()

    def test_navigate_down_forwards_to_screen(self):
        self.cs.navigate_down(None)
        self.screen.on_down.assert_called_once()

    def test_navigate_left_right_forward(self):
        self.cs.navigate_left(None)
        self.cs.navigate_right(None)
        self.screen.on_left.assert_called_once()
        self.screen.on_right.assert_called_once()

    def test_select_and_back_forward(self):
        self.cs.select(None)
        self.cs.back(None)
        self.screen.on_select.assert_called_once()
        self.screen.on_back.assert_called_once()

    def test_no_dispatch_when_ui_inactive(self):
        self.cs.ui_context_active = False
        self.cs.navigate_up(None)
        self.screen.on_up.assert_not_called()

    def test_handlers_return_break(self):
        # Returning "break" stops Tk from running default bindings.
        self.assertEqual(self.cs.navigate_up(None), "break")
        self.assertEqual(self.cs.select(None), "break")
        self.assertEqual(self.cs.back(None), "break")

    # --- A/B action buttons also record for the secret code -----------------
    def test_action_a_selects(self):
        self.cs.handle_action_a(None)
        self.screen.on_select.assert_called_once()

    def test_action_b_goes_back(self):
        self.cs.handle_action_b(None)
        self.screen.on_back.assert_called_once()

    # --- Konami code --------------------------------------------------------
    def test_konami_code_toggles_turbo(self):
        for key in ["up", "up", "down", "down", "left", "right", "left", "right", "b", "a"]:
            self.cs._record_key(key)
        self.app.toggle_turbo_mode.assert_called_once()

    def test_partial_konami_does_not_trigger(self):
        for key in ["up", "up", "down", "down"]:
            self.cs._record_key(key)
        self.app.toggle_turbo_mode.assert_not_called()

    def test_sequence_window_is_bounded(self):
        # Feeding noise then the full code should still trigger exactly once.
        for key in ["a", "b", "left", "up"]:
            self.cs._record_key(key)
        for key in ["up", "up", "down", "down", "left", "right", "left", "right", "b", "a"]:
            self.cs._record_key(key)
        self.app.toggle_turbo_mode.assert_called_once()


if __name__ == "__main__":
    unittest.main()
