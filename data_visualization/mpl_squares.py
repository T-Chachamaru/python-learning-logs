import matplotlib.pyplot as plt # 导入pyplot模块,其中含有很多生成图形的函数

print(plt.style.available) # 打印可用的默认样式

input_values = [1, 2, 3, 4, 5]
squares = [1, 4, 9, 16, 25]

plt.style.use('seaborn-v0_8') # 使用库定义的默认样式来生成图形
fig, ax = plt.subplots() # subplots在一个图形中绘制一个或多个绘图,fig表示生成的一系列绘图构成的整个图形,ax表示图形中的绘图
ax.plot(input_values, squares, linewidth = 3) # 在表示绘图的对象上调用plot方法,根据输入的数据绘制绘图。同时plot方法默认第一个值对应的x坐标值为0,但正确情况是1,因此需要同时提供输入与输出值

# 设置图题并给坐标轴加上标签
ax.set_title("Square Numbers", fontsize = 24) 
ax.set_xlabel("Value", fontsize = 14)
ax.set_ylabel("Square of Value", fontsize = 14)

# 设置刻度标记的样式
ax.tick_params(labelsize = 24)

plt.show() # 打开matplotlib查看器并显示绘图