import pygame
import random


class Player(pygame.sprite.Sprite):
    def __init__(self, image, lanes, y):
        super().__init__()
        self.image = image
        self.lanes = lanes
        self.current_lane = len(lanes) // 2  # Start in the middle lane
        self.rect = self.image.get_rect(center=(lanes[self.current_lane], y))

    def move(self, direction):
        """Snaps the player to the left (-1) or right (+1) lane, clamped to range."""
        self.current_lane = max(0, min(len(self.lanes) - 1, self.current_lane + direction))
        self.rect.centerx = self.lanes[self.current_lane]


class FallingObject(pygame.sprite.Sprite):
    """Base class for Obstacles and Collectibles."""
    def __init__(self, image, lane_x, speed, kill_y):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(lane_x, -50))
        self.speed = speed
        self.kill_y = kill_y

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > self.kill_y:  # Fell off the bottom of the screen
            self.kill()


class EspressoExpress:
    """A 3-lane dodging game. Framework notes:

    All geometry is derived from the screen size, and every sprite falls back to
    a drawn colored block when its image asset is missing, so the game runs on
    any resolution and even with no art loaded.
    """

    NUM_LANES = 3

    # Fallback sprite sizes (match the manifest dimensions) used when an image
    # asset is missing. Themeable via the "colors" asset.
    PLAYER_FALLBACK_SIZE = (32, 40)
    OBSTACLE_FALLBACK_SIZE = (40, 40)
    COLLECTIBLE_FALLBACK_SIZE = (24, 24)

    HUD_HEIGHT = 26

    # Show the score in steps of this many points so it isn't constantly ticking.
    SCORE_DISPLAY_STEP = 50

    # Sugar reward and how long its floating "+N" popup lingers (ms).
    SUGAR_POINTS = 50
    POPUP_MS = 700

    # Stage boundaries: reach a new stage at 500, 1000, 1500, then every 2000.
    STAGE_EARLY_BOUNDARIES = (500, 1000, 1500)
    STAGE_INTERVAL = 2000
    STAGE_SPEED_BONUS = 1.5   # added to fall speed for each new stage
    STAGE_FLASH_MS = 1200     # how long the "STAGE n" banner shows (ms)

    def __init__(self, screen_width, screen_height, assets, callbacks):
        pygame.init()
        self.width = screen_width
        self.height = screen_height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Espresso Express')

        self.assets = assets
        self.callbacks = callbacks
        self.colors = assets.get('colors', {})
        self.font = pygame.font.SysFont(None, 36)
        self.title_font = pygame.font.SysFont(None, 34)
        self.hud_font = pygame.font.SysFont(None, 22)

        self.clock = pygame.time.Clock()
        self.score = 0
        self.stage = 1
        self.stage_flash_until = 0  # ms timestamp until which the stage banner shows
        self.popups = []            # floating "+N" score indicators
        self.game_speed = 5.0  # Starting fall speed

        # --- Geometry derived from the screen size (single source of truth) ---
        self.lanes = [int(self.width * (i * 2 + 1) / (self.NUM_LANES * 2))
                      for i in range(self.NUM_LANES)]
        self.lane_lines = [int(self.width * (i + 1) / self.NUM_LANES)
                           for i in range(self.NUM_LANES - 1)]
        self.player_y = self.height - 50

        # Sprite Groups
        self.all_sprites = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.collectibles = pygame.sprite.Group()

        player_image = self._sprite_image('player_bean', self.PLAYER_FALLBACK_SIZE, 'player', (240, 211, 153))
        self.player = Player(player_image, self.lanes, self.player_y)
        self.all_sprites.add(self.player)

        # Spawning timers
        self.spawn_timer = 0
        self.spawn_delay = 1500  # Milliseconds between spawns

    # --- Helpers -----------------------------------------------------------
    def _color(self, key, default):
        value = self.colors.get(key, default)
        return tuple(value) if isinstance(value, (list, tuple)) else default

    def _sprite_image(self, asset_key, fallback_size, color_key, default_color):
        """Returns the loaded image for an asset, or a solid colored block of
        the given size if the asset is missing. Guarantees a non-None surface."""
        image = self.assets.get(asset_key)
        if image is not None:
            return image
        surface = pygame.Surface(fallback_size, pygame.SRCALPHA)
        surface.fill(self._color(color_key, default_color))
        return surface

    def _reset_run(self):
        """Resets all per-run state so a fresh (or replayed) game starts clean."""
        self.score = 0
        self.stage = 1
        self.stage_flash_until = 0
        self.popups = []
        self.game_speed = 5.0
        self.spawn_delay = 1500
        self.spawn_timer = pygame.time.get_ticks()
        for sprite in list(self.obstacles) + list(self.collectibles):
            sprite.kill()
        self.player.current_lane = self.NUM_LANES // 2
        self.player.rect.centerx = self.lanes[self.player.current_lane]

    def _stepped_score(self, value):
        """Rounds a score down to the display step so the counter only changes
        every SCORE_DISPLAY_STEP points instead of every frame."""
        return value - (value % self.SCORE_DISPLAY_STEP)

    def _stage_for_score(self, score):
        """Stage number for a score: new stages at 500 / 1000 / 1500, then every
        STAGE_INTERVAL points beyond 1500."""
        stage = 1
        for boundary in self.STAGE_EARLY_BOUNDARIES:
            if score >= boundary:
                stage += 1
        last_early = self.STAGE_EARLY_BOUNDARIES[-1]
        if score >= last_early:
            stage += (score - last_early) // self.STAGE_INTERVAL
        return stage

    def _update_stage(self, now):
        """Recomputes the stage from the score. On advancing, arms the flash
        banner and ramps difficulty (per stage gained). Returns True if advanced."""
        new_stage = self._stage_for_score(self.score)
        if new_stage > self.stage:
            self.game_speed += self.STAGE_SPEED_BONUS * (new_stage - self.stage)
            self.stage = new_stage
            self.stage_flash_until = now + self.STAGE_FLASH_MS
            return True
        return False

    def _add_score_popup(self, x, y, amount, now):
        """Registers a floating '+amount' indicator at a screen position."""
        self.popups.append({'x': x, 'y': y, 'amount': amount, 'born': now})

    def spawn_entity(self):
        """Randomly chooses a lane and spawns an obstacle or a collectible."""
        chosen_lane_x = random.choice(self.lanes)

        # 75% chance for an obstacle, 25% chance for a sugar cube
        if random.random() > 0.25:
            obstacle_key = random.choice(['obstacle_milk', 'obstacle_tamper'])
            img = self._sprite_image(obstacle_key, self.OBSTACLE_FALLBACK_SIZE, 'obstacle', (200, 70, 50))
            obs = FallingObject(img, chosen_lane_x, self.game_speed, self.height)
            self.all_sprites.add(obs)
            self.obstacles.add(obs)
        else:
            img = self._sprite_image('collectible_sugar', self.COLLECTIBLE_FALLBACK_SIZE, 'collectible', (230, 230, 240))
            col = FallingObject(img, chosen_lane_x, self.game_speed, self.height)
            self.all_sprites.add(col)
            self.collectibles.add(col)

    # --- Drawing -----------------------------------------------------------
    def _draw_lane_dividers(self):
        line_color = self._color('lines', (60, 30, 15))
        for lx in self.lane_lines:
            pygame.draw.line(self.screen, line_color, (lx, 0), (lx, self.height), 2)

    def draw_background(self):
        """Draws the dark chute and the lane divider lines."""
        self.screen.fill(self._color('background', (20, 10, 5)))
        self._draw_lane_dividers()

    def draw_hud(self, best):
        """Draws the live score keeper as a translucent bar across the top."""
        bar = pygame.Surface((self.width, self.HUD_HEIGHT), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 120))
        self.screen.blit(bar, (0, 0))

        text_color = self._color('text', (255, 255, 255))
        y = (self.HUD_HEIGHT - self.hud_font.get_height()) // 2

        score_surf = self.hud_font.render(f"SCORE {self._stepped_score(self.score)}", True, text_color)
        self.screen.blit(score_surf, (6, y))

        stage_surf = self.hud_font.render(f"STAGE {self.stage}", True, text_color)
        self.screen.blit(stage_surf, (self.width // 2 - stage_surf.get_width() // 2, y))

        best_surf = self.hud_font.render(f"BEST {self._stepped_score(best)}", True, text_color)
        self.screen.blit(best_surf, (self.width - best_surf.get_width() - 6, y))

    def _draw_stage_flash(self):
        """A brief centered banner announcing a newly reached stage."""
        self.message(f"STAGE {self.stage}", y_offset=-40, font=self.font)

    def _draw_popups(self, now):
        """Draws and expires the floating '+N' score popups (they rise and fade)."""
        text_color = self._color('collectible', (230, 230, 240))
        survivors = []
        for popup in self.popups:
            age = now - popup['born']
            if age >= self.POPUP_MS:
                continue
            survivors.append(popup)
            progress = age / self.POPUP_MS
            surf = self.hud_font.render(f"+{popup['amount']}", True, text_color)
            surf.set_alpha(int(255 * (1 - progress)))
            draw_y = int(popup['y'] - progress * 24)  # drift upward as it fades
            self.screen.blit(surf, surf.get_rect(center=(popup['x'], draw_y)))
        self.popups = survivors

    def message(self, msg, y_offset=0, font=None):
        font = font or self.font
        text_color = self._color('text', (255, 255, 255))
        mesg = font.render(msg, True, text_color)
        text_rect = mesg.get_rect(center=(self.width / 2, self.height / 2 + y_offset))
        self.screen.blit(mesg, text_rect)

    def _draw_intro(self):
        self.screen.fill(self._color('background', (20, 10, 5)))
        self._draw_lane_dividers()
        self.message("ESPRESSO", y_offset=-100, font=self.title_font)
        self.message("EXPRESS", y_offset=-70, font=self.title_font)
        self.message("Dodge milk & tampers", y_offset=-20, font=self.hud_font)
        self.message("Grab sugar for +10", y_offset=5, font=self.hud_font)
        self.message("<  >   Change Lane", y_offset=40, font=self.hud_font)
        self.message("A = Start    B = Quit", y_offset=80, font=self.hud_font)
        pygame.display.update()

    def _draw_game_over(self, high_score_so_far):
        best = max(high_score_so_far, self.score)
        is_new_best = self.score > high_score_so_far and self.score > 0

        self.screen.fill(self._color('background', (0, 0, 0)))
        self.message("CRASHED!", y_offset=-60)
        if is_new_best:
            self.message("NEW BEST!", y_offset=-25, font=self.hud_font)
        self.message(f"Score: {self.score}", y_offset=5)
        self.message(f"Best: {best}", y_offset=38, font=self.hud_font)
        self.message("A = Play Again", y_offset=72, font=self.hud_font)
        self.message("B = Quit", y_offset=98, font=self.hud_font)
        pygame.display.update()

    # --- Screens / loop ----------------------------------------------------
    def _run_intro(self):
        """Shows the title/instructions screen. Returns True to start, False to quit."""
        while True:
            self._draw_intro()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        return True
                    if event.key in (pygame.K_b, pygame.K_q):
                        return False
            self.clock.tick(30)

    def game_loop(self, high_score_so_far=0, show_intro=True):
        self.callbacks['set_score_visibility'](True)
        self.callbacks['update_score'](0)

        if show_intro and not self._run_intro():
            self.callbacks['set_score_visibility'](False)
            pygame.quit()
            return high_score_so_far

        self._reset_run()

        game_over = False
        game_close = False

        while not game_over:

            # --- Game Over Screen ---
            while game_close:
                self._draw_game_over(high_score_so_far)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        game_over = True; game_close = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_b or event.key == pygame.K_q:
                            game_over = True; game_close = False
                        if event.key == pygame.K_a:
                            best = max(high_score_so_far, self.score)
                            return self.game_loop(high_score_so_far=best, show_intro=False)
                self.clock.tick(30)

            # --- Event Handling ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_over = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.player.move(-1)
                    elif event.key == pygame.K_RIGHT:
                        self.player.move(1)
                    elif event.key == pygame.K_q or event.key == pygame.K_b:
                        game_over = True

            # --- Spawning Logic ---
            now = pygame.time.get_ticks()
            if now - self.spawn_timer > self.spawn_delay:
                self.spawn_entity()
                self.spawn_timer = now

                # Slowly increase the speed and spawn rate over time!
                self.game_speed += 0.1
                self.spawn_delay = max(500, self.spawn_delay - 20)

            # --- Updates ---
            self.all_sprites.update()

            # --- Collisions ---
            # Hit an obstacle? Game over!
            if pygame.sprite.spritecollide(self.player, self.obstacles, False):
                game_close = True

            # Hit a sugar cube? Score points and pop a floating "+N".
            sugar_hits = pygame.sprite.spritecollide(self.player, self.collectibles, True)
            for hit in sugar_hits:
                self.score += self.SUGAR_POINTS
                self.callbacks['update_score'](self.score)
                self._add_score_popup(hit.rect.centerx, hit.rect.centery, self.SUGAR_POINTS, now)

            # Every frame you survive gives you 1 passive point
            if not game_close:
                self.score += 1
                if self.score % 10 == 0:  # Only update UI every 10 points to save CPU
                    self.callbacks['update_score'](self.score)

            # Advance the stage at the score boundaries and arm the flash banner.
            self._update_stage(now)

            # --- Drawing ---
            self.draw_background()
            self.all_sprites.draw(self.screen)
            self._draw_popups(now)
            self.draw_hud(max(high_score_so_far, self.score))
            if now < self.stage_flash_until:
                self._draw_stage_flash()
            pygame.display.update()

            self.clock.tick(60)

        self.callbacks['set_score_visibility'](False)
        pygame.quit()
        return max(high_score_so_far, self.score)
