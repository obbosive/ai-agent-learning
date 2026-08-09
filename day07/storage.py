import json

def save_job(jobs):
    with open('day07/jobs.json','w',encoding='utf-8')as file:
        json.dump(jobs,file,ensure_ascii=False,indent=4)

def load_job():
    try:
        with open('day07/jobs.json','r',encoding='utf-8')as file:
                return json.load(file)
    except FileNotFoundError:
         return []
    except json.JSONDecodeError:
         print("数据文件损坏！")
         return None


    