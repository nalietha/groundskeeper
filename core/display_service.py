class DisplayService:
    def __init__(self, root, config, theme_service, view):
        self.root = root
        self.config = config
        self.theme_service = theme_service
        self.view = view
        self.inactivity_job_id = None

    def brighten_screen(self, active_theme_name):
        """Brightens the screen and restarts the inactivity timer."""
        if self.inactivity_job_id: 
            self.root.after_cancel(self.inactivity_job_id)
            
        theme = self.theme_service.get_theme(active_theme_name)
        if theme:
            self.view.set_theme_colors(theme.colors['bright_bg'], theme.colors['bright_fg'])
            
        # Queue up the dimming function based on the config timeout
        self.inactivity_job_id = self.root.after(
            self.config.INACTIVITY_TIMEOUT_MS, 
            lambda: self.dim_screen(active_theme_name)
        )

    def dim_screen(self, active_theme_name):
        """Dims the screen."""
        theme = self.theme_service.get_theme(active_theme_name)
        if theme:
            self.view.set_theme_colors(theme.colors['dim_bg'], theme.colors['dim_fg'])
        self.inactivity_job_id = None