import tkinter as tk
from views.screen import Screen

class SettingsView(Screen):
    def setup_ui(self):
        title_label = tk.Label(self.content_frame, text="Settings", font=self.fonts["title"])
        title_label.pack(pady=(20, 10))

        button_frame = tk.Frame(self.content_frame)
        button_frame.pack(expand=True, padx=20)

        update_button = tk.Button(
            button_frame,
            text="Check for Updates",
            font=self.fonts["button"],
            command=self.callbacks['show_updater']
        )
        update_button.pack(pady=10, fill="x")

        reset_button = tk.Button(
            button_frame,
            text="Reset All Timers",
            font=self.fonts["button"],
            command=self.callbacks['reset_all_items']
        )
        reset_button.pack(pady=10, fill="x")

        self.turbo_button = tk.Button(
            button_frame,
            text="Turbo: OFF",
            font=self.fonts["button"],
            command=self.callbacks['toggle_turbo_mode']
        )
        self.turbo_button.pack(pady=10, fill="x")

        back_button = tk.Button(
            self.content_frame,
            text="Back to Menu",
            font=self.fonts["button"],
            command=self.callbacks['show_main_menu']
        )
        back_button.pack(pady=(10, 20))
        
        # Register navigable widgets
        self.navigable_widgets = [update_button, reset_button, self.turbo_button, back_button]

    def update_turbo_button_state(self, is_on):
        if is_on:
            self.turbo_button.config(text="Turbo: ON", relief=tk.SUNKEN)
        else:
            self.turbo_button.config(text="Turbo: OFF", relief=tk.RAISED)