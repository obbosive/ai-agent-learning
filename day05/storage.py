import json
def save_papers(papers):
    with open("day05/papers.json","w",encoding="utf-8") as file:
        json.dump(papers,file,ensure_ascii=False,indent=4)


def load_papers():
    try:
        with open("day05/papers.json","r",encoding="utf-8")as file:
            return json.load(file)
    except FileNotFoundError:
        print("没有找到论文数据文件，暂时使用空列表")
        return []