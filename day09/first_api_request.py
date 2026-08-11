import os

import requests
from dotenv import load_dotenv
def show_repository_info():
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        print("没有读取到GitHub Token！")
        return



    url = "https://api.github.com/repos/obbosive/ai-agent-learning"
    headers={"Accept":"application/vnd.github+json",
             "User-Agent":"ai-agent-learning",
             "Authorization":f"Bearer {token}"}
    


    try:
        response=requests.get(url,headers=headers,timeout=10)
        print(response.request.headers['Accept'])
        print(response.request.headers['User-Agent'])
        print(f"每小时请求上限：{response.headers['X-RateLimit-Limit']}")
        print(f"本小时剩余额度：{response.headers['X-RateLimit-Remaining']}")
    except requests.exceptions.RequestException as error:
        print(f"网络请求没有完成！{error}")
        return
    print(f"状态码：{response.status_code}")
    
    if response.status_code==200:
        data=response.json()
        print(data['full_name'])
        print(data['default_branch'])
        print(data['language'])
        print(data['stargazers_count'])
    else:
        print("请求失败！")
        print(response.status_code)
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            print(f"捕获到http异常：{error}！")

if __name__=="__main__":
    show_repository_info()

