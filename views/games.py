import tkinter as tk
from views.screen import Screen

class GamesView(Screen):
    def setup_ui(self):
        title_label = tk.Label(self.content_frame, text="Games", font=self.fonts["title"])
        title_label.pack(pady=(20, 10))

        button_area = tk.Frame(self.content_frame)
        button_area.pack(expand=True)

        snake_button = tk.Button(button_area, text="Play Snake", font=self.fonts["button"], command=self.callbacks['start_snake'])
        snake_button.pack(pady=10, fill="x")

        leaderboard_button = tk.Button(button_area, text="Leaderboard", font=self.fonts["button"], command=self.callbacks['show_leaderboard'])
        leaderboard_button.pack(pady=10, fill="x")

        self.button_frame.columnconfigure(0, weight=1)
        back_button = tk.Button(self.button_frame, text="Back to Menu", font=self.fonts["button"], command=self.callbacks['show_main_menu'])
        back_button.grid(row=0, column=0, sticky="ew", pady=10)

        self.navigable_widgets = [snake_button, leaderboard_button, back_button]