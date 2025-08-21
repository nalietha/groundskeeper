import tkinter as tk

class Screen(tk.Frame):
    def __init__(self, parent, callbacks, fonts, config, **kwargs):
        super().__init__(parent)
        self.callbacks = callbacks
        self.fonts = fonts
        self.config = config
        self.navigable_widgets = []
        self.current_focus_index = 0

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.content_frame = tk.Frame(self)
        self.content_frame.grid()
        
        self.setup_ui()
        self.setup_navigation()

    def setup_ui(self): 
        raise NotImplementedError

    def setup_navigation(self):
        """Prepares the screen's widgets for keyboard navigation."""
        for widget in self.navigable_widgets:
            widget.configure(takefocus=1, highlightthickness=2, highlightcolor="yellow", highlightbackground=widget.cget('bg'))
        
        if self.navigable_widgets:
            self.navigable_widgets[0].focus_set()

    def tkraise(self, aboveThis=None):
        super().tkraise(aboveThis)
        if self.navigable_widgets:
            self.navigable_widgets[self.current_focus_index].focus_set()

    def navigate(self, direction):
        if not self.navigable_widgets:
            return
        
        # Remove focus highlight from the old widget
        self.navigable_widgets[self.current_focus_index].config(relief=tk.RAISED)

        self.current_focus_index = (self.current_focus_index + direction) % len(self.navigable_widgets)
        
        # Set focus and highlight on the new widget
        new_widget = self.navigable_widgets[self.current_focus_index]
        new_widget.focus_set()
        new_widget.config(relief=tk.SUNKEN)


    def invoke_widget(self):
        if self.navigable_widgets:
            focused_widget = self.focus_get()
            if focused_widget in self.navigable_widgets:
                focused_widget.invoke()

    def go_back(self):
        if self.__class__.__name__ == 'MainMenuView':
            if 'show_standby' in self.callbacks:
                self.callbacks['show_standby']()
        else:
            if 'show_main_menu' in self.callbacks:
                self.callbacks['show_main_menu']()