import tkinter as tk
from views.screen import Screen

class SettingsView(Screen):
    """
    A screen for application settings.
    """
    def setup_ui(self):
        title_label = tk.Label(self, text="Settings", font=self.fonts["title"])
        title_label.pack(pady=(20, 10))

        button_frame = tk.Frame(self)
        button_frame.pack(expand=True, padx=20)

        update_button = tk.Button(
            button_frame,
            text="Check for Updates",
            font=self.fonts["button"],
            command=self.callbacks['show_updater']
        )
        update_button.pack(pady=10, fill="x")

        # Add other settings buttons here in the future

        back_button = tk.Button(
            self,
            text="Back to Menu",
            font=self.fonts["button"],
            command=self.callbacks['show_main_menu']
        )
        back_button.pack(pady=(10, 20))