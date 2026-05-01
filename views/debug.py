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

        test_email_btn = tk.Button(
            button_area, 
            text="Test Email Config", 
            font=self.fonts["button"], 
            command=self._test_email
        )
        test_email_btn.pack(pady=10, fill="x")

        self.navigable_widgets = [test_email_btn] + self.navigable_widgets
        self.setup_navigation()

    def _test_email(self):
        self.status_label.config(text="Sending test email...")
        self.content_frame.update_idletasks()
        if 'test_email' in self.callbacks:
            success, msg = self.callbacks['test_email']()
            color = "green" if success else "red"
            self.status_label.config(text=msg, fg=color)
