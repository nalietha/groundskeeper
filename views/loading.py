# groundskeeper/views/loading.py
import tkinter as tk
from views.screen import Screen

class LoadingView(Screen):
    def setup_ui(self):
        self.image_label = tk.Label(self.content_frame)
        self.image_label.pack(pady=20)
        self.animation_job = None
        self.image_sequence = []
        self.current_image_index = 0

    def setup_navigation(self):
        # No navigation on the loading screen
        self.navigable_widgets = []

    def set_image_sequence(self, image_sequence):
        """Sets the images to be used for the loading animation."""
        self.image_sequence = image_sequence
        self.current_image_index = 0

    def stop_loading_animation(self):
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None
    
    def animate(self):
        if not self.image_sequence:
            return

        image = self.image_sequence[self.current_image_index]
        self.image_label.config(image=image)
        
        self.current_image_index = (self.current_image_index + 1) % len(self.image_sequence)
        
        self.animation_job = self.after(self.config.LOADING_IMAGE_INTERVAL_MS, self.animate)

    def tkraise(self, aboveThis=None):
        # The main app now loads the images. We just need to start the animation.
        super().tkraise(aboveThis)
        self.stop_loading_animation() # Ensure any old animation is stopped
        self.animate()

    def grid_remove(self):
        self.stop_loading_animation()
        super().grid_remove()