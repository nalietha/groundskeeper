# groundskeeper/views/extras.py
import tkinter as tk
from .bases import MenuScreen

class ExtrasView(MenuScreen):
    def setup_ui(self):
        title_label = tk.Label(self.content_frame, text="Extras & Fun", font=self.fonts["title"])
        title_label.pack(pady=(20, 10))

        button_area = tk.Frame(self.content_frame)
        button_area.pack(expand=True)

        joke_button = tk.Button(button_area, text="Daily Joke", font=self.fonts["button"], command=self.callbacks['show_joke'])
        joke_button.pack(pady=10, fill="x", padx=20)

        affirmation_button = tk.Button(button_area, text="Daily Affirmation", font=self.fonts["button"], command=self.callbacks['show_affirmation'])
        affirmation_button.pack(pady=10, fill="x", padx=20)

        games_button = tk.Button(button_area, text="Games", font=self.fonts["button"], command=self.callbacks['show_games'])
        games_button.pack(pady=10, fill="x", padx=20)

        # Add the new buttons to the navigable list (the back button is already there from the base class)
        self.navigable_widgets = [joke_button, affirmation_button, games_button] + self.navigable_widgets
        self.setup_navigation()