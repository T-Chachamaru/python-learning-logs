import pygame
from pygame.sprite import Sprite

class Bullet(Sprite): # 管理飞船所发射的子弹的类
    def __init__(self, ai_game): # 初始化子弹对象
        super().__init__() # 继承Sprite对象
        self.screen = ai_game.screen # 获得屏幕对象
        self.settings = ai_game.settings # 获得设置
        self.color = self.settings.bullet_color # 从设置中取得子弹颜色
        self.rect = pygame.Rect(0, 0, self.settings.bullet_width, self.settings.bullet_height) # 在0,0处设置一个子弹的矩形
        self.rect.midtop = ai_game.ship.rect.midtop # 将子弹rect设置到飞船rect之上
        self.y = float(self.rect.y) # 储存子弹位置
        
    def update(self): # 向上移动子弹
        self.y -= self.settings.bullet_speed # 更新子弹位置
        self.rect.y = self.y
    
    def draw_bullet(self): # 在屏幕上绘制子弹
        pygame.draw.rect(self.screen, self.color, self.rect)