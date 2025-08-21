import tkinter as tk
from views.screen import Screen

class LoadingView(Screen):
    def setup_ui(self):
        self.image_label = tk.Label(self.content_frame)
        self.image_label.pack(pady=20)
        self.image_update_job = None

    def start_loading_animation(self, loading_service):
        self.update_loading_image(loading_service)

    def stop_loading_animation(self):
        if self.image_update_job:
            self.after_cancel(self.image_update_job)
            self.image_update_job = None

    def update_loading_image(self, loading_service):
        new_image = loading_service.get_random_loading_image(self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT)
        if new_image:
            self.image_label.config(image=new_image)
            # Keep a reference to the image to prevent garbage collection
            self.image_label.image = new_image
        
        self.image_update_job = self.after(self.config.LOADING_IMAGE_INTERVAL_MS, lambda: self.update_loading_image(loading_service))

    def tkraise(self, aboveThis=None):
        super().tkraise(aboveThis)
        loading_service = self.callbacks.get('get_loading_service')()
        if loading_service:
            self.start_loading_animation(loading_service)

    def grid_remove(self):
        self.stop_loading_animation()
        super().grid_remove()