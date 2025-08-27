# groundskeeper/core/loading_service.py
import os
import random
from PIL import Image, ImageTk

class LoadingService:
    def __init__(self):
        # No longer scans a global folder
        pass

    def get_image_sequence(self, image_paths, width, height):
        """Processes a list of image paths into a Tkinter-compatible image sequence."""
        if not image_paths:
            return []
        
        loaded_images = []
        for path in image_paths:
            try:
                with Image.open(path) as img:
                    img_resized = img.resize((width, height), Image.Resampling.LANCZOS)
                    loaded_images.append(ImageTk.PhotoImage(img_resized))
            except Exception as e:
                print(f"Error loading image {path}: {e}")
        
        return loaded_images