import tkinter as tk
from .bases import MenuScreen

class DebugView(MenuScreen):
    def setup_ui(self):
        title_label = tk.Label(self.content_frame, text="Debug Menu", font=self.fonts["title"])
        title_label.pack(pady=(20, 10))

        button_area = tk.Frame(self.content_frame)
        button_area.pack(expand=True, padx=20)

        self.status_label = tk.Label(button_area, text="", font=self.fonts["body"], fg="blue", wraplength=200, justify="center")
        self.status_label.pack(pady=5)

        btn_test_config = tk.Button(button_area, text="Test SMTP Config", font=self.fonts["button"], command=lambda: self._run_test('test_email'))
        btn_test_config.pack(pady=5, fill="x")

        btn_test_started = tk.Button(button_area, text="Test 'Started' Email", font=self.fonts["button"], command=lambda: self._run_test('test_email_started'))
        btn_test_started.pack(pady=5, fill="x")

        btn_test_ready = tk.Button(button_area, text="Test 'Ready' Email", font=self.fonts["button"], command=lambda: self._run_test('test_email_ready'))
        btn_test_ready.pack(pady=5, fill="x")

        self.navigable_widgets = [btn_test_config, btn_test_started, btn_test_ready] + self.navigable_widgets
        self.setup_navigation()

    def _run_test(self, callback_key):
        """Runs the assigned test callback and updates the UI with the result."""
        self.status_label.config(text="Sending test email...", fg="blue")
        self.content_frame.update_idletasks()
        
        if callback_key in self.callbacks:
            success, msg = self.callbacks[callback_key]()
            color = "green" if success else "red"
            self.status_label.config(text=msg, fg=color)