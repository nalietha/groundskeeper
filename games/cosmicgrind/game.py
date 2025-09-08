# groundskeeper/games/cosmic_grind/game.py
import pygame
import random
import time
import math

class Player(pygame.sprite.Sprite):
    def __init__(self, screen_width, screen_height, assets):
        super().__init__()
        self.image = assets.get('player_ship')
        self.original_image = self.image
        self.rect = self.image.get_rect(center=(screen_width / 2, screen_height - 50))
        self.screen_width = screen_width
        self.speed = 5
        self.last_shot = 0
        self.shoot_delay = 300
        self.assets = assets
        self.lives = 3
        self.hidden = False
        self.hide_timer = pygame.time.get_ticks()

    def update(self, all_sprites, player_bullets, *args): # Corrected method signature
        if self.hidden and pygame.time.get_ticks() - self.hide_timer > 2000:
            self.hidden = False
            self.rect.centerx = self.screen_width / 2
            self.rect.bottom = self.screen_height - 10

        if self.hidden:
            self.image.set_alpha(128)
        else:
            self.image.set_alpha(255)

        keys = pygame.key.get_pressed()
        if not self.hidden:
            if keys[pygame.K_LEFT]:
                self.rect.x -= self.speed
            if keys[pygame.K_RIGHT]:
                self.rect.x += self.speed

            if self.rect.left < 0:
                self.rect.left = 0
            if self.rect.right > self.screen_width:
                self.rect.right = self.screen_width

            now = pygame.time.get_ticks()
            if keys[pygame.K_a] and now - self.last_shot > self.shoot_delay:
                self.last_shot = now
                bullet = Bullet(self.rect.centerx, self.rect.top, -10, self.assets)
                all_sprites.add(bullet)
                player_bullets.add(bullet)
            
            if keys[pygame.K_b]:
                pass

    def hide(self):
        self.lives -= 1
        self.hidden = True
        self.hide_timer = pygame.time.get_ticks()
        self.rect.center = (self.screen_width / 2, self.screen_height + 200)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, assets, target_x, target_y):
        super().__init__()
        self.assets = assets
        self.image = random.choice([assets.get('enemy_ship_1'), assets.get('enemy_ship_2')])
        self.rect = self.image.get_rect(center=(-50, -50))
        
        self.state = 'ENTERING'
        self.target_x = target_x
        self.target_y = target_y
        self.formation_speed = 4
        self.dive_pattern = random.choice(['straight', 'swoop'])
        self.dive_speed = 4
        self.swoop_speed_x = random.choice([-2, 2])

    def update(self, player, all_sprites, enemy_bullets, *args): # Corrected method signature
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
            if self.dive_pattern == 'swoop' and not player.hidden:
                if self.rect.centerx < player.rect.centerx:
                    self.rect.x += self.swoop_speed_x
                else:
                    self.rect.x -= self.swoop_speed_x
            
            self.rect.y += self.dive_speed
            if self.rect.top > 480:
                self.kill()

            if random.randrange(100) < 2:
                enemy_bullet = EnemyBullet(self.rect.centerx, self.rect.bottom, self.assets)
                all_sprites.add(enemy_bullet)
                enemy_bullets.add(enemy_bullet)

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

class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, assets):
        super().__init__()
        self.image = assets.get('enemy_bullet')
        self.rect = self.image.get_rect(center=(x, y))
        self.speedy = 5

    def update(self, *args):
        self.rect.y += self.speedy
        if self.rect.top > 480:
            self.kill()

class Powerup(pygame.sprite.Sprite):
    def __init__(self, center, assets):
        super().__init__()
        self.type = 'blue'
        self.image = assets.get('powerup_blue')
        self.rect = self.image.get_rect(center=center)
        self.speedy = 3

    def update(self, *args):
        self.rect.y += self.speedy
        if self.rect.top > 480:
            self.kill()

