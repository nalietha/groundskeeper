import tkinter as tk
from views.screen import Screen

class SettingsView(Screen):
    def setup_ui(self):
        title_label = tk.Label(self.content_frame, text="Settings", font=self.fonts["title"])
        title_label.pack(pady=(20, 10))

        button_area = tk.Frame(self.content_frame)
        button_area.pack(expand=True, padx=20)

        update_button = tk.Button(button_area, text="Check for Updates", font=self.fonts["button"], command=self.callbacks['show_updater'])
        update_button.pack(pady=10, fill="x")

        reset_button = tk.Button(button_area, text="Reset All Timers", font=self.fonts["button"], command=self.callbacks['reset_all_items'])
        reset_button.pack(pady=10, fill="x")

        self.turbo_button = tk.Button(button_area, text="Turbo: OFF", font=self.fonts["button"], command=self.callbacks['toggle_turbo_mode'])
        self.turbo_button.pack(pady=10, fill="x")

        self.button_frame.columnconfigure(0, weight=1)
        back_button = tk.Button(self.button_frame, text="<font size='5'>◄</font> Back to Menu", font=self.fonts["button"], command=self.callbacks['show_main_menu'])
        back_button.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.navigable_widgets = [update_button, reset_button, self.turbo_button, back_button]

    def update_turbo_button_state(self, is_on):
        if is_on:
            self.turbo_button.config(text="Turbo: ON", relief=tk.SUNKEN)
        else:
            self.turbo_button.config(text="Turbo: OFF", relief=tk.RAISED)