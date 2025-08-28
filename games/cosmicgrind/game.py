# groundskeeper/games/cosmic_grind/game.py
import pygame
import random

class CosmicGrind:
    def __init__(self, screen_width, screen_height, assets):
        pygame.init()
        self.width = screen_width
        self.height = screen_height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Cosmic Grind: Brew-tal Arcade Action!')

        # Load assets from the manifest
        self.assets = assets
        self.colors = assets.get('colors', {})
        self.player_ship_img = assets.get('player_ship')
        self.enemy1_img = assets.get('enemy_ship_1')
        self.enemy2_img = assets.get('enemy_ship_2')
        self.player_bullet_img = assets.get('player_bullet')
        self.enemy_bullet_img = assets.get('enemy_bullet')

        self.clock = pygame.time.Clock()
        self.font_style = pygame.font.SysFont(None, 35)
        self.score = 0

    def game_loop(self):
        game_over = False
        
        # Game objects setup (player, enemies, etc.)
        player_x = self.width / 2
        player_y = self.height - 60
        player_speed = 5

        while not game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_over = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q: # Quit
                        game_over = True

            # --- Game Logic Here ---
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                player_x -= player_speed
            if keys[pygame.K_RIGHT]:
                player_x += player_speed

            # Drawing
            self.screen.fill(self.colors.get('background', (15, 15, 25)))
            
            # Draw player ship
            if self.player_ship_img:
                self.screen.blit(self.player_ship_img, (player_x, player_y))
            else: # Fallback if image is missing
                pygame.draw.rect(self.screen, (0, 255, 0), [player_x, player_y, 32, 32])

            pygame.display.update()
            self.clock.tick(60) # 60 FPS

        pygame.quit()
        return self.score

    def message(self, msg, color, y_offset=0):
        mesg = self.font_style.render(msg, True, color)
        text_rect = mesg.get_rect(center=(self.width / 2, self.height / 2 + y_offset))
        self.screen.blit(mesg, text_rect)