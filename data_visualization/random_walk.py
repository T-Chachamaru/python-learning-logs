from random import choice

class RandomWalk: 
    # 一个生成随机游走数据的类
    def __init__(self, num_points = 5000): # 初始化随机游走的属性
        self.num_points = num_points
        self.x_values = [0] # 所有随机游走都始于(0, 0)
        self.y_values = [0]

    def fill_walk(self): # 计算随机游走包含的所有点
        while len(self.x_values) < self.num_points: # 不断游走,直到列表达到指定的长度
            x_direction = choice([1, -1]) # 决定前进的方向以及沿着这个方向前进的距离
            x_distance = choice([0, 1, 2, 3, 4])
            x_step = x_distance * x_direction

            y_direction = choice([1, -1])
            y_distance = choice([0, 1, 2, 3, 4])
            y_step = y_distance * y_direction

            if x_step == 0 and y_step == 0: # 拒绝原地踏步
                continue

            x = self.x_values[-1] + x_step # 计算下一个点的x坐标值和y坐标值
            y = self.y_values[-1] + y_step

            self.x_values.append(x)
            self.y_values.append(y)