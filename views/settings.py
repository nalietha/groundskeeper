# groundskeeper/views/settings.py
import tkinter as tk
from .bases import MenuScreen 

class SettingsView(MenuScreen):
    def setup_ui(self):
        # The content_frame is provided by the MenuScreen base class
        title_label = tk.Label(self.content_frame, text="Settings", font=self.fonts["title"])
        title_label.pack(pady=(20, 10))

        button_area = tk.Frame(self.content_frame)
        button_area.pack(expand=True, padx=20)

        update_button = tk.Button(button_area, text="Check for Updates", font=self.fonts["button"], command=self.callbacks['show_updater'])
        update_button.pack(pady=10, fill="x")

        reset_button = tk.Button(button_area, text="Reset All Timers", font=self.fonts["button"], command=self.callbacks['reset_all_items'])
        reset_button.pack(pady=10, fill="x")

        self.turbo_button = tk.Button(button_area, text="Turbo: OFF", font=self.fonts["button"], command=self.callbacks['toggle_turbo_mode'])
        self.turbo_button.pack(pady=10, fill="x")

        debug_button = tk.Button(button_area, text="Debug Menu", font=self.fonts["button"], command=self.callbacks.get('show_debug_menu'))
        debug_button.pack(pady=10, fill="x")
        
        # The "Back" button is created by the MenuScreen base.
        # We just need to add our new buttons to the navigation list.
        self.navigable_widgets = [update_button, reset_button, self.turbo_button, debug_button] + self.navigable_widgets
        self.setup_navigation()

        ip_address = self.get_ip_address()
        ip_label = tk.Label(self.content_frame, text=f"IP: {ip_address}", font=("Courier", 10), fg="gray")
        ip_label.pack(side="bottom", pady=10)

    def get_ip_address(self):
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def update_turbo_button_state(self, is_on):
        """Updates the turbo button's appearance."""
        if is_on:
            self.turbo_button.config(text="Turbo: ON", relief=tk.SUNKEN)
        else:
            self.turbo_button.config(text="Turbo: OFF", relief=tk.RAISED)