class CosmicGrind:
    def __init__(self, screen_width, screen_height, assets, callbacks):
        pygame.init()
        self.width = screen_width
        self.height = screen_height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Cosmic Grind: Brew-tal Arcade Action!')

        self.assets = assets
        self.callbacks = callbacks
        self.colors = assets.get('colors', {})
        self.font_style = pygame.font.SysFont(None, 35)
        self.large_font = pygame.font.SysFont(None, 75)
        self.score = 0
        self.game_running = True
        self.wave = 0
        
        self.last_dive_time = pygame.time.get_ticks()
        self.dive_delay = 1500
        self.wave_cleared_time = None

        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()

        self.player = Player(self.width, self.height, self.assets)
        self.all_sprites.add(self.player)

    def spawn_wave(self):
        self.wave += 1
        num_rows = 3 + (self.wave // 2)
        enemies_per_row = 6
        
        for row in range(num_rows):
            for col in range(enemies_per_row):
                target_x = (col * 35) + (self.width - enemies_per_row * 35) / 2 + 20
                target_y = (row * 35) + 40
                enemy = Enemy(self.assets, target_x, target_y)
                self.all_sprites.add(enemy)
                self.enemies.add(enemy)

    def trigger_enemy_dive(self):
        formation_enemies = [e for e in self.enemies if e.state == 'FORMATION']
        if formation_enemies:
            random.choice(formation_enemies).state = 'DIVING'

    def game_loop(self, high_score_so_far=0):
        self.callbacks['set_score_visibility'](True)
        self.callbacks['update_score'](self.score)
        self.spawn_wave()
        
        while self.game_running:
            now = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.game_running = False

            if self.wave_cleared_time is None and now - self.last_dive_time > self.dive_delay:
                self.last_dive_time = now
                self.trigger_enemy_dive()

            # The main update call now sends the correct arguments to each sprite class
            self.all_sprites.update(self.player, self.all_sprites, self.enemy_bullets, self.player_bullets)
            
            hits = pygame.sprite.groupcollide(self.enemies, self.player_bullets, True, True)
            if hits:
                for hit in hits:
                    self.score += 10
                    if random.randrange(35) == 0:
                        powerup = Powerup(hit.rect.center, self.assets)
                        self.all_sprites.add(powerup)
                        self.powerups.add(powerup)
                self.callbacks['update_score'](self.score)

            hits = pygame.sprite.spritecollide(self.player, self.powerups, True)
            for hit in hits:
                if hit.type == 'blue':
                    self.player.shoot_delay -= 50
                    if self.player.shoot_delay < 100:
                        self.player.shoot_delay = 100

            if not self.player.hidden:
                player_hit = False
                if pygame.sprite.spritecollide(self.player, self.enemy_bullets, True):
                    player_hit = True
                if pygame.sprite.spritecollide(self.player, self.enemies, True):
                    player_hit = True
                
                if player_hit:
                    self.player.hide()
                    if self.player.lives <= 0:
                        self.game_running = False

            if not self.enemies and self.wave_cleared_time is None:
                self.wave_cleared_time = pygame.time.get_ticks()

            if self.wave_cleared_time is not None and now - self.wave_cleared_time > 1000:
                self.message(f"Wave {self.wave + 1}", self.colors.get('text', (255, 255, 255)), font=self.large_font)
                pygame.display.update()
                time.sleep(2)
                self.spawn_wave()
                self.wave_cleared_time = None
            
            self.screen.fill(self.colors.get('background', (15, 15, 25)))
            self.all_sprites.draw(self.screen)
            self.draw_lives()
            
            if self.wave_cleared_time is not None and now - self.wave_cleared_time > 1000:
                self.message(f"Wave {self.wave + 1}", self.colors.get('text', (255, 255, 255)), font=self.large_font)

            pygame.display.update()
            pygame.time.Clock().tick(60)

        self.callbacks['set_score_visibility'](False)
        pygame.quit()
        return self.score
    
    def draw_lives(self):
        life_icon = self.assets.get('player_life_icon')
        if life_icon:
            for i in range(self.player.lives - 1):
                img_rect = life_icon.get_rect()
                img_rect.x = self.width - 30 - (i * 25)
                img_rect.y = 10
                self.screen.blit(life_icon, img_rect)
    
    def message(self, msg, color, y_offset=0, font=None):
        if font is None:
            font = self.font_style
        mesg = font.render(msg, True, color)
        text_rect = mesg.get_rect(center=(self.width / 2, self.height / 2 + y_offset))
        self.screen.blit(mesg, text_rect)