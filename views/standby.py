import tkinter as tk

from views.screen import Screen


class StandbyView(Screen):
    def setup_ui(self):
        self.theme_label = tk.Label(self, text="", font=self.fonts["subtitle"])
        self.theme_label.pack(pady=(5, 0))
        self.last_start_label = tk.Label(self, text="", font=self.fonts["small"])
        self.last_start_label.pack()
        
        # Frame for emoji and catcher text
        mood_frame = tk.Frame(self)
        mood_frame.pack(expand=True, padx=10)
        
        self.mood_emoji_label = tk.Label(mood_frame, text="", font=self.fonts["title"])
        self.mood_emoji_label.pack(side="left", padx=(0, 10))
        
        self.mood_catcher_label = tk.Label(mood_frame, text="", font=self.fonts["title"], justify="left", wraplength=250)
        self.mood_catcher_label.pack(side="left")
        
        self.mood_desc_label = tk.Label(self, text="", font=self.fonts["body"], justify="center", wraplength=300)
        self.mood_desc_label.pack(expand=True, side="top", pady=(0, 10))
        
        button_frame = tk.Frame(self)
        button_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        button_frame.columnconfigure((0, 1), weight=1)
        start_button = tk.Button(button_frame, text="Menu", font=self.fonts["button"], command=self.callbacks['show_main_menu'])
        start_button.grid(row=0, column=0, sticky="ew", padx=5)
        self.action_button = tk.Button(button_frame, text="Action", font=self.fonts["button"], command=self.callbacks['start_action'])
        self.action_button.grid(row=0, column=1, sticky="ew", padx=5)
