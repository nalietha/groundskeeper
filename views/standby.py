import tkinter as tk
from PIL import Image, ImageTk
from datetime import date, timedelta
from models.mood import Mood
from core.mood_service import MoodService
from .bases import TwoButtonScreen

class StandbyView(TwoButtonScreen):
    def setup_ui(self):
        # Expanded the canvas height slightly to give the layout more breathing room
        self.canvas = tk.Canvas(self.content_frame, width=240, height=250, borderwidth=0, highlightthickness=0)
        self.canvas.pack(expand=True, fill="both")

        # 1. Background Layer
        self.bg_image_id = self.canvas.create_image(120, 125, image=None)
        self.current_bg = None 
        
        # 2. Top Text (Y-coordinates adjusted for breathing room)
        self.theme_text_shadow = self.canvas.create_text(122, 22, text="", font=self.fonts["subtitle"], justify="center", fill="black")
        self.theme_text = self.canvas.create_text(120, 20, text="", font=self.fonts["subtitle"], justify="center")
        
        self.start_text_shadow = self.canvas.create_text(122, 47, text="", font=self.fonts["small"], justify="center", fill="black")
        self.start_text = self.canvas.create_text(120, 45, text="", font=self.fonts["small"], justify="center")
        
        # 3. The Themeable Symbol Layer (Dead center)
        self.symbol_image_id = self.canvas.create_image(120, 110, image=None)
        self.current_symbol = None
        
        # 4. Bottom Text
        self.catcher_text_shadow = self.canvas.create_text(122, 172, text="", font=self.fonts["subtitle"], width=200, justify="center", fill="black")
        self.catcher_text = self.canvas.create_text(120, 170, text="", font=self.fonts["subtitle"], width=200, justify="center")
        
        self.desc_text_shadow = self.canvas.create_text(122, 217, text="", font=self.fonts["body"], width=220, justify="center", fill="black")
        self.desc_text = self.canvas.create_text(120, 215, text="", font=self.fonts["body"], width=220, justify="center")

        self.setup_navigation()

    def refresh_ui(self, theme, tracked_item):
        if tracked_item:
            start_time = tracked_item['start_time']
            mood, _ = MoodService.get_mood_for_theme(theme, start_time)
            
            today = date.today()
            yesterday = today - timedelta(days=1)

            if start_time.date() == today:
                time_format = start_time.strftime("%I:%M %p").lstrip('0')
                start_time_str = f"Today, {time_format}"
            elif start_time.date() == yesterday:
                time_format = start_time.strftime("%I:%M %p").lstrip('0')
                start_time_str = f"Yesterday, {time_format}"
            else:
                start_time_str = start_time.strftime("%b %d, %I:%M %p")
        else:
            mood = Mood("Welcome!", "Start an item from the menu.")
            start_time_str = theme.not_started_text
            
        # --- Handle Background Image ---
        if hasattr(theme, 'standby_bg') and theme.standby_bg:
            try:
                img = Image.open(theme.standby_bg)
                img = img.resize((240, 250), Image.Resampling.LANCZOS)
                self.current_bg = ImageTk.PhotoImage(img)
                self.canvas.itemconfig(self.bg_image_id, image=self.current_bg)
            except Exception as e:
                print(f"Error loading standby bg: {e}")
                self.canvas.itemconfig(self.bg_image_id, image="")
                self.canvas.configure(bg=theme.colors.get('dim_bg', 'black'))
        else:
            self.canvas.itemconfig(self.bg_image_id, image="")
            self.canvas.configure(bg=theme.colors.get('dim_bg', 'black'))

        # --- Handle Symbol Image ---
        if hasattr(theme, 'symbol') and theme.symbol:
            try:
                sym_img = Image.open(theme.symbol)
                sym_img.thumbnail((72, 72), Image.Resampling.LANCZOS) # Bumped up to 72px so it commands the space
                self.current_symbol = ImageTk.PhotoImage(sym_img)
                self.canvas.itemconfig(self.symbol_image_id, image=self.current_symbol)
            except Exception as e:
                print(f"Error loading symbol: {e}")
                self.canvas.itemconfig(self.symbol_image_id, image="")
        else:
            self.canvas.itemconfig(self.symbol_image_id, image="")

        # --- Handle Text (Updating Shadow AND Foreground) ---
        fg_color = theme.colors.get('bright_fg', 'white')
        
        # System Title
        sys_str = f"SYS: {theme.name.upper()}"
        self.canvas.itemconfig(self.theme_text_shadow, text=sys_str)
        self.canvas.itemconfig(self.theme_text, text=sys_str, fill=fg_color)
        
        # Start Time
        start_str = f"{theme.start_phrase.upper()} {start_time_str}"
        self.canvas.itemconfig(self.start_text_shadow, text=start_str)
        self.canvas.itemconfig(self.start_text, text=start_str, fill=fg_color)
        
        # Mood Catcher
        self.canvas.itemconfig(self.catcher_text_shadow, text=mood.catcher)
        self.canvas.itemconfig(self.catcher_text, text=mood.catcher, fill=fg_color)
        
        # Mood Descriptor
        self.canvas.itemconfig(self.desc_text_shadow, text=mood.descriptor)
        self.canvas.itemconfig(self.desc_text, text=mood.descriptor, fill=fg_color)
        
        self.action_button.config(text=theme.action_text, command=lambda: self.callbacks['confirm_and_start_item'](theme.name))

    def tkraise(self, aboveThis=None):
        super().tkraise(aboveThis)
        if 'request_standby_refresh' in self.callbacks:
            self.callbacks['request_standby_refresh']()

    def go_back(self):
        pass