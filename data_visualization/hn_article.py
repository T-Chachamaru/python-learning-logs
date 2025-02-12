import requests
from operator import itemgetter

url = "https://hacker-news.firebaseio.com/v0/topstories.json" # 执行API调用并查看响应
r = requests.get(url)
print(f"Status code: {r.status_code}")
 
submission_ids = r.json() # 处理有关每篇文章的信息
submission_dicts = []
for submission_id in submission_ids[:5]:
    url = f"https://hacker-news.firebaseio.com/v0/item/{submission_id}.json" # 对于每篇文章,都执行一个API调用
    r = requests.get(url)
    print(f"id: {submission_id}\tstatus: {r.status_code}")
    response_dict = r.json()

    submission_dict = { # 对于每篇文章,都创建一个字典
        'title': response_dict['title'],
        'hn_link': f"https://news.ycombinator.com/item?id={submission_id}",
        'comments': response_dict['descendants'],
    }
    submission_dicts.append(submission_dict)

submission_dicts = sorted(submission_dicts, key = itemgetter('comments'), reverse = True)

for submission_dict in submission_dicts:
    print(f"\nTitle: {submission_dict['title']}")
    print(f"Discussion link: {submission_dict['hn_link']}")
    print(f"Comments: {submission_dict['comments']}")