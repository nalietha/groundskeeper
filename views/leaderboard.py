# groundskeeper/views/leaderboard.py
import tkinter as tk
from .bases import MenuScreen

class LeaderboardView(MenuScreen):
    def __init__(self, parent, callbacks, fonts, config, **kwargs):
        super().__init__(parent, callbacks, fonts, config, **kwargs)
        self.setup_ui()

    def setup_ui(self):
        # Make the title label an instance variable so we can change it
        self.title_label = tk.Label(self.content_frame, text="Leaderboard", font=self.fonts["title"])
        self.title_label.pack(pady=(20, 10))

        self.scores_frame = tk.Frame(self.content_frame)
        self.scores_frame.pack(expand=True, fill="both", padx=20)

        self.setup_navigation()

    def display_scores(self, game_name, scores):
        """Displays scores for a specific game."""
        # Update the title to show which game's leaderboard this is
        game_title = game_name.replace("_", " ").title()
        self.title_label.config(text=f"{game_title} Scores")

        for widget in self.scores_frame.winfo_children():
            widget.destroy()

        if not scores:
            no_scores_label = tk.Label(self.scores_frame, text="No scores yet!", font=self.fonts["body"])
            no_scores_label.pack()
            return

        for i, score_entry in enumerate(scores[:10]):
            rank = f"{i + 1}."
            name = score_entry.get("name", "Player")
            score = score_entry.get("score", 0)

            entry_text = f"{rank:<3} {name:<10} {score:>5}"
            score_label = tk.Label(self.scores_frame, text=entry_text, font=("Courier", 12, "bold"))
            score_label.pack(anchor="w")

    def go_back(self):
        if 'show_games' in self.callbacks:
            self.callbacks['show_games']()