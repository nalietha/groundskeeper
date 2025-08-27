# groundskeeper/views/update.py
import tkinter as tk
from .bases import MenuScreen

class UpdateView(MenuScreen):
    # Define a static, theme-independent color scheme for the updater
    UPDATER_COLORS = {
        "bg": "#1c1c1c",        # A dark charcoal background
        "fg": "#e0e0e0",        # A bright, off-white foreground
        "red": "#ff5555",       # A vibrant red for alerts
        "green": "#50fa7b",     # A vibrant green for success
    }

    def setup_ui(self):
        self.updates_available = None

        title_label = tk.Label(self.content_frame, text="Application Updater", font=self.fonts["title"])
        title_label.pack(pady=(20, 10))

        # --- Version Display ---
        version_frame = tk.Frame(self.content_frame)
        version_frame.pack(pady=10)

        current_label = tk.Label(version_frame, text="Current Version:", font=self.fonts["body"])
        current_label.grid(row=0, column=0, sticky="w", padx=5)
        self.current_version_label = tk.Label(version_frame, text="v?.?.?", font=self.fonts["body"])
        self.current_version_label.grid(row=0, column=1, sticky="w")

        latest_label = tk.Label(version_frame, text="Latest Version:", font=self.fonts["body"])
        latest_label.grid(row=1, column=0, sticky="w", padx=5)
        self.latest_version_label = tk.Label(version_frame, text="Checking...", font=self.fonts["body"])
        self.latest_version_label.grid(row=1, column=1, sticky="w")
        # ------------------------

        self.status_label = tk.Label(self.content_frame, text="Press the button to check for updates.", font=self.fonts["small"], wraplength=self.config.SCREEN_WIDTH - 20)
        self.status_label.pack(expand=True, pady=10)

        self.update_button = tk.Button(self.content_frame, text="Check for Updates", font=self.fonts["button"], command=self.callbacks['check_for_updates'])
        self.update_button.pack(pady=10)

        self.navigable_widgets = [self.update_button] + self.navigable_widgets
        self.setup_navigation()

    def _apply_colors_recursive(self, widget, bg, fg):
        """Recursively applies the static updater colors to this screen."""
        try:
            widget.configure(bg=bg, highlightbackground=bg)
            if isinstance(widget, (tk.Label, tk.Button, tk.LabelFrame)):
                widget.configure(fg=fg)
                if isinstance(widget, tk.Button):
                    widget.configure(highlightbackground=bg)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._apply_colors_recursive(child, bg, fg)

    def tkraise(self, aboveThis=None):
        """Overrides the default tkraise to apply our independent theme."""
        # Apply our independent colors every time this screen is shown
        self._apply_colors_recursive(self, self.UPDATER_COLORS["bg"], self.UPDATER_COLORS["fg"])
        # Now call the original tkraise from the base class
        super().tkraise(aboveThis)

    def update_status(self, updates):
        """Updates the labels and buttons based on the check results."""
        self.updates_available = updates
        latest_system_version = self.updates_available.get("system") if self.updates_available else self.callbacks['get_current_version']()

        if self.updates_available and "system" in self.updates_available:
            # Update is available: use the updater's RED
            self.latest_version_label.config(text=f"v{latest_system_version}", fg=self.UPDATER_COLORS["red"])
            self.status_label.config(text="A new version is available!")
            self.update_button.config(text="Apply Update", command=self.callbacks['apply_updates'])
        elif latest_system_version:
            # Already up to date: use the updater's GREEN
            self.latest_version_label.config(text=f"v{latest_system_version}", fg=self.UPDATER_COLORS["green"])
            self.status_label.config(text="You are on the latest version.")
            self.update_button.config(text="Check Again", command=self.callbacks['check_for_updates'])
        else:
            # Error case: use the updater's RED
            self.latest_version_label.config(text="Error", fg=self.UPDATER_COLORS["red"])
            self.status_label.config(text="Could not check for updates.")
            self.update_button.config(text="Try Again", command=self.callbacks['check_for_updates'])