import unittest
from unittest import mock

from tests.support import TK_AVAILABLE

if TK_AVAILABLE:
    import tkinter as tk
    from views.bases import BaseScreen

    class DummyScreen(BaseScreen):
        def setup_ui(self):
            pass


@unittest.skipUnless(TK_AVAILABLE, "Tk display not available")
class BaseScreenInputTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.callbacks = {"show_main_menu": mock.Mock()}
        self.screen = DummyScreen(self.root, self.callbacks, {}, object())

    def tearDown(self):
        self.root.destroy()

    # --- Default (button-list) behavior ------------------------------------
    def test_on_up_navigates_backwards(self):
        self.screen.navigate = mock.Mock()
        self.screen.on_up()
        self.screen.navigate.assert_called_once_with(-1)

    def test_on_down_navigates_forwards(self):
        self.screen.navigate = mock.Mock()
        self.screen.on_down()
        self.screen.navigate.assert_called_once_with(1)

    def test_on_left_right_navigate(self):
        self.screen.navigate = mock.Mock()
        self.screen.on_left()
        self.screen.on_right()
        self.screen.navigate.assert_has_calls([mock.call(-1), mock.call(1)])

    def test_on_select_invokes_widget(self):
        self.screen.invoke_widget = mock.Mock()
        self.screen.on_select()
        self.screen.invoke_widget.assert_called_once()

    def test_on_back_calls_go_back(self):
        self.screen.on_back()
        self.callbacks["show_main_menu"].assert_called_once()

    # --- Carousel-backed behavior ------------------------------------------
    def test_on_up_down_drive_carousel(self):
        self.screen.carousel = mock.Mock()
        self.screen.on_up()
        self.screen.on_down()
        self.screen.carousel.go_previous.assert_called_once()
        self.screen.carousel.go_next.assert_called_once()

    def test_on_select_invokes_carousel_callback(self):
        callback = mock.Mock()
        self.screen.carousel = mock.Mock()
        self.screen.carousel.get_current_callback.return_value = callback
        self.screen.on_select()
        callback.assert_called_once()

    def test_on_select_carousel_without_callback_is_safe(self):
        self.screen.carousel = mock.Mock()
        self.screen.carousel.get_current_callback.return_value = None
        # Should not raise.
        self.screen.on_select()


if __name__ == "__main__":
    unittest.main()
