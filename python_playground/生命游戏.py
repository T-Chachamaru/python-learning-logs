import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# 定义细胞状态
ON = 255  # 存活状态
OFF = 0   # 死亡状态
vals = [ON, OFF]

def randomGrid(N):
    """生成随机网格,20%概率为存活状态"""
    return np.random.choice(vals, N*N, p=[0.2, 0.8]).reshape(N, N)

def addGlider(i, j, grid):
    """在指定位置添加滑翔机图案"""
    glider = np.array([[OFF, OFF, ON], 
                       [ON,  OFF, ON],
                       [ON,  ON,  OFF]])
    grid[i:i+3, j:j+3] = glider

def update(frameNum, img, grid, N):
    """更新网格状态"""
    newGrid = grid.copy()
    for i in range(N):
        for j in range(N):
            # 计算8个邻居的状态总和
            total = int((grid[i, (j-1)%N] + grid[i, (j+1)%N] + 
                         grid[(i-1)%N, j] + grid[(i+1)%N, j] +
                         grid[(i-1)%N, (j-1)%N] + grid[(i-1)%N, (j+1)%N] +
                         grid[(i+1)%N, (j-1)%N] + grid[(i+1)%N, (j+1)%N])/255)
            # 应用游戏规则
            if grid[i, j] == ON:
                if (total < 2) or (total > 3):
                    newGrid[i, j] = OFF  # 死亡规则
            else:
                if total == 3:
                    newGrid[i, j] = ON   # 繁殖规则
    img.set_data(newGrid)
    grid[:] = newGrid[:]
    return img,

def addGosperGun(i, j, grid):
    """
    在指定位置添加高斯帕滑翔机枪图案
    原始图案尺寸:36x9,需确保网格足够大
    """
    # 定义滑翔机枪的核心坐标（相对起始点i,j）
    gun = [
        # 左方块
        (5,1), (5,2), (6,1), (6,2),
        # 左中部结构
        (3,13), (3,14), (4,12), (4,16),
        (5,11), (5,17), (6,11), (6,15), (6,17), (6,18),
        (7,11), (7,17), (8,12), (8,16),
        (9,13), (9,14),
        # 右中部结构
        (1,25), (2,23), (2,25),
        (3,21), (3,22),
        (4,21), (4,22),
        (5,21), (5,22),
        (6,23), (6,25),
        (7,25),
        # 右方块振荡器
        (3,35), (3,36), (4,35), (4,36)
    ]
    # 将图案绘制到网格
    for (x, y) in gun:
        grid[i + x, j + y] = ON
    # 添加右侧滑翔机
    addGlider(i + 10, j + 38, grid)  # 调用现有滑翔机函数

def main():
    # 参数解析
    parser = argparse.ArgumentParser(description="运行康威生命游戏模拟")
    parser.add_argument('--grid-size', dest='N', type=int, 
                       help="定义网格尺寸(必须大于8)")
    parser.add_argument('--mov-file', dest='movfile', 
                       help="输出视频文件名")
    parser.add_argument('--interval', dest='interval', type=int,
                       help="更新间隔（毫秒）")
    parser.add_argument('--glider', action='store_true',
                       help="使用滑翔机初始图案")
    parser.add_argument('--gosper', action='store_true',
                       help="使用高斯帕滑翔枪初始图案")
    args = parser.parse_args()
    # 初始化参数
    N = 100  # 默认网格尺寸
    if args.N and args.N > 8:
        N = args.N
    updateInterval = 50  # 默认更新间隔
    if args.interval:
        updateInterval = args.interval
    # 初始化网格
    grid = np.zeros(N*N, dtype=int).reshape(N, N)  # 统一初始化为空网格
    if args.glider:
        addGlider(1, 1, grid)
    elif args.gosper:  # 新增分支
        if N < 50:  # 检查网格尺寸
            print("错误:高斯帕滑翔枪需要网格尺寸至少40x40")
            sys.exit(1)
        addGosperGun(5, 5, grid)
    else:
        grid = randomGrid(N)
    # 设置动画
    fig, ax = plt.subplots()
    img = ax.imshow(grid, interpolation='nearest')
    ani = animation.FuncAnimation(fig, update, fargs=(img, grid, N),
                                  frames=10,
                                  interval=updateInterval,
                                  save_count=50)
    # 输出视频文件
    if args.movfile:
        ani.save(args.movfile, fps=30, extra_args=['-vcodec', 'libx264'])
    plt.show()

if __name__ == '__main__':
    main()