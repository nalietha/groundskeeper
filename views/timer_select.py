import tkinter as tk
from .bases import MenuScreen

class TimerSelectView(MenuScreen):
    def setup_ui(self):
        self.title_label = tk.Label(self.content_frame, text="Select Time", font=self.fonts["title"])
        self.title_label.pack(pady=(20, 10))

        self.button_area = tk.Frame(self.content_frame)
        self.button_area.pack(expand=True, fill="both", padx=20)

    def tkraise(self, aboveThis=None):
        # 1. Clear out old buttons
        for widget in self.button_area.winfo_children():
            widget.destroy()
            
        # 2. Reset navigation list to just the "Back" button
        self.navigable_widgets = [self.navigable_widgets[-1]] 
        
        # 3. Get the theme to see its options
        theme_name = self.callbacks.get('get_active_theme_name', lambda: None)()
        theme = self.callbacks.get('get_theme', lambda x: None)(theme_name)
        
        # 4. Generate new buttons
        if theme and hasattr(theme, 'timer_options') and theme.timer_options:
            self.title_label.config(text=f"{theme.name} Options")
            for option in theme.timer_options:
                btn = tk.Button(
                    self.button_area,
                    text=option['label'],
                    font=self.fonts["button"],
                    command=lambda ms=option['ms']: self.callbacks['start_tracking_with_time'](theme.name, ms)
                )
                btn.pack(pady=10, fill="x")
                # Insert the new button into the navigation list before the "Back" button
                self.navigable_widgets.insert(-1, btn)
                
        self.setup_navigation()
        super().tkraise(aboveThis)