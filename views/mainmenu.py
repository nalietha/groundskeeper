import tkinter as tk
from views.screen import Screen

class MainMenuView(Screen):
    def setup_ui(self):
        # All widgets are now placed in self.content_frame for centering
        menu_label = tk.Label(self.content_frame, text="Main Menu", font=self.fonts["title"])
        menu_label.pack(pady=(10, 5))
        
        theme_frame = tk.LabelFrame(self.content_frame, text="Select Item to View", font=self.fonts["small"], padx=10, pady=5)
        theme_frame.pack(pady=5, padx=10, fill="x")
        all_themes = self.callbacks['get_all_themes']()
        for theme in all_themes:
            btn = tk.Button(
                theme_frame, 
                text=theme.name, 
                font=self.fonts["small"], 
                command=lambda t=theme.name: self.callbacks['set_active_theme'](t)
            )
            btn.pack(side="top", expand=True, fill="x", pady=2)
            
        menu_button_frame = tk.Frame(self.content_frame)
        menu_button_frame.pack(expand=True, fill="both", padx=10, pady=5)
        menu_button_frame.columnconfigure((0, 1), weight=1)
        menu_button_frame.rowconfigure((0, 1), weight=1)
        
        buttons = {
            "Games": self.callbacks['show_games'], 
            "Affirmation": self.callbacks['show_affirmation'], 
            "Joke": self.callbacks['show_joke'],
            "Settings": self.callbacks['show_settings']
        }
        
        row, col = 0, 0
        for text, command in buttons.items():
            btn = tk.Button(menu_button_frame, text=text, font=self.fonts["body"], command=command)
            btn.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
            col = (col + 1) % 2
            if col == 0: row += 1
            
        back_button = tk.Button(self.content_frame, text="Back to Standby", font=self.fonts["small"], command=self.callbacks['show_standby'])
        back_button.pack(pady=(0, 10))