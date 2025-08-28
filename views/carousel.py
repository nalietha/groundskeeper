# groundskeeper/views/carousel.py
import tkinter as tk
from PIL import Image, ImageTk

class Carousel(tk.Frame):
    def __init__(self, parent, items, fonts, config):
        super().__init__(parent, borderwidth=0, highlightthickness=0, bg=parent.cget("bg"))
        
        self.items = items
        self.fonts = fonts
        self.config = config
        self.current_index = 0
        self.photo_images = {} # Cache for images

        screen_w = self.config.SCREEN_WIDTH
        # Increase the height of the carousel area to accommodate larger images
        screen_h = 200 
        
        self.canvas = tk.Canvas(self, width=screen_w, height=screen_h, bg=parent.cget("bg"), highlightthickness=0)
        self.canvas.pack()

        self.label = tk.Label(self, text="", font=self.fonts["subtitle"], bg=parent.cget("bg"))
        self.label.pack(pady=5)

        self._load_images()
        self.update_display()

    def _load_images(self):
        """Pre-load and resize all images to avoid lag during navigation."""
        for i, item in enumerate(self.items):
            try:
                with Image.open(item['image_path']) as img:
                    # --- FIX: Increase the size of the card images ---
                    large_img = img.copy()
                    large_img.thumbnail((180, 135), Image.Resampling.LANCZOS)
                    
                    small_img = img.copy()
                    small_img.thumbnail((120, 90), Image.Resampling.LANCZOS)
                    # -------------------------------------------------
                    
                    self.photo_images[i] = {
                        'large': ImageTk.PhotoImage(large_img),
                        'small': ImageTk.PhotoImage(small_img)
                    }
            except Exception as e:
                print(f"Error loading image {item['image_path']}: {e}")
                self.photo_images[i] = None

    def update_display(self):
        self.canvas.delete("all")
        center_y = self.winfo_height() / 2 if self.winfo_height() > 1 else 100

        # --- FIX: Adjust positioning for the "tucked under" effect ---
        # Draw side cards first
        prev_index = (self.current_index - 1 + len(self.items)) % len(self.items)
        prev_item_images = self.photo_images.get(prev_index)
        if prev_item_images:
            prev_photo = prev_item_images.get('small')
            if prev_photo:
                # Move the left card closer to the center
                self.canvas.create_image(60, center_y, image=prev_photo, tags="prev")

        next_index = (self.current_index + 1) % len(self.items)
        next_item_images = self.photo_images.get(next_index)
        if next_item_images:
            next_photo = next_item_images.get('small')
            if next_photo:
                # Move the right card closer to the center
                self.canvas.create_image(self.config.SCREEN_WIDTH - 60, center_y, image=next_photo, tags="next")

        # Draw center card last so it's on top
        center_item_images = self.photo_images.get(self.current_index)
        if center_item_images:
            center_photo = center_item_images.get('large')
            if center_photo:
                self.canvas.create_image(self.config.SCREEN_WIDTH / 2, center_y, image=center_photo, tags="center")
        # -----------------------------------------------------------
            
        self.label.config(text=self.items[self.current_index]['text'])

    def go_next(self):
        self.current_index = (self.current_index + 1) % len(self.items)
        self.update_display()

    def go_previous(self):
        self.current_index = (self.current_index - 1 + len(self.items)) % len(self.items)
        self.update_display()
        
    def get_current_callback(self):
        if self.items:
            return self.items[self.current_index].get('callback')
        return None

    def get_current_item_key(self):
        """Returns the unique key of the item currently in the center."""
        if self.items:
            return self.items[self.current_index].get('key')
        return None
