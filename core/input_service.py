# groundskeeper/core/input_service.py
"""Owns the rotational dial and feeds its rotations into ControlService.

The dial is deliberately thin: one turn of a detent becomes one `on_up` or
`on_down` intent, which is exactly what the existing buttons already produce.
Every screen therefore supports the dial for free -- the carousel scrolls, menu
focus moves, and NameEntryView cycles letters, with no per-screen changes.

This service is also the thread boundary. Encoder edges arrive on a GPIO
callback thread, and Tk is not thread-safe, so rotations are re-queued onto the
UI thread with `root.after` before anything touches a widget.
"""
from pathlib import Path

from core.utils import load_json
from hardware.input import create_backend

DEFAULT_KEYBINDS = "configs/keybinds.json"


class InputService:
    def __init__(self, root, control_service, keybinds_file=DEFAULT_KEYBINDS):
        self.root = root
        self.control_service = control_service

        # Anchor to the project root so the dial config still loads when the
        # app is launched from somewhere other than the source directory
        # (systemd units start with CWD=/, for instance).
        config_path = Path(__file__).parent.parent / keybinds_file
        settings = load_json(config_path, default={}) or {}
        self.dial_settings = settings.get("dial", {})

        self.enabled = self.dial_settings.get("enabled", True)
        self.backend_name = self.dial_settings.get("backend", "auto")
        self.backend = None

    def start(self):
        """Selects and starts a backend. Returns True if a dial is live."""
        if not self.enabled:
            print("Dial: disabled in keybinds.json.")
            return False

        name = self._resolve_backend_name()
        self.backend = create_backend(name, self._on_rotate, self.dial_settings, self.root)

        if not self.backend.start():
            # A backend that cannot start (no GPIO, no root) leaves the buttons
            # working rather than taking the app down with it.
            self.backend = None
            return False
        return True

    def stop(self):
        if self.backend:
            self.backend.stop()
            self.backend = None

    def _resolve_backend_name(self):
        """Picks the real encoder when the hardware is present, else the sim."""
        if self.backend_name != "auto":
            return self.backend_name

        from hardware.input import RotaryEncoderBackend, KeyboardDialBackend
        if RotaryEncoderBackend.is_available():
            return RotaryEncoderBackend.name
        return KeyboardDialBackend.name

    def _on_rotate(self, steps):
        """Backend entry point. May be called from a non-Tk thread."""
        self.root.after(0, lambda: self.control_service.dial_rotate(steps))
