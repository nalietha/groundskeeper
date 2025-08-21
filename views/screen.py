import tkinter as tk

class Screen(tk.Frame):
    def __init__(self, parent, callbacks, fonts, **kwargs):
        super().__init__(parent)
        self.callbacks = callbacks
        self.fonts = fonts
        self.setup_ui()
    def setup_ui(self): raise NotImplementedError