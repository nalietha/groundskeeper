import tkinter as tk
from views.screen import Screen

class AffirmationView(Screen):
    """
    A screen to display a single, centered message with a back button.
    """
    def setup_ui(self):
        title_label = tk.Label(self, text="Your Daily Affirmation", font=self.fonts["subtitle"])
        title_label.pack(pady=(20, 10))

        self.affirmation_label = tk.Label(
            self,
            text="", # The text will be set by the controller
            font=self.fonts["body"],
            wraplength=280, # Adjust wrap length for portrait screen
            justify="center"
        )
        self.affirmation_label.pack(expand=True, padx=20)

        # The callback for this button is 'show_main_menu', which is more reusable
        # than a specific 'back_to_menu' callback.
        back_button = tk.Button(
            self,
            text="Back to Menu",
            font=self.fonts["button"],
            command=self.callbacks['show_main_menu']
        )
        back_button.pack(pady=(10, 20))
