# groundskeeper/views/name_entry.py
import tkinter as tk
from .bases import BaseScreen

class NameEntryView(BaseScreen):
    def __init__(self, parent, callbacks, fonts, config, **kwargs):
        super().__init__(parent, callbacks, fonts, config, **kwargs)
        # This call ensures all widgets are created before anything else happens.
        self.setup_ui()
    # ---------------------
    def setup_ui(self):
        self.game_name = ""
        self.score = 0
        
        # --- Arcade Input Logic ---
        self.character_set = "ABCDEFGHIJKLMNOPQRSTUVWXYZ_!?."
        self.char_indices = [0, 0, 0] # Index for 'A', 'A', 'A'
        self.cursor_pos = 0
        # ------------------------

        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0); self.grid_rowconfigure(2, weight=1)
        
        content_frame = tk.Frame(self)
        content_frame.grid(row=1, column=0)

        title_label = tk.Label(content_frame, text="New High Score!", font=self.fonts["title"])
        title_label.pack(pady=(20, 10))
        self.score_label = tk.Label(content_frame, text="Score: 0", font=self.fonts["subtitle"])
        self.score_label.pack(pady=10)

        # --- Character Display ---
        entry_frame = tk.Frame(content_frame)
        entry_frame.pack(pady=20)
        self.char_labels = []
        for i in range(3):
            label = tk.Label(entry_frame, text="A", font=("Courier", 40, "bold"), width=2)
            label.pack(side="left", padx=5)
            self.char_labels.append(label)
        # -------------------------
        
        # No button bar is needed for this screen
        self.navigable_widgets = [] # Controls are handled directly
        self.update_highlight()

    def set_score(self, game_name, score):
        self.game_name = game_name
        self.score = score
        self.score_label.config(text=f"Score: {self.score}")
        self.char_indices = [0, 0, 0]
        self.cursor_pos = 0
        self.update_labels()
        self.update_highlight()

    def change_char(self, direction):
        """Changes the character at the current cursor position."""
        current_char_index = self.char_indices[self.cursor_pos]
        new_index = (current_char_index + direction + len(self.character_set)) % len(self.character_set)
        self.char_indices[self.cursor_pos] = new_index
        self.update_labels()

    def move_cursor(self, direction):
        """Moves the highlight to the next or previous character."""
        self.cursor_pos = (self.cursor_pos + direction + 3) % 3
        self.update_highlight()

    def advance_or_submit(self):
        """Advances the cursor or submits the score."""
        if self.cursor_pos < 2:
            self.move_cursor(1)
        else:
            name = "".join([self.character_set[i] for i in self.char_indices])
            self.callbacks['save_score'](self.game_name, name, self.score)
            self.callbacks['show_leaderboard']()
            
    def update_labels(self):
        """Updates the text of the character labels."""
        for i, label in enumerate(self.char_labels):
            char_index = self.char_indices[i]
            label.config(text=self.character_set[char_index])
            
    def update_highlight(self):
        """Updates which character is currently highlighted as active."""
        for i, label in enumerate(self.char_labels):
            if i == self.cursor_pos:
                label.config(relief="solid", borderwidth=2)
            else:
                label.config(relief="flat", borderwidth=0)

    def go_back(self):
        # Back button moves the cursor left, or exits if at the first char
        if self.cursor_pos > 0:
            self.move_cursor(-1)
        else:
            self.callbacks['show_leaderboard']() # Exit without saving