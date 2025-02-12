import matplotlib.pyplot as plt
from random_walk import RandomWalk

while True:
    rw = RandomWalk(50_000) # 创建一个实例对象并填满数据集
    rw.fill_walk()

    plt.style.use('classic') # 将所有的店都绘制出来
    fig, ax = plt.subplots(figsize = (15, 9), dpi = 128) # figsize参数改变图形的大小尺寸,dpi参数表示每英寸的分辨率
    point_numbers = range(rw.num_points) # 颜色映射,准确地指出从起点到终点的变化
    ax.scatter(rw.x_values, rw.y_values, c = point_numbers, cmap = plt.cm.Blues, edgecolors = 'none', s = 1) # degecolors参数删除每个点的轮廓
    ax.set_aspect('equal')

    ax.scatter(0, 0, c = 'green', edgecolors = 'none', s = 100) # 突出起点和终点
    ax.scatter(rw.x_values[-1], rw.y_values[-1], c = 'red', edgecolors = 'none', s = 100)

    ax.get_xaxis().set_visible(False) # 隐藏坐标轴
    ax.get_yaxis().set_visible(False)

    plt.show()

    keep_running = input("Make another walk? (y/n):")
    if keep_running == 'n':
        break