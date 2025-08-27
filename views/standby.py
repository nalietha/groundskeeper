# groundskeeper/views/standby.py
import tkinter as tk
from .bases import TwoButtonScreen

class StandbyView(TwoButtonScreen):
    def setup_ui(self):
        # The content_frame is already created and centered by the base class
        self.theme_label = tk.Label(self.content_frame, text="", font=self.fonts["subtitle"])
        self.theme_label.pack(pady=(10, 0))

        self.last_start_label = tk.Label(self.content_frame, text="", font=self.fonts["small"])
        self.last_start_label.pack()
        
        # --- MODIFIED: Mood Frame Layout ---
        # This frame will hold the emoji and the catcher phrase
        mood_frame = tk.Frame(self.content_frame)
        mood_frame.pack(pady=20, padx=5, fill="x", expand=True) # Fill horizontal space

        # Configure the grid inside the mood_frame to manage space
        mood_frame.columnconfigure(0, weight=0) # Emoji column (fixed size)
        mood_frame.columnconfigure(1, weight=1) # Text column (takes remaining space)

        self.mood_emoji_label = tk.Label(mood_frame, text="", font=self.fonts["title"])
        self.mood_emoji_label.grid(row=0, column=0, sticky="w")
        
        # FIX: Increased wraplength to prevent wrapping on long words
        self.mood_catcher_label = tk.Label(mood_frame, text="", font=self.fonts["title"], justify="left", wraplength=self.config.SCREEN_WIDTH - 80)
        self.mood_catcher_label.grid(row=0, column=1, sticky="ew")
        # ------------------------------------
        
        self.mood_desc_label = tk.Label(self.content_frame, text="", font=self.fonts["body"], justify="center", wraplength=self.config.SCREEN_WIDTH - 20)
        self.mood_desc_label.pack(pady=(0, 10))
        
        self.setup_navigation()

    def go_back(self):
        pass # This screen doesn't go back