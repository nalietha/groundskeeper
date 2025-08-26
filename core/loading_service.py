import os
import random
from PIL import Image, ImageTk

class LoadingService:
    def __init__(self, loading_folder="resources/loading"):
        self.image_sets = []
        if os.path.isdir(loading_folder):
            for item in os.listdir(loading_folder):
                item_path = os.path.join(loading_folder, item)
                if os.path.isdir(item_path):
                    images = sorted([
                        os.path.join(item_path, f) for f in os.listdir(item_path)
                        if f.endswith(('.png', '.jpg', '.jpeg'))
                    ])
                    if images:
                        self.image_sets.append(images)
        
        if not self.image_sets:
            print("Warning: No loading image sets found.")

    def get_random_image_sequence(self, width, height):
        if not self.image_sets:
            return []
        
        image_path_sequence = random.choice(self.image_sets)
        loaded_images = []
        for path in image_path_sequence:
            try:
                img = Image.open(path)
                img = img.resize((width, height), Image.Resampling.LANCZOS)
                loaded_images.append(ImageTk.PhotoImage(img))
            except Exception as e:
                print(f"Error loading image {path}: {e}")
        
        return loaded_images