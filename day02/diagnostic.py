papers=[
        {"title":"ReAct","year":2022,"is_read":True},
        {"title":"AutoGen","year":2023,"is_read":False},
        {"title":"MetaGPT","year":2023,"is_read":False}
        ]

def get_read_status(is_read):
    if not is_read:
        return "未读"
    else:
        return "已读"

not_read_num=0
for paper in papers:
    if not paper["is_read"]:
        not_read_num+=1       
    read_status=get_read_status(paper["is_read"])
    title=paper["title"]
    year=paper["year"]

    print(f"{title}-{year}-{read_status}")
print(f"未读论文数量:{not_read_num}")
