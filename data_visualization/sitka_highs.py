import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
import csv

path = Path('weather_data/sitka_weather_2014.csv') # 获取csv文件的路径
lines = path.read_text().splitlines() # 读取csv文件并且返回一个拆分成各行的列表

reader = csv.reader(lines) # 传入一个行列表,解析文件的各行
header_row = next(reader) # next返回文件的下一行,因为是第一次调用,所以返回的是第一行
for index, column_header in enumerate(header_row): # 获取每个元素的索引及其值
    print(index, column_header)

dates, highs, lows = [], [], [] # 提取最高温度、时间与最低温度
for row in reader:
    current_date = datetime.strptime(row[0], '%Y-%m-%d')
    high = int((row[4]))
    low = int((row[5]))
    dates.append(current_date)
    highs.append(high)
    lows.append(low)

plt.style.use('seaborn-v0_8') # 设置最高温度绘图
fig, ax = plt.subplots()
ax.plot(dates, highs, color = 'red', alpha = 0.5) # alpha参数指定透明度
ax.plot(dates, lows, color= 'blue', alpha = 0.5)
ax.fill_between(dates, highs, lows, facecolor = 'blue', alpha = 0.1) # 传入一组x坐标与两组y坐标,填充波动之间的空隙

ax.set_title("Daily High and low Temperatures, 2014", fontsize = 24) # 设置绘图的格式
ax.set_xlabel('', fontsize = 16)
fig.autofmt_xdate()
ax.set_ylabel("Temperature (F)", fontsize = 16)
ax.tick_params(labelsize = 16)

plt.show()