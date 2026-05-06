import tkinter as tk
from views.bases import MenuScreen

class AffirmationView(MenuScreen):
    def __init__(self, parent, callbacks, fonts, config, **kwargs):
        super().__init__(parent, callbacks, fonts, config, **kwargs)
        self.setup_ui()
        
    def setup_ui(self):
        title_label = tk.Label(self.content_frame, text="Your Daily Affirmation", font=self.fonts["subtitle"])
        title_label.pack(pady=(20, 10))

        self.affirmation_label = tk.Label(self.content_frame, text="", font=self.fonts["body"], wraplength=self.config.SCREEN_WIDTH - 40, justify="center")
        self.affirmation_label.pack(expand=True, padx=20)
        
        self.setup_navigation()

    def go_back(self):
        """Overrides the default back behavior to go to the extras menu."""
        if 'show_extras' in self.callbacks:
            self.callbacks['show_extras']()