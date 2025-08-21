import tkinter as tk
from views.screen import Screen

class JokeView(Screen):
    def setup_ui(self):
        # All widgets are now placed in self.content_frame for centering
        title_label = tk.Label(self.content_frame, text="Your Daily Joke", font=self.fonts["subtitle"])
        title_label.pack(pady=(20, 10))

        self.joke_label = tk.Label(
            self.content_frame,
            text="",
            font=self.fonts["body"],
            wraplength=self.config.SCREEN_WIDTH - 40,
            justify="center"
        )
        self.joke_label.pack(expand=True, padx=20)

        back_button = tk.Button(
            self.content_frame,
            text="Back to Menu",
            font=self.fonts["button"],
            command=self.callbacks['show_main_menu']
        )
        back_button.pack(pady=(10, 20))