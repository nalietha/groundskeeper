import pygame
import random

class SnakeGame:
    def __init__(self, screen_width, screen_height, theme_assets):
        pygame.init()
        self.width = screen_width
        self.height = screen_height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Groundskeeper - Snake')

        self.food_asset = theme_assets.get('food')
        self.colors = theme_assets.get('colors', {
            "snake": (0, 255, 0),
            "food": (255, 0, 0),
            "background": (0, 0, 0),
            "text": (255, 255, 255)
        })

        self.clock = pygame.time.Clock()
        self.snake_block = 20
        self.snake_speed = 10
        self.font_style = pygame.font.SysFont(None, 35)

    def game_loop(self):
        game_over = False
        game_close = False

        x1 = self.width / 2
        y1 = self.height / 2
        x1_change = 0
        y1_change = 0

        snake_list = []
        length_of_snake = 1

        foodx = round(random.randrange(0, self.width - self.snake_block) / self.snake_block) * self.snake_block
        foody = round(random.randrange(0, self.height - self.snake_block) / self.snake_block) * self.snake_block

        while not game_over:
            while game_close:
                self.screen.fill(self.colors['background'])
                self.message("You Lost! Press Q-Quit or C-Play Again", self.colors['text'])
                pygame.display.update()

                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_q:
                            game_over = True
                            game_close = False
                        if event.key == pygame.K_c:
                            self.game_loop()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_over = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT and x1_change == 0:
                        x1_change = -self.snake_block
                        y1_change = 0
                    elif event.key == pygame.K_RIGHT and x1_change == 0:
                        x1_change = self.snake_block
                        y1_change = 0
                    elif event.key == pygame.K_UP and y1_change == 0:
                        y1_change = -self.snake_block
                        x1_change = 0
                    elif event.key == pygame.K_DOWN and y1_change == 0:
                        y1_change = self.snake_block
                        x1_change = 0

            if x1 >= self.width or x1 < 0 or y1 >= self.height or y1 < 0:
                game_close = True
            x1 += x1_change
            y1 += y1_change
            self.screen.fill(self.colors['background'])
            
            if self.food_asset:
                self.screen.blit(self.food_asset, (foodx, foody))
            else:
                pygame.draw.rect(self.screen, self.colors['food'], [foodx, foody, self.snake_block, self.snake_block])

            snake_head = []
            snake_head.append(x1)
            snake_head.append(y1)
            snake_list.append(snake_head)
            if len(snake_list) > length_of_snake:
                del snake_list[0]

            for x in snake_list[:-1]:
                if x == snake_head:
                    game_close = True

            self.draw_snake(snake_list)
            self.display_score(length_of_snake - 1)

            pygame.display.update()

            if x1 == foodx and y1 == foody:
                foodx = round(random.randrange(0, self.width - self.snake_block) / self.snake_block) * self.snake_block
                foody = round(random.randrange(0, self.height - self.snake_block) / self.snake_block) * self.snake_block
                length_of_snake += 1

            self.clock.tick(self.snake_speed)

        pygame.quit()

    def message(self, msg, color):
        mesg = self.font_style.render(msg, True, color)
        self.screen.blit(mesg, [self.width / 6, self.height / 3])

    def draw_snake(self, snake_list):
        for x in snake_list:
            pygame.draw.rect(self.screen, self.colors['snake'], [x[0], x[1], self.snake_block, self.snake_block])

    def display_score(self, score):
        value = self.font_style.render("Your Score: " + str(score), True, self.colors['text'])
        self.screen.blit(value, [0, 0])