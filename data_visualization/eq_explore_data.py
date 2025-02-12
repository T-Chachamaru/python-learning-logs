import plotly.express as px
from pathlib import Path
import json
import pandas as pd

path = Path('eq_data/eq_data_30_day_m1.geojson') # 将数据作为字符串读取并转换为python对象
try:
    contents = path.read_text()
except:
    contents = path.read_text(encoding = 'utf-8')
all_eq_data = json.loads(contents) # 将读取出来的字符串表示转换为python对象表示

# path = Path('eq_data/readable_eq_data.geojson') # 将数据文件转换成更易读的版本
# readable_contents = json.dumps(all_eq_data, indent = 4) # 将内容格式化为更易阅读的形式,indent参数指定数据结构中嵌套元素的缩进量
# path.write_text(readable_contents)
all_eq_dicts = all_eq_data['features'] # 查看数据集中的所有地震
mags, titles, lons, lats = [], [], [], []
for eq_dict in all_eq_dicts:
    mag = eq_dict['properties']['mag']
    title = eq_dict['properties']['title']
    lon = eq_dict['geometry']['coordinates'][0]
    lat = eq_dict['geometry']['coordinates'][1]
    mags.append(mag)
    titles.append(title)
    lons.append(lon)
    lats.append(lat)

data = pd.DataFrame(data = zip(lons, lats, titles, mags), columns = ['经度', '纬度', '位置', '震级'])
data.head()
fig = px.scatter(
    data,
    x = '经度',
    y = '纬度',
    range_x = [-200, 200],
    range_y = [-90, 90],
    width = 800,
    height = 800,
    title = '全球地震散点图',
    size = '震级',
    size_max = 10,
    color = '震级',
    hover_name = '位置',
)
fig.write_html('global_earthquakes.html')
fig.show()
