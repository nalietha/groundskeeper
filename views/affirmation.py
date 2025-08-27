import tkinter as tk
from views.bases import MenuScreen

class AffirmationView(MenuScreen):
    def setup_ui(self):
        title_label = tk.Label(self.content_frame, text="Your Daily Affirmation", font=self.fonts["subtitle"])
        title_label.pack(pady=(20, 10))

        self.affirmation_label = tk.Label(self.content_frame, text="", font=self.fonts["body"], wraplength=self.config.SCREEN_WIDTH - 40, justify="center")
        self.affirmation_label.pack(expand=True, padx=20)
        
        self.setup_navigation()