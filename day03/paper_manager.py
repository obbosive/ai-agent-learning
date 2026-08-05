import json
# papers=[
#         {"title":"ReAct","year":2022,"is_read":True},
#         {"title":"AutoGen","year":2023,"is_read":False},
#         {"title":"MetaGPT","year":2023,"is_read":False}
#         ]
def save_papers(papers):
     with open("day03/papers.json","w",encoding="utf-8") as file:
        json.dump(papers,file,ensure_ascii=False,indent=4)


def load_papers():
    with open("day03/papers.json","r",encoding="utf-8")as file:
        return json.load(file)
    

loaded_papers=load_papers()
for paper in loaded_papers:
    if paper["title"]=="MetaGPT":
        paper["is_read"]=True
save_papers(loaded_papers)
print(loaded_papers)
print(type(loaded_papers))
