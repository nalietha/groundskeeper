# groundskeeper/views/standby.py
import tkinter as tk

class StandbyView(tk.Frame):
    def __init__(self, parent, callbacks, fonts, config, **kwargs):
        super().__init__(parent)
        self.callbacks = callbacks
        self.fonts = fonts
        self.config = config
        
        self.setup_ui()

    def setup_ui(self):
        # --- Main Content Labels ---
        self.theme_label = tk.Label(self, text="", font=self.fonts["subtitle"])
        self.theme_label.place(relx=0.5, rely=0.2, anchor="center")

        self.last_start_label = tk.Label(self, text="", font=self.fonts["small"])
        self.last_start_label.place(relx=0.5, rely=0.28, anchor="center")
        
        # --- Mood Section (Centering the Emoji and Text) ---
        mood_frame = tk.Frame(self)
        mood_frame.place(relx=0.5, rely=0.45, anchor="center")

        self.mood_emoji_label = tk.Label(mood_frame, text="", font=self.fonts["title"])
        self.mood_emoji_label.pack(side="left", padx=5)
        
        self.mood_catcher_label = tk.Label(mood_frame, text="", font=self.fonts["title"], justify="left", wraplength=self.config.SCREEN_WIDTH - 120)
        self.mood_catcher_label.pack(side="left")
        
        self.mood_desc_label = tk.Label(self, text="", font=self.fonts["body"], justify="center", wraplength=self.config.SCREEN_WIDTH - 20)
        self.mood_desc_label.place(relx=0.5, rely=0.65, anchor="center")
        
        # --- Bottom Buttons ---
        button_frame = tk.Frame(self)
        button_frame.place(relx=0, rely=1, relwidth=1, anchor="sw") # Place at the bottom
        button_frame.columnconfigure((0, 1), weight=1)

        menu_button = tk.Button(button_frame, text="Menu", font=self.fonts["button"], command=self.callbacks['show_main_menu'])
        menu_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        self.action_button = tk.Button(button_frame, text="Action", font=self.fonts["button"])
        self.action_button.grid(row=0, column=1, sticky="ew", padx=5, pady=5)