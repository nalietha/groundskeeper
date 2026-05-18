class NavigationController:
    def __init__(self, root, config, view, display_service, loading_service, theme_service, 
                 affirmation_service, joke_service, updater, game_service, app):
        self.root = root
        self.config = config
        self.view = view
        self.display_service = display_service
        self.loading_service = loading_service
        self.theme_service = theme_service
        self.affirmation_service = affirmation_service
        self.joke_service = joke_service
        self.updater = updater
        self.game_service = game_service
        self.app = app
        self.turbo_mode = False

    def navigate_to(self, screen_name, setup_func=None):
        """The core routing engine. Handles loading screens and UI preparation."""
        active_theme_name = self.app.active_theme_name
        
        def _action():
            self.display_service.brighten_screen(active_theme_name)
            if setup_func:
                setup_func()
            self.view.show_screen(screen_name)
            self.root.deiconify()

        delay = 0 if self.turbo_mode else self.config.LATENCY_MS
        
        if delay > 0:
            active_theme = self.theme_service.get_theme(active_theme_name)
            loading_screen = self.view.screens.get('LoadingView')
            if loading_screen and active_theme and active_theme.loading_images:
                image_sequence = self.loading_service.get_image_sequence(
                    active_theme.loading_images, self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT
                )
                loading_screen.set_image_sequence(image_sequence)
            
            self.view.show_screen('LoadingView')
            self.root.after(delay, _action)
        else:
            _action()

    def toggle_turbo_mode(self):
        self.turbo_mode = not self.turbo_mode
        print(f"Turbo mode {'ENABLED' if self.turbo_mode else 'DISABLED'}")
        self.view.status_bar.set_turbo_visibility(self.turbo_mode)
        settings_screen = self.view.screens.get('SettingsView')
        if settings_screen:
            settings_screen.update_turbo_button_state(self.turbo_mode)

    # --- Screen-Specific Routes ---

    def show_standby_screen(self):
        self.view.show_screen('StandbyView')
        self.display_service.dim_screen(self.app.active_theme_name)

    def show_main_menu(self):
        self.navigate_to('MainMenuView')

    def show_affirmation(self):
        def _setup():
            affirmation = self.affirmation_service.get_daily_affirmation()
            self.view.screens['AffirmationView'].affirmation_label.config(text=affirmation)
        self.navigate_to('AffirmationView', _setup)

    def show_joke(self):
        def _setup():
            active_theme = self.theme_service.get_theme(self.app.active_theme_name)
            joke = self.joke_service.get_joke(theme=active_theme)
            self.view.screens['JokeView'].joke_label.config(text=joke)
        self.navigate_to('JokeView', _setup)

    def show_extras(self):
        self.navigate_to('ExtrasView')

    def show_qr_screen(self):
        self.navigate_to('QRCodeView')

    def show_settings(self):
        self.navigate_to('SettingsView')

    def show_debug_menu(self):
        self.navigate_to('DebugView')

    def show_updater(self):
        def _setup():
            update_screen = self.view.screens['UpdateView']
            current_version = self.updater.current_versions.get('system', '?.?.?')
            update_screen.current_version_label.config(text=f"v{current_version}")
            
            default_fg = update_screen.current_version_label.cget("foreground")
            update_screen.latest_version_label.config(text="Checking...", fg=default_fg)
            update_screen.status_label.config(text="Press the button to check for updates.")
            update_screen.update_button.config(text="Check for Updates", command=self.app.callbacks['check_for_updates'])
        self.navigate_to('UpdateView', _setup)

    def show_games(self):
        self.navigate_to('GamesView')

    def show_leaderboard(self):
        def _setup():
            games_screen = self.view.screens.get('GamesView')
            game_name = "All Games"
            if games_screen and hasattr(games_screen, 'carousel'):
                game_name = games_screen.carousel.get_current_item_key() or "All Games"
            
            scores = self.game_service.get_scores(game_name)
            self.view.screens['LeaderboardView'].display_scores(game_name, scores)
        self.navigate_to('LeaderboardView', _setup)

    def show_name_entry(self, game_name, score):
        def _setup():
            self.view.screens['NameEntryView'].set_score(game_name, score)
        self.navigate_to('NameEntryView', _setup)
        
    def show_splash_screen(self):
        self.view.show_screen('SplashView')
        self.root.after(3000, self.show_title_screen)

    def show_title_screen(self):
        self.view.show_screen('TitleView')