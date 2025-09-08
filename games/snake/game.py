# groundskeper/games/snake/game.py
import pygame
import random

class Snake:
    def __init__(self, screen_width, screen_height, assets, callbacks):
        pygame.init()
        self.width = screen_width
        self.height = screen_height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Groundskeeper - Snake')

        self.assets = assets
        self.callbacks = callbacks
        self.colors = assets.get('colors', {})
        self.player_head_original = assets.get('player_head')
        self.player_head_rotated = self.player_head_original
        self.player_body_img = assets.get('player_body')
        self.food_img = assets.get('food')

        self.clock = pygame.time.Clock()
        self.snake_block = 20
        self.snake_speed = 10
        self.font_style = pygame.font.SysFont(None, 35)
        self.score_font = pygame.font.SysFont(None, 50)

    def _generate_food(self, snake_list):
        """Generates food at a position that is not currently occupied by the snake."""
        while True:
            foodx = round(random.randrange(0, self.width - self.snake_block) / self.snake_block) * self.snake_block
            foody = round(random.randrange(0, self.height - self.snake_block) / self.snake_block) * self.snake_block
            
            if [foodx, foody] not in snake_list:
                return foodx, foody

    def game_loop(self, high_score_so_far=0):
        """
        Main game loop. Tracks the highest score within a session.
        """
        self.callbacks['set_score_visibility'](True)
        self.callbacks['update_score'](0)
        
        game_over = False
        game_close = False

        x1 = self.width / 2
        y1 = self.height / 2
        x1_change = 0
        y1_change = 0

        snake_list = []
        length_of_snake = 1
        
        foodx, foody = self._generate_food(snake_list)

        while not game_over:
            while game_close:
                self.screen.fill(self.colors.get('background', (0,0,0)))
                
                current_score = length_of_snake - 1
                session_high_score = max(high_score_so_far, current_score)

                self.message("You Lost!", self.colors.get('text', (255,255,255)), y_offset=-50)
                self.message(f"Final Score: {current_score}", self.colors.get('text', (255,255,255)), font=self.score_font, y_offset=0)
                self.message("Press A-Play Again", self.colors.get('text', (255,255,255)), y_offset=50)
                self.message("B-Quit", self.colors.get('text', (255,255,255)), y_offset=100)
                pygame.display.update()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        game_over = True; game_close = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_b:
                            game_over = True; game_close = False
                        if event.key == pygame.K_a:
                            return self.game_loop(high_score_so_far=session_high_score)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_over = True
                if event.type == pygame.KEYDOWN:
                    if self.player_head_original:
                        if event.key == pygame.K_LEFT and x1_change == 0:
                            x1_change = -self.snake_block; y1_change = 0
                            self.player_head_rotated = pygame.transform.rotate(self.player_head_original, -90)
                        elif event.key == pygame.K_RIGHT and x1_change == 0:
                            x1_change = self.snake_block; y1_change = 0
                            self.player_head_rotated = pygame.transform.rotate(self.player_head_original, 90)
                        elif event.key == pygame.K_UP and y1_change == 0:
                            y1_change = -self.snake_block; x1_change = 0
                            self.player_head_rotated = pygame.transform.rotate(self.player_head_original, 180)
                        elif event.key == pygame.K_DOWN and y1_change == 0:
                            y1_change = self.snake_block; x1_change = 0
                            self.player_head_rotated = self.player_head_original

            if x1 >= self.width or x1 < 0 or y1 >= self.height or y1 < 0:
                game_close = True
            x1 += x1_change
            y1 += y1_change
            self.screen.fill(self.colors.get('background', (0,0,0)))
            
            if self.food_img:
                self.screen.blit(self.food_img, (foodx, foody))
            else:
                pygame.draw.rect(self.screen, self.colors.get('food_color', (255,0,0)), [foodx, foody, self.snake_block, self.snake_block])

            snake_head = [x1, y1]
            snake_list.append(snake_head)
            if len(snake_list) > length_of_snake:
                del snake_list[0]

            head_rect = pygame.Rect(snake_head[0], snake_head[1], self.snake_block, self.snake_block)
            food_rect = pygame.Rect(foodx, foody, self.snake_block, self.snake_block)

            for x in snake_list[:-1]:
                segment_rect = pygame.Rect(x[0], x[1], self.snake_block, self.snake_block)
                if head_rect.colliderect(segment_rect):
                    game_close = True

            self.draw_snake_body(snake_list[:-1])
            if self.player_head_rotated:
                self.screen.blit(self.player_head_rotated, (snake_head[0], snake_head[1]))
            else: 
                pygame.draw.rect(self.screen, self.colors.get('snake', (0,255,0)), [snake_head[0], snake_head[1], self.snake_block, self.snake_block])
            
            pygame.display.update()
            
            if head_rect.colliderect(food_rect):
                foodx, foody = self._generate_food(snake_list)
                length_of_snake += 1
                self.callbacks['update_score'](length_of_snake - 1)

            self.clock.tick(self.snake_speed)

        self.callbacks['set_score_visibility'](False)
        pygame.quit()
        final_score = length_of_snake - 1
        return max(high_score_so_far, final_score)

    def message(self, msg, color, font=None, y_offset=0):
        if font is None:
            font = self.font_style
        mesg = font.render(msg, True, color)
        text_rect = mesg.get_rect(center=(self.width / 2, self.height / 2 + y_offset))
        self.screen.blit(mesg, text_rect)

    def draw_snake_body(self, snake_list):
        if self.player_body_img:
            for x in snake_list:
                self.screen.blit(self.player_body_img, (x[0], x[1]))
        else:
            for x in snake_list:
                pygame.draw.rect(self.screen, self.colors.get('snake', (0,255,0)), [x[0], x[1], self.snake_block, self.snake_block])