import pygame.font

class Button: # 为游戏创建按钮的类
    def __init__(self, ai_game, msg): # 初始化按钮的属性
        self.screen = ai_game.screen
        self.screen_rect = self.screen.get_rect()
        self.width,self.height = 200, 50 # 设置按钮的尺寸和其他属性
        self.button_color = (0, 135, 0)
        self.text_color = (255, 255, 255)
        self.font = pygame.font.SysFont(None, 48) # 将字符串映射到屏幕上
        self.x = 0
        self.y = 0
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height) # 设置按钮的rect对象,并使其居中
        self._prep_msg(msg) # 按钮的标签只需创建一次

    def _prep_msg(self, msg): # 将msg渲染为图像,并使其在按钮上居中
        self.msg_image = self.font.render(msg, True, self.text_color, self.button_color) # 将文本转换为图像
        self.msg_image_rect = self.msg_image.get_rect()
        self.msg_image_rect.center = self.rect.center

    def draw_button(self): # 绘制一个用颜色填充的按钮,再绘制文本
        self.screen.fill(self.button_color, self.rect) # 绘制表示按钮的矩形
        self.screen.blit(self.msg_image, self.msg_image_rect) # 绘制文本图像