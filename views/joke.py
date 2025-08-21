import tkinter as tk
from views.screen import Screen

class JokeView(Screen):
    """
    A screen to display a single, centered message with a back button.
    """
    def setup_ui(self):
        title_label = tk.Label(self, text="Your Daily Joke", font=self.fonts["subtitle"])
        title_label.pack(pady=(20, 10))

        self.joke_label = tk.Label(
            self,
            text="", # The text will be set by the controller
            font=self.fonts["body"],
            wraplength=280, # Adjust wrap length for portrait screen
            justify="center"
        )
        self.joke_label.pack(expand=True, padx=20)

        back_button = tk.Button(
            self,
            text="Back to Menu",
            font=self.fonts["button"],
            command=self.callbacks['show_main_menu']
        )
        back_button.pack(pady=(10, 20))