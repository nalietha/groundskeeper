import pygame
import random

class Player(pygame.sprite.Sprite):
    def __init__(self, assets):
        super().__init__()
        self.image = assets.get('player_bean')
        self.rect = self.image.get_rect()
        
        # The exact X-coordinates of the 3 lanes on a 240px wide screen
        self.lanes = [40, 120, 200]
        self.current_lane = 1 # Start in the middle
        self.rect.center = (self.lanes[self.current_lane], 270) # Stay near the bottom

    def move(self, direction):
        """Snaps the player to the left (-1) or right (+1) lane."""
        self.current_lane += direction
        # Keep the player inside the 3 lanes
        if self.current_lane < 0: self.current_lane = 0
        if self.current_lane > 2: self.current_lane = 2
        
        self.rect.centerx = self.lanes[self.current_lane]

class FallingObject(pygame.sprite.Sprite):
    """Base class for Obstacles and Collectibles"""
    def __init__(self, image, lane_x, speed):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(lane_x, -50))
        self.speed = speed

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > 320: # If it falls off the bottom of the screen
            self.kill()

class EspressoExpress:
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
        
        self.clock = pygame.time.Clock()
        self.score = 0
        self.game_speed = 5.0 # Starting fall speed
        
        # Sprite Groups
        self.all_sprites = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.collectibles = pygame.sprite.Group()
        
        self.player = Player(assets)
        self.all_sprites.add(self.player)
        
        # Spawning timers
        self.spawn_timer = 0
        self.spawn_delay = 1500 # Milliseconds between spawns

    def spawn_entity(self):
        """Randomly chooses a lane and spawns an obstacle or a collectible."""
        lanes = [40, 120, 200]
        chosen_lane = random.choice(lanes)
        
        # 75% chance for an obstacle, 25% chance for a sugar cube
        if random.random() > 0.25:
            # Pick randomly between milk or tamper
            img = random.choice([self.assets.get('obstacle_milk'), self.assets.get('obstacle_tamper')])
            obs = FallingObject(img, chosen_lane, self.game_speed)
            self.all_sprites.add(obs)
            self.obstacles.add(obs)
        else:
            img = self.assets.get('collectible_sugar')
            col = FallingObject(img, chosen_lane, self.game_speed)
            self.all_sprites.add(col)
            self.collectibles.add(col)

    def draw_background(self):
        """Draws the dark chute and the lane divider lines."""
        self.screen.fill(self.colors.get('background', (20, 10, 5)))
        line_color = self.colors.get('lines', (60, 30, 15))
        
        # Draw two vertical lines to separate the 3 lanes
        pygame.draw.line(self.screen, line_color, (80, 0), (80, self.height), 2)
        pygame.draw.line(self.screen, line_color, (160, 0), (160, self.height), 2)

    def message(self, msg, y_offset=0):
        text_color = self.colors.get('text', (255, 255, 255))
        mesg = self.font.render(msg, True, text_color)
        text_rect = mesg.get_rect(center=(self.width / 2, self.height / 2 + y_offset))
        self.screen.blit(mesg, text_rect)

    def game_loop(self, high_score_so_far=0):
        self.callbacks['set_score_visibility'](True)
        self.callbacks['update_score'](0)
        
        game_over = False
        game_close = False

        while not game_over:
            
            # --- Game Over Screen ---
            while game_close:
                self.screen.fill(self.colors.get('background', (0,0,0)))
                self.message("CRASHED!", y_offset=-40)
                self.message(f"Score: {self.score}", y_offset=0)
                self.message("A = Play Again", y_offset=50)
                self.message("B = Quit", y_offset=80)
                pygame.display.update()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        game_over = True; game_close = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_b or event.key == pygame.K_q:
                            game_over = True; game_close = False
                        if event.key == pygame.K_a:
                            return self.game_loop(high_score_so_far=max(high_score_so_far, self.score))

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
                
            # Hit a sugar cube? +10 points!
            sugar_hits = pygame.sprite.spritecollide(self.player, self.collectibles, True)
            for hit in sugar_hits:
                self.score += 10
                self.callbacks['update_score'](self.score)

            # Every frame you survive gives you 1 passive point
            if not game_close:
                self.score += 1
                if self.score % 10 == 0: # Only update UI every 10 points to save CPU
                    self.callbacks['update_score'](self.score)

            # --- Drawing ---
            self.draw_background()
            self.all_sprites.draw(self.screen)
            pygame.display.update()
            
            self.clock.tick(60)

        self.callbacks['set_score_visibility'](False)
        pygame.quit()
        return max(high_score_so_far, self.score)