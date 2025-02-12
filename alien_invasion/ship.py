import pygame
from pygame.sprite import Sprite

class Ship(Sprite): # 管理飞船的类
    def __init__(self, ai_game): # 初始化飞船并设置其初始位置
        super().__init__() # 继承sprite
        self.screen = ai_game.screen # 将AlienInvasion类中的屏幕属性赋给Ship类的属性
        self.settings = ai_game.settings # 引入设置类
        self.screen_rect = ai_game.screen.get_rect() # 使用get_rect方法访问屏幕的rect属性并赋给Ship类的属性,以让我们能够将飞船放到正确的位置
        self.image = pygame.image.load('image/ship.bmp') # 加载飞船图像并获取其外接矩形
        self.rect = self.image.get_rect() # 获取image表示飞船的surface对象的rect属性
        self.rect.midbottom = self.screen_rect.midbottom # 使用屏幕的rect属性来将每艘新飞船都放在屏幕底部的中央
        '''rect对象的center、centerx或centery属性可设置是否居中;top、bottom、left或right属性可设置游戏元素与屏幕边缘对齐;
        还有一些midbottom、midtop、midleft和midright的组合属性。属性x和y则可调整游戏元素的水平或垂直位置'''
        self.x = float(self.rect.x) # 使用变量储存x轴的浮点数
        self.y = float(self.rect.y) # 使用变量储存y轴的浮点数
        self.moving_right = False # 右移动标识
        self.moving_left = False # 左移动标识
        self.moving_top = False # 上移动标识
        self.moving_bottom = False # 下移动标识
    
    def blitme(self):
        self.screen.blit(self.image, self.rect) # 在指定位置绘制飞船

    def update(self): # 如果移动标识为True,rect的x与y轴会持续递增,以达到连续移动的效果
        if self.moving_right and self.rect.right < self.screen_rect.right: # 限制飞船的移动范围
            self.x += self.settings.ship_speed
        if self.moving_left and self.rect.left > 0:
            self.x -= self.settings.ship_speed
        if self.moving_top and self.rect.top > 0:
            self.y -= self.settings.ship_speed
        if self.moving_bottom and self.rect.bottom < self.screen_rect.bottom:
            self.y += self.settings.ship_speed
        self.rect.x = self.x # 用储存的x轴属性来更新rect对象
        self.rect.y = self.y # 用储存的y轴属性来更新rect对象
    
    def center_ship(self): # 将飞机放在屏幕底部的中央
        self.rect.midbottom = self.screen_rect.midbottom
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)