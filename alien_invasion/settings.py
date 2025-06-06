class Settings: # 储存游戏中所有设置的类
    def __init__(self): # 初始化游戏的静态设置
        self.screen_width = 1200 # 屏幕设置
        self.screen_height = 800
        self.bg_color = (230, 230, 230)
        self.ship_limit = 3 # 飞船设置
        self.bullet_width = 300 # 子弹设置
        self.bullet_height = 15
        self.bullet_color = (60, 60, 60)
        self.bullets_allowed = 30 # 限制子弹数目
        self.fleet_drop_speed = 10 # 外星人设置
        self.speedup_scale = 1.1 # 游戏节奏
        self.score_scale = 1.5 # 外星人分数的提高速度
        self.initialize_dynamic_settings()
    
    def initialize_dynamic_settings(self): # 初始化随游戏进行而变化的设置
        self.ship_speed = 1.5
        self.bullet_speed = 2.5
        self.alien_speed = 1.0
        self.fleet_direction = 1 # 左右变化
        self.alien_points = 50
    
    def increase_speed(self): # 提高速度设置的值
        self.ship_speed *= self.speedup_scale
        self.bullet_speed *= self.speedup_scale
        self.alien_speed *= self.speedup_scale
        self.alien_points = int(self.alien_points * self.score_scale)
