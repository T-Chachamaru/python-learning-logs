import argparse
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scipy.spatial.distance import squareform, pdist, cdist
from numpy.linalg import norm

# 窗口尺寸
width, height = 640, 480

class Boids:
    """Boids模拟类,实现鸟群行为规则与环境影响因素"""
    def __init__(self, N, obstacle=None):
        # 初始化位置：围绕屏幕中心随机分布
        self.pos = [width/2.0, height/2.0] + 10*np.random.rand(2*N).reshape(N, 2)
        # 初始化速度：随机方向
        angles = 2*math.pi*np.random.rand(N)
        self.vel = np.array(list(zip(np.sin(angles), np.cos(angles))))
        self.N = N                  # Boid数量
        self.minDist = 25.0         # 分离规则的作用距离
        self.maxRuleVel = 0.03      # 规则所能施加的最大速度
        self.maxVel = 2.0           # Boid的最大速度
        self.obstacle = obstacle    # 障碍物参数 (x, y, R)
        self.windActive = False    # 风效激活状态
        self.windDuration = 0      # 风效持续时间
        self.windCounter = 0       # 风效剩余时间
        self.dragFactor = 0.05     # 速度衰减系数（5%）

    def tick(self, frameNum, pts, beak):
        """更新每一帧的状态"""
        # 更新风效状态
        self.updateWind()
        # 计算所有Boid之间的欧氏距离矩阵
        self.distMatrix = squareform(pdist(self.pos))
        # 应用行为规则并更新速度
        self.vel += self.applyRules()
        # 应用避障规则
        if self.obstacle:
            self.vel += self.avoidObstacle()
        # 应用风效减速
        if self.windActive:
            self.applyWindEffect()
        # 限制速度范围
        self.limit(self.vel, self.maxVel)
        # 更新位置
        self.pos += self.vel
        # 处理边界条件
        self.applyBC()
        # 更新绘图数据
        pts.set_data(self.pos.reshape(2*self.N)[::2], 
                     self.pos.reshape(2*self.N)[1::2])
        # 计算鸟嘴方向向量
        vec = self.pos + 10*self.vel/self.maxVel
        beak.set_data(vec.reshape(2*self.N)[::2], 
                      vec.reshape(2*self.N)[1::2])
        
    def applyWindEffect(self):
        """应用风效：按比例衰减速度"""
        self.vel *= (1 - self.dragFactor)

    def updateWind(self):
        """随机触发风效"""
        if not self.windActive:
            # 每帧有1%概率触发新风效
            if np.random.rand() < 0.01:
                self.activateWind()
        else:
            self.windCounter -= 1
            if self.windCounter <= 0:
                self.windActive = False

    def activateWind(self):
        """初始化风效参数"""
        self.windActive = True
        self.windDuration = np.random.randint(50, 100)  # 持续1-2秒（50-100帧）
        self.windCounter = self.windDuration
        
    def avoidObstacle(self):
        """避障规则：远离障碍物"""
        obstacleForce = np.zeros_like(self.vel)
        if self.obstacle:
            # 解包障碍物参数
            ox, oy, R = self.obstacle
            # 计算每个boid到障碍物的距离
            distances = np.linalg.norm(self.pos - [ox, oy], axis=1)
            # 找出在影响范围内的个体
            inDanger = distances < R
            # 计算排斥方向（远离障碍物）
            directions = self.pos - [ox, oy]
            # 归一化方向向量
            normDirections = directions / (distances.reshape(-1, 1) + 1e-6)  # 防止除以零
            # 计算排斥力（距离越近力量越大）
            force_magnitude = 0.5 * (R - distances) / R
            obstacleForce[inDanger] = normDirections[inDanger] * force_magnitude[inDanger, None]
        return obstacleForce

    def limitVec(self, vec, maxVal):
        """限制单个向量的模长"""
        mag = norm(vec)
        if mag > maxVal:
            vec[0], vec[1] = vec[0]*maxVal/mag, vec[1]*maxVal/mag

    def limit(self, X, maxVal):
        """限制所有向量的模长"""
        for vec in X:
            self.limitVec(vec, maxVal)

    def applyBC(self):
        """边界条件处理,越界后从对侧出现"""
        deltaR = 2.0
        for coord in self.pos:
            # 水平边界检测
            if coord[0] > width + deltaR:
                coord[0] = -deltaR
            elif coord[0] < -deltaR:
                coord[0] = width + deltaR
            # 垂直边界检测
            if coord[1] > height + deltaR:
                coord[1] = -deltaR
            elif coord[1] < -deltaR:
                coord[1] = height + deltaR

    def applyRules(self):
        """应用三条行为规则计算速度变化"""
        # 规则1：分离 - 避免与邻近个体碰撞
        D = self.distMatrix < 25.0  # 找出距离小于25的个体
        # 计算分离所需的调整速度
        vel = self.pos*D.sum(axis=1).reshape(self.N, 1) - D.dot(self.pos)
        self.limit(vel, self.maxRuleVel)
        # 规则2：对齐 - 匹配邻近个体的平均方向
        D = self.distMatrix < 50.0  # 扩大作用范围到50
        vel2 = D.dot(self.vel)       # 计算邻居速度之和
        self.limit(vel2, self.maxRuleVel)
        vel += vel2  # 累加对齐规则的影响
        # 规则3：聚集 - 向邻近个体的平均位置移动
        vel3 = D.dot(self.pos) - self.pos  # 计算向中心聚集的向量
        self.limit(vel3, self.maxRuleVel)
        vel += vel3  # 累加聚集规则的影响
        return vel

    def buttonPress(self, event):
        """鼠标点击事件处理"""
        # 忽略窗口外的点击事件
        if event.xdata is None or event.ydata is None:
            return
        # 左键添加新Boid
        if event.button == 1:
            new_pos = np.array([[event.xdata, event.ydata]])
            self.pos = np.concatenate((self.pos, new_pos), axis=0)
            # 随机生成新Boid的速度
            angles = 2*math.pi*np.random.rand(1)
            v = np.array(list(zip(np.sin(angles), np.cos(angles))))
            self.vel = np.concatenate((self.vel, v), axis=0)
            self.N += 1
        # 右键模拟Boid受惊
        elif event.button == 3:
            target = np.array([[event.xdata, event.ydata]])
            self.vel += 0.1*(self.pos - target)

