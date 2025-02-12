import matplotlib.pyplot as plt

x_values = range(1, 1001)
y_values = [x**2 for x in x_values] # 列表推导式

plt.style.use('seaborn-v0_8')
fig, ax = plt.subplots()
# 使用散点图,参数s用来控制绘图时使用的点的尺寸,参数color表示要使用的颜色(其中可用元组表示的RGB值),参数c表示关于颜色渐变的映射,参数cmap表示要使用哪个颜色映射
ax.scatter(x_values, y_values, c = y_values, cmap = plt.cm.Blues, s = 10) 

# 设置图题并给坐标轴加上标签
ax.set_title("Square Numbers", fontsize = 24) 
ax.set_xlabel("Value", fontsize = 14)
ax.set_ylabel("Square of Value", fontsize = 14)

# 设置刻度标记的样式
ax.tick_params(labelsize = 24)

ax.axis([0, 1100, 0, 1_100_000]) # 设置每个坐标轴的取值范围,分别是x和y轴的最小值与最大值
ax.ticklabel_format(style = 'plain') # 覆盖默认的刻度标记样式

plt.show()
# plt.savefig('squares_plot.png', bbox_inches = 'tight') # 将绘图储存下来,第一个参数是储存下来的文件名,也可以使用path对象储存在任何地方。第二个参数指定将多余的空白区域裁剪掉