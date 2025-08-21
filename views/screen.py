import tkinter as tk

class Screen(tk.Frame):
    def __init__(self, parent, callbacks, fonts, config, **kwargs):
        super().__init__(parent)
        self.callbacks = callbacks
        self.fonts = fonts
        self.config = config

        # Configure the base screen to center its content
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # This content_frame will hold all widgets and be centered
        # All subclasses should place their widgets inside this frame
        self.content_frame = tk.Frame(self)
        self.content_frame.grid()
        
        self.setup_ui()
        
    def setup_ui(self): 
        # Subclasses will implement this and add widgets to self.content_frame
        raise NotImplementedError