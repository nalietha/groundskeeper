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

    def start_loading_animation(self):
        loading_service = self.callbacks.get('get_loading_service')()
        if loading_service:
            self.image_sequence = loading_service.get_random_image_sequence(
                self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT
            )
            self.current_image_index = 0
            self.animate()

    def stop_loading_animation(self):
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None
        self.image_sequence = []

    def animate(self):
        if not self.image_sequence:
            return

        image = self.image_sequence[self.current_image_index]
        self.image_label.config(image=image)
        
        self.current_image_index = (self.current_image_index + 1) % len(self.image_sequence)
        
        self.animation_job = self.after(self.config.LOADING_IMAGE_INTERVAL_MS, self.animate)

    def tkraise(self, aboveThis=None):
        super().tkraise(aboveThis)
        self.start_loading_animation()

    def grid_remove(self):
        self.stop_loading_animation()
        super().grid_remove()