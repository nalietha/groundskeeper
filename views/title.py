# groundskeeper/views/title.py
import tkinter as tk
from .bases import BaseScreen
from .image_utils import GIFImage

class TitleView(BaseScreen):
    def __init__(self, parent, callbacks, fonts, config, **kwargs):
        super().__init__(parent, callbacks, fonts, config, **kwargs)
        self.setup_ui()
        
    def setup_ui(self):
        self.configure(bg="black")
        self.animation_job = None

        try:
            self.gif = GIFImage("assets/branding/press_start.gif")
            self.gif_label = tk.Label(self, image=self.gif.get_frame(), bg="black")
            self.gif_label.pack(expand=True)
            self.animate()
        except Exception as e:
            print(f"Could not load title screen GIF: {e}")
            fallback_label = tk.Label(self, text="Press Start", font=("Press Start 2P", 20), fg="white", bg="black")
            fallback_label.pack(expand=True)

    def on_select(self):
        # The title/attract screen: any select press enters the main menu.
        self.callbacks['show_main_menu']()

    def animate(self):
        """Cycles through the GIF frames."""
        frame = self.gif.get_frame()
        self.gif_label.config(image=frame)
        self.animation_job = self.after(self.gif.delay, self.animate)

    def tkraise(self, aboveThis=None):
        super().tkraise(aboveThis)
        # Restart animation when the screen is shown
        if hasattr(self, 'gif'):
            self.animate()

    def grid_remove(self):
        if self.animation_job:
            self.after_cancel(self.animation_job)
        super().grid_remove()