def tick(frameNum, pts, beak, boids):
    """动画更新函数"""
    boids.tick(frameNum, pts, beak)
    return pts, beak

def main():
    # 参数解析
    parser = argparse.ArgumentParser(description="实现Craig Reynolds的Boids鸟群模拟")
    parser.add_argument('--num-boids', dest='N', required=False)
    parser.add_argument('--obstacle', nargs=3, type=float, metavar=('X', 'Y', 'R'),
                       help='设置障碍物参数 (x坐标 y坐标 半径)')
    args = parser.parse_args()
    # 设置Boid数量，默认100
    N = 100
    if args.N:
        N = int(args.N)
    # 解析障碍物参数
    obstacle = None
    if args.obstacle:
        obstacle = (args.obstacle[0], args.obstacle[1], args.obstacle[2])
    # 初始化模拟系统
    boids = Boids(N, obstacle=obstacle)
    # 设置matplotlib
    fig = plt.figure()
    ax = plt.axes(xlim=(0, width), ylim=(0, height))
    # 绘制障碍物绘制
    if obstacle:
        circle = plt.Circle((obstacle[0], obstacle[1]), obstacle[2] - 20, 
                            color='red', fill=False)
        ax.add_patch(circle)
    # 初始化绘图元素
    pts, = ax.plot([], [], markersize=10, c='k', marker='o', ls='None')  # 鸟身
    beak, = ax.plot([], [], markersize=4, c='r', marker='o', ls='None')   # 鸟嘴方向
    # 创建动画
    anim = animation.FuncAnimation(fig, tick, fargs=(pts, beak, boids), interval=50)
    # 绑定鼠标点击事件
    fig.canvas.mpl_connect('button_press_event', boids.buttonPress)
    # 显示窗口
    plt.show()

if __name__ == '__main__':
    main()