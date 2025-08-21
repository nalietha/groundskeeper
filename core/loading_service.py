import os
import random
from PIL import Image, ImageTk

class LoadingService:
    def __init__(self, loading_folder="resources/loading"):
        self.image_paths = []
        if os.path.isdir(loading_folder):
            self.image_paths = [
                os.path.join(loading_folder, f) for f in os.listdir(loading_folder)
                if f.endswith(('.png', '.jpg', '.jpeg'))
            ]
        
        if not self.image_paths:
            print("Warning: No loading images found.")

    def get_random_loading_image(self, width, height):
        if not self.image_paths:
            return None
        
        path = random.choice(self.image_paths)
        try:
            img = Image.open(path)
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error loading image {path}: {e}")
            return None