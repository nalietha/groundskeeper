# groundskeeper/hardware/input.py
"""Hardware backends for the rotational dial.

Every backend turns a physical (or simulated) knob into a stream of signed
detent counts and hands them to one ``on_rotate(steps)`` callback: positive is
clockwise, negative is counter-clockwise. Backends know nothing about menus --
InputService decides what a rotation *means*, so swapping the hardware never
touches the UI.

Backend callbacks may fire from a non-Tk thread. InputService is responsible
for marshalling them onto the UI thread; backends must not touch widgets.

Adding a backend: subclass DialBackend, implement is_available/start/stop, and
register it in BACKENDS. An absolute-position source (e.g. a potentiometer on
an MCP3008 ADC) fits by tracking the last reported notch and emitting the
difference as steps.
"""

# --- Quadrature decode table ------------------------------------------------
# State is (clk << 1) | dt, so the four states are 0b00, 0b01, 0b10, 0b11.
# A clockwise turn walks 00 -> 01 -> 11 -> 10 -> 00; counter-clockwise walks it
# backwards. Indexing [previous_state][new_state] yields +1, -1, or 0 for the
# impossible two-bit jumps that contact bounce produces -- which is what makes
# this table tolerant of noisy detents without any debounce delay.
_TRANSITIONS = (
    #  to 00  01  10  11
    (0, +1, -1, 0),   # from 00
    (-1, 0, 0, +1),   # from 01
    (+1, 0, 0, -1),   # from 10
    (0, -1, +1, 0),   # from 11
)


class DialBackend:
    """Base class and no-op implementation."""

    name = "null"

    def __init__(self, on_rotate, settings=None, root=None):
        self.on_rotate = on_rotate
        self.settings = settings or {}
        self.root = root

    @classmethod
    def is_available(cls):
        """True when this backend's dependencies/hardware are present."""
        return True

    def start(self):
        """Begins listening. Returns True if the backend is now live."""
        return True

    def stop(self):
        """Releases any hardware or bindings. Must be safe to call twice."""


class KeyboardDialBackend(DialBackend):
    """Simulates a dial with keys and the mouse wheel, for desktop development.

    The wheel is the closest stand-in for a detented knob -- one notch of the
    wheel is one detent of the dial -- so the feel can be checked on a laptop
    before the encoder is wired up.
    """

    name = "keyboard"

    def __init__(self, on_rotate, settings=None, root=None):
        super().__init__(on_rotate, settings, root)
        self.cw_key = self.settings.get("cw_key", "<period>")
        self.ccw_key = self.settings.get("ccw_key", "<comma>")
        self._bindings = []

    @classmethod
    def is_available(cls):
        return True

    def start(self):
        if self.root is None:
            print("Dial: keyboard backend needs a Tk root; not started.")
            return False

        self._bind(self.cw_key, lambda e: self._emit(1))
        self._bind(self.ccw_key, lambda e: self._emit(-1))

        # Wheel events differ by platform: Windows/macOS deliver <MouseWheel>
        # with a signed delta, X11 delivers buttons 4 (up) and 5 (down).
        self._bind("<MouseWheel>", self._on_wheel)
        self._bind("<Button-4>", lambda e: self._emit(-1))
        self._bind("<Button-5>", lambda e: self._emit(1))

        print(f"Dial: keyboard/wheel simulation active ({self.ccw_key} / {self.cw_key} / scroll).")
        return True

    def stop(self):
        for event, binding_id in self._bindings:
            try:
                self.root.unbind(event, binding_id)
            except Exception:
                pass
        self._bindings = []

    def _bind(self, event, callback):
        self._bindings.append((event, self.root.bind(event, callback)))

    def _on_wheel(self, event):
        # Scrolling away from you (positive delta) reads as clockwise.
        self._emit(1 if getattr(event, "delta", 0) > 0 else -1)

    def _emit(self, steps):
        self.on_rotate(steps)
        return "break"


class RotaryEncoderBackend(DialBackend):
    """Incremental quadrature encoder (KY-040 and friends) on two GPIO pins.

    Decoding is interrupt-driven and uses the transition table above rather
    than a sleep-based debounce, so a fast spin is not dropped and a bouncing
    contact cannot register a phantom detent.
    """

    name = "encoder"

    def __init__(self, on_rotate, settings=None, root=None):
        super().__init__(on_rotate, settings, root)
        self.clk_pin = self.settings.get("clk_pin", 17)
        self.dt_pin = self.settings.get("dt_pin", 27)
        # A KY-040 completes four quadrature transitions per mechanical detent.
        self.steps_per_detent = max(1, int(self.settings.get("steps_per_detent", 4)))
        self.invert = bool(self.settings.get("invert", False))

        self._state = 0
        self._accumulator = 0
        self._started = False

    @classmethod
    def is_available(cls):
        try:
            import RPi.GPIO  # noqa: F401
            return True
        except (ImportError, RuntimeError):
            return False

    def start(self):
        if not self.is_available():
            print("Dial: RPi.GPIO not available; encoder backend not started.")
            return False

        import RPi.GPIO as GPIO

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self._state = self._read_state(GPIO)
        for pin in (self.clk_pin, self.dt_pin):
            GPIO.add_event_detect(pin, GPIO.BOTH, callback=self._on_edge)

        self._started = True
        print(f"Dial: encoder active on CLK={self.clk_pin}, DT={self.dt_pin}.")
        return True

    def stop(self):
        if not self._started:
            return
        import RPi.GPIO as GPIO
        for pin in (self.clk_pin, self.dt_pin):
            try:
                GPIO.remove_event_detect(pin)
            except Exception:
                pass
        self._started = False

    def _read_state(self, GPIO):
        return (GPIO.input(self.clk_pin) << 1) | GPIO.input(self.dt_pin)

    def _on_edge(self, _channel):
        import RPi.GPIO as GPIO
        new_state = self._read_state(GPIO)
        movement = _TRANSITIONS[self._state][new_state]
        self._state = new_state
        if movement:
            self._accumulate(movement)

    def _accumulate(self, movement):
        """Collects quadrature steps and emits once a full detent is turned."""
        self._accumulator += movement
        while abs(self._accumulator) >= self.steps_per_detent:
            direction = 1 if self._accumulator > 0 else -1
            self._accumulator -= direction * self.steps_per_detent
            self.on_rotate(-direction if self.invert else direction)


BACKENDS = {
    RotaryEncoderBackend.name: RotaryEncoderBackend,
    KeyboardDialBackend.name: KeyboardDialBackend,
    DialBackend.name: DialBackend,
}


def create_backend(name, on_rotate, settings=None, root=None):
    """Builds a backend by name, falling back to the no-op one if unknown."""
    backend_class = BACKENDS.get(name)
    if backend_class is None:
        print(f"Dial: unknown backend '{name}'; dial disabled.")
        backend_class = DialBackend
    return backend_class(on_rotate, settings, root)
