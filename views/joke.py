# groundskeeper/views/joke.py
import tkinter as tk
from views.bases import SingleButtonScreen

class JokeView(SingleButtonScreen):
    def setup_ui(self):
        # The content_frame is centered.
        title_label = tk.Label(self.content_frame, text="Your Daily Joke", font=self.fonts["subtitle"])
        title_label.pack(pady=(10, 10))

        self.joke_label = tk.Label(self.content_frame, text="", font=self.fonts["body"], wraplength=self.config.SCREEN_WIDTH - 20, justify="center")
        self.joke_label.pack(expand=True)
        
        # Navigation setup is all that's needed.
        self.setup_navigation()