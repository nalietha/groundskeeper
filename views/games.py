import tkinter as tk
from views.screen import Screen

class GamesView(Screen):
    def setup_ui(self):
        # All widgets are now placed in self.content_frame for centering
        title_label = tk.Label(self.content_frame, text="Games", font=self.fonts["title"])
        title_label.pack(pady=(20, 10))

        button_frame = tk.Frame(self.content_frame)
        button_frame.pack(expand=True, padx=20)

        snake_button = tk.Button(
            button_frame,
            text="Play Snake",
            font=self.fonts["button"],
            command=self.callbacks['start_snake']
        )
        snake_button.pack(pady=10, fill="x")

        leaderboard_button = tk.Button(
            button_frame,
            text="Leaderboard",
            font=self.fonts["button"],
            command=self.callbacks['show_leaderboard']
        )
        leaderboard_button.pack(pady=10, fill="x")

        back_button = tk.Button(
            self.content_frame,
            text="Back to Menu",
            font=self.fonts["button"],
            command=self.callbacks['show_main_menu']
        )
        back_button.pack(pady=(10, 20))