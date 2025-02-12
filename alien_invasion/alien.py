import pygame
from pygame.sprite import Sprite

class Alien(Sprite): # 表示单个外星人的类
    def __init__(self, ai_game): # 初始化外星人并设置起始位置
        super().__init__() # 继承Sprite类
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.image = pygame.image.load('image/alien.bmp') # 加载外星人图像并设置rece属性
        self.rect = self.image.get_rect()
        self.rect.x = self.rect.width # 获取外星人的位置,外星人最初在屏幕的左上角
        self.rect.y = self.rect.height
        self.x = float(self.rect.x) # 储存外星人的精确位置

    def check_edges(self): # 检查外星人是否位于屏幕边缘
        screen_rect = self.screen.get_rect()
        return (self.rect.right >= screen_rect.right) or (self.rect.left <= 0)

    def update(self): # 外星人向右或向左移动
        self.x += self.settings.alien_speed * self.settings.fleet_direction
        self.rect.x = self.x