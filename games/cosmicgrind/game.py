# groundskeeper/games/cosmic_grind/game.py
import pygame
import random
import time
import math

class Player(pygame.sprite.Sprite):
    def __init__(self, screen_width, screen_height, assets):
        super().__init__()
        self.image = assets.get('player_ship')
        self.rect = self.image.get_rect(center=(screen_width / 2, screen_height - 50))
        self.screen_width = screen_width
        self.speed = 5
        self.last_shot = 0
        self.shoot_delay = 300  # milliseconds
        self.assets = assets

    def update(self, all_sprites, bullets):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed

        # Keep player on the screen
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > self.screen_width:
            self.rect.right = self.screen_width

        # Shooting
        now = pygame.time.get_ticks()
        if keys[pygame.K_a] and now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            bullet = Bullet(self.rect.centerx, self.rect.top, -10, self.assets)
            all_sprites.add(bullet)
            bullets.add(bullet)
        
        if keys[pygame.K_b]:
            pass


class Enemy(pygame.sprite.Sprite):
    def __init__(self, assets, target_x, target_y):
        super().__init__()
        self.image = random.choice([assets.get('enemy_ship_1'), assets.get('enemy_ship_2')])
        self.rect = self.image.get_rect(center=(-50, -50)) # Start off-screen
        
        self.state = 'ENTERING'
        self.target_x = target_x
        self.target_y = target_y
        self.formation_speed = 4
        self.dive_speed = 5

    def update(self, *args):
        if self.state == 'ENTERING':
            dx, dy = self.target_x - self.rect.centerx, self.target_y - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > self.formation_speed:
                self.rect.centerx += dx / dist * self.formation_speed
                self.rect.centery += dy / dist * self.formation_speed
            else:
                self.rect.center = (self.target_x, self.target_y)
                self.state = 'FORMATION'

        elif self.state == 'DIVING':
            self.rect.y += self.dive_speed
            if self.rect.top > 480:
                self.kill()


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed, assets):
        super().__init__()
        self.image = assets.get('player_bullet')
        self.rect = self.image.get_rect(center=(x, y))
        self.speedy = speed

    def update(self, *args):
        self.rect.y += self.speedy
        if self.rect.bottom < 0:
            self.kill()

class CosmicGrind:
    def __init__(self, screen_width, screen_height, assets):
        pygame.init()
        self.width = screen_width
        self.height = screen_height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Cosmic Grind: Brew-tal Arcade Action!')

        self.assets = assets
        self.colors = assets.get('colors', {})
        self.font_style = pygame.font.SysFont(None, 35)
        self.large_font = pygame.font.SysFont(None, 75)
        self.score = 0
        self.game_over = False
        self.wave = 0
        
        self.last_dive_time = pygame.time.get_ticks()
        self.dive_delay = 2000

        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()

        self.player = Player(self.width, self.height, self.assets)
        self.all_sprites.add(self.player)

    def spawn_wave(self):
        self.wave += 1
        num_rows = 3 + (self.wave // 2)
        enemies_per_row = 6
        
        for row in range(num_rows):
            for col in range(enemies_per_row):
                target_x = (col * 35) + (self.width - enemies_per_row * 35) / 2 + 20
                target_y = (row * 35) + 40 # Reduced vertical spacing
                enemy = Enemy(self.assets, target_x, target_y)
                self.all_sprites.add(enemy)
                self.enemies.add(enemy)

    def trigger_enemy_dive(self):
        formation_enemies = [e for e in self.enemies if e.state == 'FORMATION']
        if formation_enemies:
            random.choice(formation_enemies).state = 'DIVING'

    def game_loop(self, high_score_so_far=0):
        self.spawn_wave()
        
        while not self.game_over:
            now = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_over = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.game_over = True

            if now - self.last_dive_time > self.dive_delay:
                self.last_dive_time = now
                self.trigger_enemy_dive()

            self.all_sprites.update(self.all_sprites, self.bullets)

            hits = pygame.sprite.groupcollide(self.enemies, self.bullets, True, True)
            for hit in hits:
                self.score += 10

            hits = pygame.sprite.spritecollide(self.player, self.enemies, True)
            if hits:
                self.game_over = True

            if not self.enemies:
                self.message(f"Wave {self.wave + 1}", self.colors.get('text', (255, 255, 255)), font=self.large_font)
                pygame.display.update()
                time.sleep(2)
                self.spawn_wave()
            
            self.screen.fill(self.colors.get('background', (15, 15, 25)))
            self.all_sprites.draw(self.screen)
            self.display_score()
            pygame.display.update()
            pygame.time.Clock().tick(60)

        pygame.quit()
        return self.score

    def display_score(self):
        score_text = self.font_style.render(f"Score: {self.score}", True, self.colors.get('text', (255, 255, 255)))
        self.screen.blit(score_text, (10, 10))
    
    def message(self, msg, color, y_offset=0, font=None):
        if font is None:
            font = self.font_style
        mesg = font.render(msg, True, color)
        text_rect = mesg.get_rect(center=(self.width / 2, self.height / 2 + y_offset))
        self.screen.blit(mesg, text_rect)