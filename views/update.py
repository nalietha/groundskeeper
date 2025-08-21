import tkinter as tk
from views.screen import Screen

class UpdateView(Screen):
    def setup_ui(self):
        self.title_label = tk.Label(self, text="Application Updater", font=self.fonts["subtitle"])
        self.title_label.pack(pady=(20, 10))

        self.status_label = tk.Label(self, text="Click below to check for updates.", font=self.fonts["body"], wraplength=280)
        self.status_label.pack(expand=True, padx=20)

        self.update_button = tk.Button(self, text="Check for Updates", font=self.fonts["button"], command=self.callbacks['check_for_updates'])
        self.update_button.pack(pady=10)

        back_button = tk.Button(self, text="Back to Menu", font=self.fonts["button"], command=self.callbacks['show_main_menu'])
        back_button.pack(pady=(0, 20))