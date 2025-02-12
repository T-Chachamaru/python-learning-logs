import pygame.font
from pygame.sprite import Group
from ship import Ship

class Scoreboard: # 显示得分信息的类
    def __init__(self, ai_game): # 初始化显示得分涉及的属性
        self.ai_game = ai_game # 获得游戏实例
        self.screen = ai_game.screen
        self.screen_rect = self.screen.get_rect()
        self.settings = ai_game.settings
        self.stats = ai_game.stats
        self.text_color = (30, 30, 30) # 显示得分信息所用的字体设置
        self.font = pygame.font.SysFont(None, 48)
        self.prep_score() # 准备初始得分与最高分的图像
        self.prep_high_score()
        self.prep_level()
        self.prep_ships()

    def prep_score(self): # 将得分渲染为图像
        rounded_score = round(self.stats.score, -1) # 舍入到十位数
        score_str = f"{rounded_score:,}" # 格式化字符在合适的位置插入,
        self.score_image = self.font.render(score_str, True, self.text_color, self.settings.bg_color)
        self.score_rect = self.score_image.get_rect() # 在屏幕右上角显示得分
        self.score_rect.right = self.screen_rect.right - 20
        self.score_rect.top = 20

    def show_score(self): # 在屏幕上显示得分
        self.screen.blit(self.score_image, self.score_rect)
        self.screen.blit(self.high_score_image, self.high_score_rect)
        self.screen.blit(self.level_image, self.level_rect)
        self.ships.draw(self.screen)

    def prep_high_score(self): # 将最高分渲染为图像
        high_score = round(self.stats.high_score, -1)
        high_score_str = f"{high_score:,}"
        self.high_score_image = self.font.render(high_score_str, True, self.text_color, self.settings.bg_color)
        self.high_score_rect = self.high_score_image.get_rect() # 将最高分放在屏幕顶部的中央
        self.high_score_rect.right = self.screen_rect.right - 300
        self.high_score_rect.top = 20
    
    def check_high_score(self): # 检查是否诞生了新的最高分
        if self.stats.score > self.stats.high_score:
            self.stats.high_score = self.stats.score
            self.prep_high_score()
    
    def prep_level(self): # 将等级渲染为图像
        level_str = str(self.stats.level)
        self.level_image = self.font.render(level_str, True, self.text_color, self.settings.bg_color)
        self.level_rect = self.level_image.get_rect() # 将等级放在得分下方
        self.level_rect.right = self.screen_rect.right - 20
        self.level_rect.top = self.score_rect.bottom + 10

    def prep_ships(self): # 显示还余下多少艘飞船
        self.ships = Group()
        for ship_number in range(self.stats.ships_left):
            ship = Ship(self.ai_game)
            ship.rect.x = 250 + ship_number * ship.rect.width
            ship.rect.y = 10
            self.ships.add(ship)