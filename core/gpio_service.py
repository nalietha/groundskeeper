import threading
import time

try:
    import RPi.GPIO as GPIO
    from pynput.keyboard import Key, Controller
    RPI_AVAILABLE = True
except (ImportError, RuntimeError):
    RPI_AVAILABLE = False

class GPIOService:
    def __init__(self, pin_mappings):
        if not RPI_AVAILABLE:
            print("Skipping GPIO setup: RPi.GPIO or pynput not found.")
            return

        self.keyboard = Controller()
        self.pin_mappings = pin_mappings
        self.stop_thread = False

        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        for pin in self.pin_mappings.values():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.thread = threading.Thread(target=self.monitor_pins)
        self.thread.daemon = True

    def start(self):
        if RPI_AVAILABLE:
            self.thread.start()
            print("GPIO monitoring started.")

    def stop(self):
        if RPI_AVAILABLE:
            self.stop_thread = True
            self.thread.join()
            GPIO.cleanup()
            print("GPIO monitoring stopped and cleaned up.")

    def monitor_pins(self):
        last_press_time = {key: 0 for key in self.pin_mappings.keys()}
        debounce_time = 0.2  # 200ms debounce delay

        while not self.stop_thread:
            current_time = time.time()
            for key_name, pin in self.pin_mappings.items():
                if GPIO.input(pin) == GPIO.LOW: # Button pressed
                    if (current_time - last_press_time[key_name]) > debounce_time:
                        key_to_press = self.get_key_from_name(key_name)
                        if key_to_press:
                            print(f"GPIO: Detected '{key_name}' press on pin {pin}. Simulating key: {key_to_press}")
                            self.keyboard.press(key_to_press)
                            self.keyboard.release(key_to_press)
                        last_press_time[key_name] = current_time
            time.sleep(0.02) # Small delay to prevent high CPU usage

    def get_key_from_name(self, name):
        key_map = {
            "up": Key.up,
            "down": Key.down,
            "left": Key.left,
            "right": Key.right,
            "select": Key.enter,
            "back": Key.backspace,
            "action1": 'a',
            "action2": 'b',
            "coin": Key.space
        }
        return key_map.get(name)