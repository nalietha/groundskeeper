# groundskeeper.py
import tkinter as tk
from tkinter import messagebox
import threading

# --- Config & Models ---
from configs.config import Config

# --- Core Services ---
from core.theme_service import ThemeService
from core.affirmation_service import AffirmationService
from core.joke_service import JokeService
from core.update_service import UpdateService
from core.game_service import GameService
from core.tracking_service import TrackingService
from core.gpio_service import GPIOService
from core.control_service import ControlService
from core.input_service import InputService
from core.loading_service import LoadingService
from core.notification_service import NotificationService
from core.webapp_service import WebAppService
from core.newsletter_service import NewsletterService
from core.display_service import DisplayService
from core.navigation_controller import NavigationController

# --- Views ---
from views.view import View
from views.affirmation import AffirmationView
from views.joke import JokeView
from views.update import UpdateView
from views.settings import SettingsView
from views.games import GamesView
from views.loading import LoadingView
from views.extras import ExtrasView
from views.leaderboard import LeaderboardView
from views.name_entry import NameEntryView
from views.splash import SplashView
from views.title import TitleView
from views.qr_code_view import QRCodeView
from views.debug import DebugView
from views.timer_select import TimerSelectView
from views.standby import StandbyView
from views.mainmenu import MainMenuView


