# groundskeeper/views/carousel.py
import tkinter as tk

class Carousel(tk.Frame):
    def __init__(self, parent, items, fonts, config):
        super().__init__(parent, borderwidth=0, highlightthickness=0, bg=parent.cget("bg"))
        
        self.items = items
        self.fonts = fonts
        self.config = config
        self.current_index = 0

        # Start with a small requested size, let the packer expand it to fit the viewport exactly
        self.canvas = tk.Canvas(self, width=150, height=150, bg=parent.cget("bg"), highlightthickness=0)
        self.canvas.pack(expand=True, fill="both")

        # Dummy label to prevent crashes if external views try to configure self.carousel.label
        self.label = tk.Label(self) 

        # Bind to the configure event so it redraws whenever the window/frame resizes
        self.canvas.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        """Called automatically when the canvas is drawn or resized."""
        self.update_display()

    def update_display(self):
        self.canvas.delete("all")
        
        # Dynamically get width and height from the canvas itself!
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        # Fallbacks just in case it fires before fully rendering
        center_x = canvas_w / 2 if canvas_w > 10 else 100
        center_y = canvas_h / 2 if canvas_h > 10 else 100

        if not self.items:
            return

        def draw_placeholder(index, y_pos, width, height, color, font_key):
            if index is None: return
            text = self.items[index]['text']
            
            # Calculate coordinates for the box
            x1 = center_x - (width / 2)
            y1 = y_pos - (height / 2)
            x2 = center_x + (width / 2)
            y2 = y_pos + (height / 2)
            
            # Draw the light border box
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=2, fill="#1a0f0a")
            
            # Draw the text centered inside the box
            self.canvas.create_text(
                center_x, y_pos, 
                text=text, 
                fill=color, 
                font=self.fonts[font_key], 
                justify="center", 
                width=width-10
            )

        num_items = len(self.items)
        
        # Calculate indices for the vertical scroll
        prev_index = (self.current_index - 1 + num_items) % num_items if num_items > 1 else None
        next_index = (self.current_index + 1) % num_items if num_items > 1 else None
        
        # Prevent drawing duplicates on top/bottom if there are exactly 2 items
        if num_items == 2:
            prev_index = None

        # --- Sizing tuned specifically to fit the mechanical viewport ---
        spacing = 55
        
        # Draw Top Card (Previous)
        if prev_index is not None:
            draw_placeholder(prev_index, center_y - spacing, 130, 35, "#a67c52", "body")
            
        # Draw Bottom Card (Next)
        if next_index is not None:
            draw_placeholder(next_index, center_y + spacing, 130, 35, "#a67c52", "body")
            
        # Draw Center Card (Active)
        draw_placeholder(self.current_index, center_y, 170, 50, "#d4a373", "subtitle")

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
        if self.items:
            return self.items[self.current_index].get('key')
        return None