# groundskeeper/views/splash.py
import tkinter as tk
from PIL import Image, ImageTk
from .bases import BaseScreen

class SplashView(BaseScreen):
    def __init__(self, parent, callbacks, fonts, config, **kwargs):
        super().__init__(parent, callbacks, fonts, config, **kwargs)
        self.setup_ui()

    def setup_ui(self):
        self.configure(bg="black") # A black background for the splash
        try:
            with Image.open("assets/branding/medusa_studio.png") as img:
                # Calculate a new height to maintain the aspect ratio
                width, height = img.size
                scale_factor = self.config.SCREEN_WIDTH / width
                new_height = int(height * scale_factor)
                
                resized_img = img.resize((self.config.SCREEN_WIDTH, new_height), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(resized_img)
            logo_label = tk.Label(self, image=self.logo_photo, bg="black")
            logo_label.pack(expand=True)
            
        except Exception as e:
            print(f"Could not load splash screen logo: {e}")
            # Fallback text if image fails
            fallback_label = tk.Label(self, text="Medusa Studio", font=("Press Start 2P", 20), fg="white", bg="black")
            fallback_label.pack(expand=True)