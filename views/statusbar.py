# groundskeeper/views/statusbar.py
import tkinter as tk
from PIL import Image, ImageTk
from datetime import datetime

class StatusBar(tk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent, borderwidth=0, highlightthickness=0)
        self.config = config

        # --- Layout Configuration ---
        self.columnconfigure(0, weight=1) # Left side (clock)
        self.columnconfigure(1, weight=1) # Right side (icons)

        # --- Clock Label ---
        self.clock_label = tk.Label(self, text="", font=("Press Start 2P", 8))
        self.clock_label.grid(row=0, column=0, sticky="w", padx=5)

        # --- Game Score Label ---
        self.score_label = tk.Label(self, text="", font=("Press Start 2P", 8))
        self.score_label.grid(row=0, column=1, sticky="w")
        

        # --- Icons Frame ---
        icons_frame = tk.Frame(self)
        icons_frame.grid(row=0, column=1, sticky="e", padx=5)

        # --- Turbo Mode Icon ---
        try:
            self.turbo_icon_image = ImageTk.PhotoImage(Image.open("assets/icons/turbo_on.png").resize((16, 16)))
            self.turbo_icon_label = tk.Label(icons_frame, image=self.turbo_icon_image)
            # The label is created but not shown initially. We'll use pack_forget() to hide it.
            self.turbo_icon_label.pack()
            self.turbo_icon_label.pack_forget()
        except Exception as e:
            print(f"Could not load turbo icon: {e}")
            self.turbo_icon_label = None # Handle missing icon gracefully

        self.update_clock()

    def update_clock(self):
        """Updates the time display every second."""
        now = datetime.now()
        time_format = "%I:%M %p" if not self.config.USE_24H_CLOCK else "%H:%M"
        time_str = now.strftime(time_format).lstrip('0')
        self.clock_label.config(text=time_str)
        self.after(1000, self.update_clock)

    def set_turbo_visibility(self, is_on):
        """Shows or hides the turbo mode icon."""
        if not self.turbo_icon_label:
            return
            
        if is_on:
            self.turbo_icon_label.pack(side="right")
        else:
            self.turbo_icon_label.pack_forget()
    
    def set_score_visibility(self, is_visible):
        """Shows or hides the score label."""
        if is_visible:
            self.score_label.grid()
        else:
            self.score_label.grid_remove()

    def update_score(self, score):
        """Updates the score display."""
        self.score_label.config(text=f"Score: {score}")