import requests
url="https://api.github.com/search/repositories"
keyword=input("请输入仓库搜索关键词").strip()
params={
    'q':f'{keyword} language:python',
    'per_page':3,
    'sort':'stars',
    'order':'desc'
}
response=requests.get(url,params=params,timeout=10)

print(f"原始地址：{url}")
print(f"实际请求地址：{response.url}")

print(f"状态码：{response.status_code}")
if response.status_code==200:
    data=response.json()
    repositories=data['items']

    print(f"最外层类型：{type(data)}")
    print(f"items类型：{type(repositories)}")
    print(f"返回仓库数量：{len(repositories)}")

    for repository in repositories:
        print(f"仓库名称：{repository['full_name']}")
        print(f"主要语言：{repository['language']}")
        print(f"star数量：{repository['stargazers_count']}")
        print('-'*30)

else:
    print("搜索请求失败！")