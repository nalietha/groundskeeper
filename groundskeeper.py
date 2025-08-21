import tkinter as tk
from datetime import datetime
import json
import os

from core.theme_service import ThemeService
from core.mood_service import MoodService
from core.affirmation_service import AffirmationService
from core.joke_service import JokeService
from core.update_service import UpdateService
from core.game_service import GameService
from core.tracking_service import TrackingService

from models.mood import Mood
from views.view import View
from views.affirmation import AffirmationView
from views.joke import JokeView
from views.update import UpdateView
from views.settings import SettingsView
from views.games import GamesView
from configs.config import Config

class StandbyScreenApp:
    def __init__(self, root, config):
        self.root, self.config = root, config
        self.root.resizable(False, False)
        self.inactivity_job_id = None
        self.theme_service = ThemeService()
        self.affirmation_service = AffirmationService()
        self.joke_service = JokeService()
        self.updater = UpdateService()
        self.game_service = GameService(config)
        self.state_file = "state.json"
        self.tracking_service = TrackingService(self.state_file, self.theme_service)

        if not self.theme_service.themes:
            raise RuntimeError("Could not load any themes.")
        
        self.active_theme_name = self.config.DEFAULT_THEME

        callbacks = {
            'show_main_menu': self.show_main_menu, 
            'start_new_item': self.start_new_item, 
            'show_standby': self.show_standby_screen, 
            'show_games': self.show_games, 
            'show_leaderboard': self.show_leaderboard, 
            'show_affirmation': self.show_affirmation, 
            'show_joke': self.show_joke, 
            'get_all_themes': self.theme_service.get_all_themes, 
            'check_for_updates': self.check_for_updates,
            'show_updater': self.show_updater,
            'show_settings': self.show_settings,
            'start_snake': self.start_snake,
            'set_active_theme': self.set_active_theme
        }
        self.view = View(root, callbacks, config, [AffirmationView, JokeView, UpdateView, SettingsView, GamesView])
        self.show_standby_screen()
        self.periodic_check()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.tracking_service._save_tracked_items()
        self.root.destroy()

    def brighten_screen(self):
        if self.inactivity_job_id: self.root.after_cancel(self.inactivity_job_id)
        active_theme = self.theme_service.get_theme(self.active_theme_name)
        theme_colors = active_theme.colors
        self.view.set_theme_colors(theme_colors['bright_bg'], theme_colors['bright_fg'])
        self.inactivity_job_id = self.root.after(self.config.INACTIVITY_TIMEOUT_MS, self.dim_screen)

    def dim_screen(self):
        active_theme = self.theme_service.get_theme(self.active_theme_name)
        theme_colors = active_theme.colors
        self.view.set_theme_colors(theme_colors['dim_bg'], theme_colors['dim_fg'])
        self.inactivity_job_id = None

    def periodic_check(self):
        self.update_standby_ui()
        self.root.after(60000, self.periodic_check)

    def update_standby_ui(self):
        standby_screen = self.view.screens['StandbyView']
        tracked_item = next((item for item in self.tracking_service.get_tracked_items() if item['theme_name'] == self.active_theme_name), None)
        theme = self.theme_service.get_theme(self.active_theme_name)

        if tracked_item:
            mood, _ = MoodService.get_mood_for_theme(theme, tracked_item['start_time'])
            start_time_str = tracked_item['start_time'].strftime("%I:%M %p").lstrip('0')
        else:
            mood = Mood("Welcome!", "Start an item from the menu.", "👋")
            start_time_str = "Not started"
            
        standby_screen.theme_label.config(text=f"Viewing: {theme.name}")
        standby_screen.last_start_label.config(text=f"{theme.start_phrase} {start_time_str}")
        standby_screen.mood_emoji_label.config(text=mood.emoji)
        standby_screen.mood_catcher_label.config(text=mood.catcher)
        standby_screen.mood_desc_label.config(text=mood.descriptor)
        standby_screen.action_button.config(text=theme.action_text, command=lambda: self.start_new_item(theme.name))


    def start_new_item(self, theme_name):
        self.tracking_service.start_tracking_item(theme_name)
        self.active_theme_name = theme_name
        self.show_standby_screen()

    def set_active_theme(self, theme_name):
        self.active_theme_name = theme_name
        self.show_standby_screen()

    def show_standby_screen(self):
        self.view.show_screen('StandbyView')
        self.update_standby_ui()
        self.dim_screen()

    def show_main_menu(self):
        self.brighten_screen()
        if self.inactivity_job_id: self.root.after_cancel(self.inactivity_job_id)
        self.view.show_screen('MainMenuView')
        self.root.deiconify()

    def show_affirmation(self):
        self.brighten_screen()
        affirmation_text = self.affirmation_service.get_daily_affirmation()
        affirmation_screen = self.view.screens['AffirmationView']
        affirmation_screen.affirmation_label.config(text=affirmation_text)
        self.view.show_screen('AffirmationView')

    def show_joke(self):
        self.brighten_screen()
        joke_text = self.joke_service.get_joke()
        joke_screen = self.view.screens['JokeView']
        joke_screen.joke_label.config(text=joke_text)
        self.view.show_screen('JokeView')
        
    def show_updater(self):
        self.brighten_screen()
        self.view.show_screen('UpdateView')
        
    def show_settings(self):
        self.brighten_screen()
        self.view.show_screen('SettingsView')

    def check_for_updates(self):
        # ... (rest of the function is unchanged)
        pass

    def show_games(self):
        self.brighten_screen()
        self.view.show_screen('GamesView')
        
    def show_leaderboard(self):
        self.brighten_screen()
        print("Showing leaderboard...")

    def start_snake(self):
        self.root.iconify()
        active_theme = self.theme_service.get_theme(self.active_theme_name)
        self.game_service.start_snake(active_theme)
        self.show_main_menu()

if __name__ == "__main__":
    app_root = tk.Tk()
    app_config = Config()
    try:
        app = StandbyScreenApp(app_root, app_config)
        app_root.mainloop()
    except RuntimeError as e:
        print(e)
        app_root.destroy()