class GroundskeeperApp:
    def __init__(self, root, config):
        self.root, self.config = root, config
        self.root.resizable(False, False)
        self.root.pack_propagate(False)
        self.active_theme_name = self.config.DEFAULT_THEME

        # --- 1. Initialize Core Services ---
        self.theme_service = ThemeService()
        self.affirmation_service = AffirmationService()
        self.joke_service = JokeService()
        self.updater = UpdateService()
        self.game_service = GameService(config)
        self.loading_service = LoadingService()
        self.newsletter_service = NewsletterService(
            self.joke_service, self.affirmation_service, self.game_service,
            deck_file="data/newsletter_deck.json"
        )
        self.notification_service = NotificationService(getattr(self.config, 'EMAIL_CONFIG', {}))
        
        self.state_file = "data/state.json"
        self.tracking_service = TrackingService(
            self.state_file, self.theme_service, self.joke_service, 
            self.affirmation_service, self.newsletter_service
        )
        self.gpio_service = GPIOService(config.GPIO_PINS)
        self.gpio_service.start()
        self.control_service = ControlService(self)
        self.input_service = InputService(self.root, self.control_service)
        self.input_service.start()

        # --- 2. Build the Callbacks Dictionary ---
        self.callbacks = {
            'get_all_themes': self.theme_service.get_all_themes, 
            'get_theme': self.theme_service.get_theme,
            'get_active_theme_name': lambda: self.active_theme_name,
            'check_for_updates': self.check_for_updates,
            'apply_updates': self.apply_updates,
            'get_current_version': lambda: self.updater.current_versions.get('system', '?.?.?'),
            'get_available_games': self.game_service.get_available_games, 
            'start_game': self.start_game,
            'set_active_theme': self.set_active_theme,
            'save_score': self.game_service.save_score,
            'reset_all_items': self.reset_all_items,
            'get_loading_service': lambda: self.loading_service,
            'get_webapp_ip': lambda: self.webapp_service.get_local_ip() if hasattr(self, 'webapp_service') else "127.0.0.1",
            'test_email': self.notification_service.send_test_email,
            'test_email_started': self.test_email_started,
            'test_email_ready': self.test_email_ready,
            'update_score': lambda score: self.view.update_score(score),
            'set_score_visibility': lambda is_visible: self.view.set_score_visibility(is_visible),
            'request_standby_refresh': self.update_standby_ui,
            'start_tracking_with_time': self._actually_start_item,
            'confirm_and_start_item': self.confirm_and_start_item,
        }

        # --- 3. Initialize Views & Controllers ---
        self.view = View(root, self.callbacks, config, self.control_service, [
            SplashView, TitleView, AffirmationView, JokeView, UpdateView, 
            SettingsView, GamesView, LoadingView, ExtrasView, LeaderboardView, 
            NameEntryView, QRCodeView, DebugView, TimerSelectView,
            StandbyView, MainMenuView
        ])
        
        self.display_service = DisplayService(self.root, self.config, self.theme_service, self.view)
        
        self.router = NavigationController(
            self.root, self.config, self.view, self.display_service, self.loading_service,
            self.theme_service, self.affirmation_service, self.joke_service, self.updater,
            self.game_service, self
        )

        # --- 4. Populate Callbacks (Part 2: Navigation) ---
        self.callbacks.update({
            'show_main_menu': self.router.show_main_menu,
            'show_title_screen': self.router.show_title_screen, 
            'show_standby': self.router.show_standby_screen, 
            'show_extras': self.router.show_extras,
            'show_games': self.router.show_games, 
            'show_leaderboard': self.router.show_leaderboard, 
            'show_affirmation': self.router.show_affirmation, 
            'show_joke': self.router.show_joke, 
            'show_updater': self.router.show_updater,
            'show_settings': self.router.show_settings,
            'show_name_entry': self.router.show_name_entry,
            'show_qr_screen': self.router.show_qr_screen,
            'show_debug_menu': self.router.show_debug_menu,
            'toggle_turbo_mode': self.router.toggle_turbo_mode,
        })

        # --- 5. Web App & Threads ---
        self.webapp_service = WebAppService(self.notification_service, self.theme_service, self.tracking_service)
        self.webapp_service.start()
        
        self.update_thread = threading.Thread(target=self._background_update_check, daemon=True)
        self.update_thread.start()
        
        # --- 6. Boot App ---
        self.periodic_check()
        self.router.show_splash_screen()

    def on_closing(self):
        self.tracking_service._save_tracked_items()
        self.input_service.stop()
        self.gpio_service.stop()
        self.root.destroy()

    def toggle_turbo_mode(self):
        """Exposed on the app because ControlService reaches for it by name."""
        self.router.toggle_turbo_mode()

    def periodic_check(self):
        self.update_standby_ui()
        self.tracking_service.check_notifications(self.notification_service)
        self.root.after(60000, self.periodic_check)
        
    def _background_update_check(self):
        import time
        while True:
            updates = self.updater.check_for_updates()
            if updates:
                self.root.after(0, lambda: self.view.status_bar.set_update_visibility(True))
            else:
                self.root.after(0, lambda: self.view.status_bar.set_update_visibility(False))
            time.sleep(3600) 

    def update_standby_ui(self):
        standby_screen = self.view.screens.get('StandbyView')
        if not standby_screen: return
        
        tracked_item = next((item for item in self.tracking_service.get_tracked_items() if item['theme_name'] == self.active_theme_name), None)
        theme = self.theme_service.get_theme(self.active_theme_name)
        standby_screen.refresh_ui(theme, tracked_item)

    def confirm_and_start_item(self, theme_name):
        is_tracked = any(item['theme_name'] == theme_name for item in self.tracking_service.get_tracked_items())
        
        proceed = True
        if is_tracked:
            proceed = messagebox.askyesno(title="Confirm Reset", message=f"A timer for '{theme_name}' is already running. Are you sure you want to reset it?")
        
        if proceed:
            theme = self.theme_service.get_theme(theme_name)
            if hasattr(theme, 'timer_options') and theme.timer_options:
                self.active_theme_name = theme_name
                self.view.show_screen('TimerSelectView')
            else:
                self._actually_start_item(theme_name, None)

    def _actually_start_item(self, theme_name, custom_timer_ms):
        self.tracking_service.start_tracking_item(theme_name, custom_timer_ms)
        self.active_theme_name = theme_name
        self.router.show_standby_screen()

    def set_active_theme(self, theme_name):
        self.active_theme_name = theme_name
        self.router.show_standby_screen()

    def reset_all_items(self):
        self.tracking_service.reset_all_items()
        self.active_theme_name = self.config.DEFAULT_THEME
        self.router.show_standby_screen()
    
    def check_for_updates(self):
        update_screen = self.view.screens['UpdateView']
        update_screen.status_label.config(text="Checking GitHub for new releases...")
        self.root.update_idletasks()
        updates = self.updater.check_for_updates()
        update_screen.update_status(updates)
        
    def apply_updates(self):
        update_screen = self.view.screens['UpdateView']
        if not update_screen.updates_available: return

        system_update_version = update_screen.updates_available.get("system")
        if system_update_version:
            update_screen.status_label.config(text=f"Applying system update to v{system_update_version}...")
            self.root.update_idletasks()
            result_message = self.updater.apply_update("system", system_update_version)
            update_screen.status_label.config(text=result_message)
            update_screen.current_version_label.config(text=f"v{system_update_version}")
            update_screen.update_button.config(text="Update Applied", state="disabled")

    def start_game(self, game_name):
        self.control_service.deactivate_all_controls()
        self.root.iconify()
        active_theme = self.theme_service.get_theme(self.active_theme_name)
        score = self.game_service.start_game(game_name, active_theme, self.callbacks)
        self.root.deiconify()

        if self.game_service.is_high_score(game_name, score):
            self.router.show_name_entry(game_name, score)
        else:
            self.router.show_leaderboard()

# region Debug Actions
    def _send_test_email(self, main_message, label):
        theme = self.theme_service.get_theme(self.active_theme_name)
        context = {"theme_name": theme.name, "main_message": main_message.format(name=theme.name)}
        if hasattr(self.tracking_service, '_get_newsletter_content'):
            context.update(self.tracking_service._get_newsletter_content(theme))

        try:
            self.notification_service.send_notification(theme.name, context, test_mode=True)
            return True, f"'{label}' preview sent to your email!"
        except Exception as e:
            return False, f"Failed: {str(e)}"

    def test_email_started(self):
        return self._send_test_email("[TEST] {name} has just been started!", "Started")

    def test_email_ready(self):
        return self._send_test_email("[TEST] {name} is now ready! Enjoy!", "Ready")
# endregion

if __name__ == "__main__":
    app_root = tk.Tk()
    app_config = Config()
    try:
        app = GroundskeeperApp(app_root, app_config)
        app_root.protocol("WM_DELETE_WINDOW", app.on_closing)
        app_root.mainloop()
    except RuntimeError as e:
        print(e)
        app_root.destroy()