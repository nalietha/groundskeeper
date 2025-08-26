# groundskeeper.py
import tkinter as tk
from tkinter import messagebox
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
from core.gpio_service import GPIOService
from core.control_service import ControlService
from core.loading_service import LoadingService

from models.mood import Mood
from views.view import View
from views.affirmation import AffirmationView
from views.joke import JokeView
from views.update import UpdateView
from views.settings import SettingsView
from views.games import GamesView
from views.loading import LoadingView
from views.extras import ExtrasView
from configs.config import Config

class StandbyScreenApp:
    def __init__(self, root, config):
        self.root, self.config = root, config
        self.root.resizable(False, False)
        self.root.pack_propagate(False)
        self.inactivity_job_id = None
        self.theme_service = ThemeService()
        self.affirmation_service = AffirmationService()
        self.joke_service = JokeService()
        self.updater = UpdateService()
        self.game_service = GameService(config)
        self.state_file = "state.json"
        self.tracking_service = TrackingService(self.state_file, self.theme_service)
        self.gpio_service = GPIOService(config.GPIO_PINS)
        self.control_service = ControlService(root)
        self.loading_service = LoadingService()
        self.turbo_mode = False

        if not self.theme_service.themes:
            raise RuntimeError("Could not load any themes.")
        
        self.active_theme_name = self.config.DEFAULT_THEME

        callbacks = {
            'show_main_menu': self.show_main_menu, 
            'confirm_and_start_item': self.confirm_and_start_item, 
            'show_standby': self.show_standby_screen, 
            'show_extras': self.show_extras,
            'show_games': self.show_games, 
            'show_leaderboard': self.show_leaderboard, 
            'show_affirmation': self.show_affirmation, 
            'show_joke': self.show_joke, 
            'get_all_themes': self.theme_service.get_all_themes, 
            'check_for_updates': self.check_for_updates,
            'apply_updates': self.apply_updates,
            'get_current_version': lambda: self.updater.current_versions.get('system', '?.?.?'),
            'show_updater': self.show_updater,
            'show_settings': self.show_settings,
            'start_snake': self.start_snake,
            'set_active_theme': self.set_active_theme,
            'reset_all_items': self.reset_all_items,
            'toggle_turbo_mode': self.toggle_turbo_mode,
            'get_loading_service': lambda: self.loading_service
        }

        self.view = View(root, callbacks, config, self.control_service, [AffirmationView, JokeView, UpdateView, SettingsView, GamesView, LoadingView, ExtrasView])
        self.show_standby_screen()
        self.periodic_check()
        self.gpio_service.start()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.tracking_service._save_tracked_items()
        self.gpio_service.stop()
        self.root.destroy()
        
    def show_loading_and_run(self, target_function):
        """Displays the loading screen, then runs the target function after a delay."""
        delay = 0 if self.turbo_mode else self.config.LATENCY_MS
        
        if delay > 0:
            self.view.show_screen('LoadingView')
            self.root.after(delay, target_function)
        else:
            target_function()

    def toggle_turbo_mode(self):
        self.turbo_mode = not self.turbo_mode
        print(f"Turbo mode {'ENABLED' if self.turbo_mode else 'DISABLED'}")
        settings_screen = self.view.screens.get('SettingsView')
        if settings_screen:
            settings_screen.update_turbo_button_state(self.turbo_mode)

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
            start_time = datetime.fromisoformat(tracked_item['start_time']) if isinstance(tracked_item['start_time'], str) else tracked_item['start_time']
            mood, _ = MoodService.get_mood_for_theme(theme, start_time)
            start_time_str = start_time.strftime("%I:%M %p").lstrip('0')
        else:
            mood = Mood("Welcome!", "Start an item from the menu.", "👋")
            start_time_str = theme.not_started_text
            
        standby_screen.theme_label.config(text=f"Viewing: {theme.name}")
        standby_screen.last_start_label.config(text=f"{theme.start_phrase} {start_time_str}")
        standby_screen.mood_emoji_label.config(text=mood.emoji)
        standby_screen.mood_catcher_label.config(text=mood.catcher)
        standby_screen.mood_desc_label.config(text=mood.descriptor)
        standby_screen.action_button.config(text=theme.action_text, command=lambda: self.confirm_and_start_item(theme.name))

    def confirm_and_start_item(self, theme_name):
        is_tracked = any(item['theme_name'] == theme_name for item in self.tracking_service.get_tracked_items())
        
        proceed = True
        if is_tracked:
            proceed = messagebox.askyesno(
                title="Confirm Reset",
                message=f"A timer for '{theme_name}' is already running. Are you sure you want to reset it?"
            )
        
        if proceed:
            self.tracking_service.start_tracking_item(theme_name)
            self.active_theme_name = theme_name
            self.show_standby_screen()

    def set_active_theme(self, theme_name):
        self.active_theme_name = theme_name
        self.show_standby_screen()

    def reset_all_items(self):
        self.tracking_service.reset_all_items()
        self.active_theme_name = self.config.DEFAULT_THEME
        self.show_standby_screen()

    def show_standby_screen(self):
        self.view.show_screen('StandbyView')
        self.update_standby_ui()
        self.dim_screen()

    def show_main_menu(self):
        def _action():
            self.brighten_screen()
            self.view.show_screen('MainMenuView')
            self.root.deiconify()
        self.show_loading_and_run(_action)

    def show_affirmation(self):
        def _action():
            affirmation = self.affirmation_service.get_daily_affirmation()
            affirmation_screen = self.view.screens['AffirmationView']
            affirmation_screen.affirmation_label.config(text=affirmation)
            self.brighten_screen()
            self.view.show_screen('AffirmationView')
        self.show_loading_and_run(_action)

    def show_joke(self):
        def _action():
            active_theme = self.theme_service.get_theme(self.active_theme_name)
            joke = self.joke_service.get_joke(theme=active_theme)
            joke_screen = self.view.screens['JokeView']
            joke_screen.joke_label.config(text=joke)
            self.brighten_screen()
            self.view.show_screen('JokeView')
        self.show_loading_and_run(_action)
    
    def show_extras(self):
        def _action():
            self.brighten_screen()
            self.view.show_screen('ExtrasView')
        self.show_loading_and_run(_action) 
        
    def show_settings(self):
        def _action():
            self.brighten_screen()
            self.view.show_screen('SettingsView')
        self.show_loading_and_run(_action)

    def show_updater(self):
        def _action():
            self.brighten_screen()
            update_screen = self.view.screens['UpdateView']
            current_version = self.updater.current_versions.get('system', '?.?.?')
            update_screen.current_version_label.config(text=f"v{current_version}")
            
            default_fg = update_screen.current_version_label.cget("foreground")
            update_screen.latest_version_label.config(text="Checking...", fg=default_fg)
            
            update_screen.status_label.config(text="Press the button to check for updates.")
            update_screen.update_button.config(text="Check for Updates", command=self.check_for_updates)
            self.view.show_screen('UpdateView')
        self.show_loading_and_run(_action)

    def check_for_updates(self):
        update_screen = self.view.screens['UpdateView']
        update_screen.status_label.config(text="Checking GitHub for new releases...")
        self.root.update_idletasks() # Force UI to update

        updates = self.updater.check_for_updates()
        update_screen.update_status(updates)
        
    def apply_updates(self):
        update_screen = self.view.screens['UpdateView']
        if not update_screen.updates_available:
            update_screen.status_label.config(text="No updates to apply.")
            return

        system_update_version = update_screen.updates_available.get("system")
        if system_update_version:
            update_screen.status_label.config(text=f"Applying system update to v{system_update_version}...")
            self.root.update_idletasks()
            
            # In a real app, this is where you'd download and apply the update.
            # For now, we'll simulate it by just updating the version file.
            result_message = self.updater.apply_update("system", system_update_version)
            
            update_screen.status_label.config(text=result_message)
            # Update the current version label and disable the button
            update_screen.current_version_label.config(text=f"v{system_update_version}")
            update_screen.update_button.config(text="Update Applied", state="disabled")

    def show_games(self):
        def _action():
            self.brighten_screen()
            self.view.show_screen('GamesView')
        self.show_loading_and_run(_action)
        
    def show_leaderboard(self):
        def _action():
            self.brighten_screen()
            print("Showing leaderboard...")
        self.show_loading_and_run(_action)

    def start_snake(self):
        self.control_service.deactivate_all_controls()
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