import requests
import plotly.express as px

url = "https://api.github.com/search/repositories" # 执行API调用并查看响应
url += "?q=language:python+sort:stars+stars:>10000"

headers = {"Accpet": "application/vnd.github.v3+json"} # 指定使用第三版并返回json格式
r = requests.get(url, headers = headers)
print(f"Status code: {r.status_code}") # 打印状态码显示是否成功

response_dict = r.json() # 将响应转换为字典
print(f"Comlete results: {not response_dict['incomplete_results']}")

repo_dicts = response_dict['items'] # 探索有关仓库的信息
repo_links, stars, hover_texts = [], [], []
for repo_dict in repo_dicts:
    repo_name = repo_dict['name'] # 将仓库名转换成链接
    repo_url = repo_dict['html_url']
    repo_link = f"<a href='{repo_url}'>{repo_name}</a>"
    repo_links.append(repo_link)
    stars.append(repo_dict['stargazers_count'])

    owner = repo_dict['owner']['login'] # 创建悬停文本
    description = repo_dict['description']
    hover_text = f"{owner}<br />{description}"
    hover_texts.append(hover_text)

title = "Most-Starred Python Projects on Github"  # 可视化
labels = {'x': 'Repository', 'y': 'Stars'}
fig = px.bar(x = repo_links, y = stars, title = title, labels = labels, hover_name = hover_texts)
fig.update_layout(title_font_size = 28, xaxis_title_font_size = 20, yaxis_title_font_size = 20)
fig.update_traces(marker_color = 'SteelBlue', marker_opacity = 0.6)
fig.show()