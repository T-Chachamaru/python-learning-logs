import sys,pygame
from settings import Settings
from ship import Ship
from bullet import Bullet
from alien import Alien
from game_stats import GameStats
from button import Button
from scoreboard import Scoreboard
# 这是pygame的一个最小开发框架模式,在开发其他小游戏程序时都可以参考它
class AlienInvasion: # 管理游戏资源和行为的类
    def __init__(self):
        pygame.init() # 初始化游戏并创建游戏资源
        self.clock = pygame.time.Clock() # 创建一个Clock类的实例
        self.settings = Settings() # 实例化设置类为属性
        self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height)) 
        # 使用设置类设定的宽高来创建游戏窗口
        '''elf.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN) # 创建全屏游戏窗口
        self.settings.screen_width = self.screen.get_rect().width # 将全盘游戏窗口的宽高交给设置以适配全局环境
        self.settings.screen_height = self.screen.get_rect().height'''
        pygame.display.set_caption("Alien Invasion") # 赋予游戏窗口标题
        self.stats = GameStats(self) # 创建一个用于统计游戏信息的实例对象
        self.sb = Scoreboard(self) # 创建记分牌
        self.ship = Ship(self) # 将管理飞船的ship类实例化为属性,将本身作为参数
        self.bullets = pygame.sprite.Group() # 创建子弹编组
        self.aliens = pygame.sprite.Group() # 创建外星人编组
        self._create_fleet()
        self.waiting_for_respawn = False # 等待标识
        self.respawn_wait_start = 0 # 等待时间
        self.game_active = False # 游戏启动后处于非活动状态
        self.play_button_easy = Button(self, "Play-easy") # 创建play按钮
        self.play_button_normal = Button(self, "Play-normal")
        self.play_button_normal.rect.y += 55
        self.play_button_normal.msg_image_rect.center = self.play_button_normal.rect.center
        self.play_button_hard = Button(self, "Play-hard")
        self.play_button_hard.rect.y += 110
        self.play_button_hard.msg_image_rect.center = self.play_button_hard.rect.center
        try:
            data = open('data.txt', 'r')
            self.stats.high_score = int(data.read())
            data.close()
        except FileNotFoundError:
            print("you not have data.txt")
        except ValueError:
            print("data.txt not number")
            sys.exit()

    def run_game(self):
        while True: # 开始游戏的主循环
            self._check_events() # 调用侦听事件的辅助方法
            current_time = pygame.time.get_ticks() # 检查等待
            if self.waiting_for_respawn and (current_time - self.respawn_wait_start >= 500):
                self.waiting_for_respawn = False
            if not self.waiting_for_respawn: # 非等待则更新游戏元素
                if self.game_active: # 如果游戏处于非活动状态则停止运行逻辑
                    self.ship.update() # 飞船移动
                    self._update_bullets() # 子弹移动
                    self._update_aliens() # 外星人移动
            self._update_screen() # 调用刷新屏幕上的图像的辅助方法
            self.clock.tick(60) # 使用Clock类控制游戏帧率,此为60帧
    
    def _check_events(self):
        for event in pygame.event.get(): # 侦听键盘和鼠标事件
            if event.type == pygame.QUIT: # 如果用户用鼠标点击X则触发事件相等而退出
                data = open('data.txt', 'w')
                data.write(str(self.stats.high_score))
                data.close()
                sys.exit()
            elif event.type == pygame.KEYDOWN: # 如果用户按下键盘击键
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP: # 如果用户放开键盘击键
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN: # 在屏幕单击时将检测到该事件
                mouse_pos = pygame.mouse.get_pos() # 返回单击时的光标的x和y轴
                self._check_play_button(mouse_pos) # 检测是否在按钮范围内
        
    def _check_play_button(self, mouse_pos): # 在玩家单击play按钮时开启新游戏
        if self._difficulty_detection(mouse_pos):
            button_clicked = self._difficulty_detection(mouse_pos)
            if button_clicked and not self.game_active: # 仅在游戏状态作为False时才会点击重置开始
                self.settings.initialize_dynamic_settings() # 还原节奏
                self._start_game()

    def _difficulty_detection(self, mouse_pos): # 检测玩家点击的按钮是哪个难度
        if self.play_button_easy.rect.collidepoint(mouse_pos):
            return True
        elif self.play_button_normal.rect.collidepoint(mouse_pos):
            self.settings.speedup_scale = 1.3
            return True
        elif self.play_button_hard.rect.collidepoint(mouse_pos):
            self.settings.speedup_scale = 1.5
            return True
        else:
            return False
    
    def _start_game(self):
        self.stats.reset_stats() # 重置游戏的统计信息
        self.sb.prep_score()
        self.sb.prep_level()
        self.sb.prep_ships()
        self.game_active = True
        self.bullets.empty() # 清空外星人列表和子弹列表
        self.aliens.empty()
        self._create_fleet() # 创建一个新的外星舰队,并将飞船放在屏幕底部的中央
        self.ship.center_ship()
        pygame.mouse.set_visible(False) # 隐藏光标

    def _check_keydown_events(self, event): # 响应按下
        if event.key == pygame.K_LEFT: # 如果击键是左方向键
            self.ship.moving_left = True # 将飞船的左移动标识的置为True
        elif event.key == pygame.K_RIGHT: # 如果是右方向键
            self.ship.moving_right = True # 将飞船的右移动标识的置为True
        elif event.key == pygame.K_UP:
            self.ship.moving_top = True
        elif event.key == pygame.K_DOWN:
            self.ship.moving_bottom = True
        elif event.key == pygame.K_q: # 按下q则退出
            data = open('data.txt', 'w')
            data.write(str(self.stats.high_score))
            data.close()
            sys.exit()
        elif event.key == pygame.K_SPACE: # 按下空格发射子弹
            self._fire_bullet()
        elif event.key == pygame.K_p and not self.game_active: # 按下p键并且游戏状态作为False时可启动游戏
            self._start_game()

    def _check_keyup_events(self, event): # 响应松开
        if event.key == pygame.K_LEFT: # 如果击键是左方向键
            self.ship.moving_left = False # 将飞船的左移动标识的置为False
        elif event.key == pygame.K_RIGHT: # 如果是右方向键
            self.ship.moving_right = False # 将飞船的右移动标识的置为Flase
        elif event.key == pygame.K_UP:
            self.ship.moving_top = False
        elif event.key == pygame.K_DOWN:
            self.ship.moving_bottom = False
        
    def _fire_bullet(self): # 每次调用都将创建一颗子弹并加入子弹编组
        if len(self.bullets) < self.settings.bullets_allowed: # 屏幕上的子弹数小于4时才能射击
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)
    
    def _update_screen(self):
        self.screen.fill(self.settings.bg_color) # 实用设置类的背景颜色RGB值改变窗口背景颜色
        for bullet in self.bullets.sprites(): # 调用编组中的每个子弹对象的绘制子弹方法来模拟子弹前进
            bullet.draw_bullet()
        self.ship.blitme() # 调用blitme方法实时地刷新绘制飞船
        self.aliens.draw(self.screen) # 将外星人绘制到屏幕上
        self.sb.show_score() # 显示得分
        if not self.game_active: # 如果游戏处于非活动状态,则绘制play按钮
            self.play_button_easy.draw_button()
            self.play_button_normal.draw_button()
            self.play_button_hard.draw_button()
        pygame.display.flip() # 刷新屏幕,让最近更新的屏幕可见

    def _update_bullets(self): # 更新子弹的位置并删除已消失的子弹
        self.bullets.update() # 对编组中的每颗子弹都调用方法来移动子弹
        for bullet in self.bullets.copy(): # 每个子弹飞出屏幕都将从编组中删除
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)
        self._check_bullet_alien_collistions()
    
    def _check_bullet_alien_collistions(self):
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True) # 检查编组碰撞,模拟子弹击中
        # 该函数返回一个字典,其中有表示碰撞的键值对,对应碰撞上的子弹与外星人。将第一个True设为False,将删除外星人,但不删除对应的子弹
        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens) # 更新得分
            self.sb.prep_score()
            self.sb.check_high_score()
        if not self.aliens: # 检测外星人编组是否为空
            self.bullets.empty() # 清空子弹编组
            self._create_fleet() # 重新生成外星人舰队
            self.settings.increase_speed() # 增强游戏节奏
            self.stats.level += 1 # 提高等级
            self.sb.prep_level()

    def _create_fleet(self): # 调用后将创建一个外星舰队
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        current_x, current_y = alien_width, alien_height # 获取第一个外星人的宽度与高度
        while current_y < (self.settings.screen_height - 3 * alien_height): # 不断添加外星人直到屏幕空间充满
            while current_x < (self.settings.screen_width - 2 * alien_width):
                self._create_alien(current_x,current_y)
                current_x += 2 * alien_width
            current_x = alien_width
            current_y += 2 * alien_height

    def _create_alien(self, x_position, y_position): # 创建一个外星人并将其放在当前行中
        new_alien = Alien(self) # 创建一个新外星人
        new_alien.x = x_position # 将水平位置设置为当前焦点
        new_alien.rect.x = x_position
        new_alien.rect.y = y_position
        self.aliens.add(new_alien) # 加入编组

    def _update_aliens(self): # 更新外星舰队中所有外星人的位置
        self._check_fleet_edges()
        self.aliens.update()
        if pygame.sprite.spritecollideany(self.ship, self.aliens): # 检测外星人与飞船的碰撞
            self._ship_hit()
        self._check_aliens_bottom() # 检测是否有外星人到了屏幕的下边缘
    
    def _check_fleet_edges(self): # 外星舰队到达屏幕边缘时采取相应措施
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self): # 将外星舰队向下移动
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _ship_hit(self): # 响应飞船和外星人的碰撞
        if self.stats.ships_left > 0: # 如果生命值等于0则停止游戏
            self.stats.ships_left -= 1 # 将生命值减1
            self.sb.prep_ships()
            self.bullets.empty() # 清空外星人列表和子弹列表
            self.aliens.empty()
            self._create_fleet() # 创建一个新的外星舰队,并将飞船重新放在屏幕底部的中央
            self.ship.center_ship()
            self.waiting_for_respawn = True # 启用等待
            self.respawn_wait_start = pygame.time.get_ticks() # 记录等待时间
        else:
            self.game_active = False
            pygame.mouse.set_visible(True) # 显示光标

    def _check_aliens_bottom(self): # 检查是否有外星人到了屏幕的下边缘
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= self.settings.screen_height:
                self._ship_hit()
                break

if __name__ == '__main__': 
    ai = AlienInvasion() # 创建游戏实例并运行游戏
    ai.run_game()