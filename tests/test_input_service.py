import unittest
from unittest import mock

from hardware.input import (
    _TRANSITIONS,
    DialBackend,
    KeyboardDialBackend,
    RotaryEncoderBackend,
    create_backend,
)


class QuadratureDecodeTests(unittest.TestCase):
    """The encoder decoder is pure logic, so it tests without any hardware."""

    def setUp(self):
        self.rotations = []
        self.backend = RotaryEncoderBackend(
            self.rotations.append,
            {"steps_per_detent": 4},
        )

    def _feed(self, states):
        """Replays a sequence of (clk, dt) states through the decode table."""
        for clk, dt in states:
            new_state = (clk << 1) | dt
            movement = _TRANSITIONS[self.backend._state][new_state]
            self.backend._state = new_state
            if movement:
                self.backend._accumulate(movement)

    # Clockwise walks 00 -> 01 -> 11 -> 10 -> 00.
    CW = [(0, 1), (1, 1), (1, 0), (0, 0)]
    CCW = [(1, 0), (1, 1), (0, 1), (0, 0)]

    def test_one_clockwise_detent_emits_one_step(self):
        self._feed(self.CW)
        self.assertEqual(self.rotations, [1])

    def test_one_counter_clockwise_detent_emits_one_step(self):
        self._feed(self.CCW)
        self.assertEqual(self.rotations, [-1])

    def test_partial_detent_emits_nothing(self):
        self._feed(self.CW[:2])
        self.assertEqual(self.rotations, [])

    def test_multiple_detents_accumulate(self):
        self._feed(self.CW * 3)
        self.assertEqual(self.rotations, [1, 1, 1])

    def test_reversing_cancels_a_partial_detent(self):
        # Half a turn clockwise, then back again, should land on nothing.
        self._feed(self.CW[:2])
        self._feed([(0, 1), (0, 0)])
        self.assertEqual(self.rotations, [])

    def test_invert_flips_direction(self):
        rotations = []
        backend = RotaryEncoderBackend(rotations.append, {"steps_per_detent": 4, "invert": True})
        self.backend = backend
        self.rotations = rotations
        self._feed(self.CW)
        self.assertEqual(rotations, [-1])

    def test_bouncing_contact_does_not_register(self):
        # A two-bit jump (00 -> 11) is electrically impossible on a real
        # encoder; the table must score it as zero movement.
        self.assertEqual(_TRANSITIONS[0b00][0b11], 0)
        self.assertEqual(_TRANSITIONS[0b11][0b00], 0)
        self.assertEqual(_TRANSITIONS[0b01][0b10], 0)


class BackendSelectionTests(unittest.TestCase):
    def test_create_backend_by_name(self):
        self.assertIsInstance(create_backend("keyboard", lambda s: None), KeyboardDialBackend)
        self.assertIsInstance(create_backend("encoder", lambda s: None), RotaryEncoderBackend)

    def test_unknown_backend_falls_back_to_null(self):
        backend = create_backend("does-not-exist", lambda s: None)
        self.assertIs(type(backend), DialBackend)

    def test_null_backend_starts_and_emits_nothing(self):
        rotations = []
        backend = create_backend("null", rotations.append)
        self.assertTrue(backend.start())
        backend.stop()
        self.assertEqual(rotations, [])

    def test_keyboard_backend_without_root_does_not_start(self):
        backend = KeyboardDialBackend(lambda s: None, {}, root=None)
        self.assertFalse(backend.start())


class InputServiceTests(unittest.TestCase):
    """InputService is tested against a fake root so it needs no display."""

    def setUp(self):
        from core.input_service import InputService

        self.root = mock.Mock()
        # Fake `after` runs the callback immediately, standing in for the Tk
        # event loop draining the queue.
        self.root.after = lambda delay, fn: fn()
        self.control = mock.Mock()
        self.service = InputService(self.root, self.control)

    def test_rotation_reaches_control_service(self):
        self.service._on_rotate(1)
        self.control.dial_rotate.assert_called_once_with(1)

    def test_disabled_dial_does_not_start(self):
        self.service.enabled = False
        self.assertFalse(self.service.start())
        self.assertIsNone(self.service.backend)

    def test_auto_selects_keyboard_when_gpio_absent(self):
        with mock.patch.object(RotaryEncoderBackend, "is_available", return_value=False):
            self.service.backend_name = "auto"
            self.assertEqual(self.service._resolve_backend_name(), "keyboard")

    def test_auto_selects_encoder_when_gpio_present(self):
        with mock.patch.object(RotaryEncoderBackend, "is_available", return_value=True):
            self.service.backend_name = "auto"
            self.assertEqual(self.service._resolve_backend_name(), "encoder")

    def test_failed_backend_leaves_service_inert(self):
        self.service.backend_name = "keyboard"
        self.service.root = None
        self.assertFalse(self.service.start())
        self.assertIsNone(self.service.backend)


if __name__ == "__main__":
    unittest.main()
