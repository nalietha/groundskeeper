import tkinter as tk
from datetime import datetime
import random

from core.theme_service import ThemeService
from core.mood_service import MoodService
from core.affirmation_service import AffirmationService

from models.mood import Mood
from views.view import View
from views.affirmation import AffirmationView
from configs.config import Config

class StandbyScreenApp:
    def __init__(self, root, config):
        self.root, self.config = root, config
        self.inactivity_job_id = None
        self.theme_service = ThemeService()
        self.affirmation_service = AffirmationService()
        if not self.theme_service.themes:
            raise RuntimeError("Could not load any themes.")
        self.action_start_time = None
        self.current_mood = Mood("Welcome!", "Select a theme and an action.", "👋")
        self.current_mood_tier_name = None
        self.current_theme = self.theme_service.get_theme(self.config.DEFAULT_THEME) or self.theme_service.get_all_themes()[0]
        callbacks = {'show_main_menu': self.show_main_menu, 'start_action': self.start_action, 'show_standby': self.show_standby_screen, 'show_games': self.show_games, 'show_leaderboard': self.show_leaderboard, 'show_affirmation': self.show_affirmation, 'show_joke': self.show_joke, 'get_all_themes': self.theme_service.get_all_themes, 'change_theme': self.change_theme}
        self.view = View(root, callbacks, config, [AffirmationView])
        self.show_standby_screen()
        self.periodic_check()

    def brighten_screen(self):
        if self.inactivity_job_id: self.root.after_cancel(self.inactivity_job_id)
        theme_colors = self.current_theme.colors
        self.view.set_theme_colors(theme_colors['bright_bg'], theme_colors['bright_fg'])
        self.inactivity_job_id = self.root.after(self.config.INACTIVITY_TIMEOUT_MS, self.dim_screen)

    def dim_screen(self):
        theme_colors = self.current_theme.colors
        self.view.set_theme_colors(theme_colors['dim_bg'], theme_colors['dim_fg'])
        self.inactivity_job_id = None

    def periodic_check(self):
        new_mood, new_tier_name = MoodService.get_mood_for_theme(self.current_theme, self.action_start_time)
        if new_tier_name != self.current_mood_tier_name:
            print(f"Mood tier changed from '{self.current_mood_tier_name}' to '{new_tier_name}'.")
            self.current_mood = new_mood
            self.current_mood_tier_name = new_tier_name
        self.update_standby_ui()
        self.root.after(60000, self.periodic_check)

    def update_standby_ui(self):
        standby_screen = self.view.screens['StandbyView']
        standby_screen.theme_label.config(text=f"Current: {self.current_theme.name}")
        time_format = "%H:%M" if self.config.USE_24H_CLOCK else "%I:%M %p"
        start_time_str = self.action_start_time.strftime(time_format).lstrip('0') if self.action_start_time else "Not started"
        standby_screen.last_start_label.config(text=f"{self.current_theme.start_phrase} {start_time_str}")
        standby_screen.mood_emoji_label.config(text=self.current_mood.emoji)
        standby_screen.mood_catcher_label.config(text=self.current_mood.catcher)
        standby_screen.mood_desc_label.config(text=self.current_mood.descriptor)
        standby_screen.action_button.config(text=self.current_theme.action_text)

    def change_theme(self, theme_name):
        new_theme = self.theme_service.get_theme(theme_name)
        if new_theme:
            self.current_theme = new_theme
            self.action_start_time = None
            self.current_mood_tier_name = None
            print(f"Theme changed to: {self.current_theme.name}")
            self.show_standby_screen()
        self.brighten_screen()

    def start_action(self):
        self.action_start_time = datetime.now()
        self.current_mood_tier_name = None
        print(f"Action '{self.current_theme.action_text}' started.")
        self.periodic_check()
        self.brighten_screen()

    def show_standby_screen(self):
        self.view.show_screen('StandbyView')
        self.update_standby_ui()
        self.dim_screen()

    def show_main_menu(self):
        self.brighten_screen()
        if self.inactivity_job_id: self.root.after_cancel(self.inactivity_job_id)
        self.view.show_screen('MainMenuView')

    def show_affirmation(self):
        self.brighten_screen()
        if self.inactivity_job_id: self.root.after_cancel(self.inactivity_job_id)
        affirmation_text = self.affirmation_service.get_daily_affirmation()
        affirmation_screen = self.view.screens['AffirmationView']
        affirmation_screen.affirmation_label.config(text=affirmation_text)
        self.view.show_screen('AffirmationView')

    def show_games(self): self.brighten_screen()
    def show_leaderboard(self): self.brighten_screen()
    def show_joke(self): self.brighten_screen()

if __name__ == "__main__":
    app_root = tk.Tk()
    app_config = Config()
    try:
        app = StandbyScreenApp(app_root, app_config)
        app_root.mainloop()
    except RuntimeError as e:
        print(e)
        app_root.destroy()