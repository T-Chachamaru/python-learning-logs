import plotly.express as px
from die import Die

die_1 = Die() # 创建一个d6骰
die_2 = Die(10)
title = "Results of Rolling a D6 and a D10 50,000 Times"

results = [] # 掷几次骰子并将结果储存在一个列表中
for roll_num in range(50_000):
    result = die_1.roll() + die_2.roll()
    results.append(result)

frequencies = [] # 分析结果
max_result = die_1.num_sides + die_2.num_sides
poss_results = range(1, max_result + 1)
for value in poss_results:
    frequency = results.count(value) # 计算每个点数被骰出了多少次
    frequencies.append(frequency)

labels = {'x':'Result', 'y':'Frequency of Result'}
fig = px.bar(x = poss_results, y = frequencies, title = title, labels = labels) # 对结果进行可视化,title参数为图题,labels参数是要添加的坐标轴比值的键值对
# fig = px.line(x = poss_results, y = frequencies) # 线形图
# fig = px.scatter(x = poss_results, y = frequencies) # 散点图
fig.update_layout(xaxis_dtick = 1) # 给每个条形都加上标签

fig.show()
# fig.write_html('dice_visual_d6d10.html') # 将输出的图形保存为html文件,可以传递一个path对象,把输出文件保存到任何地方