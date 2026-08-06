from storage import  save_papers

def show_papers(papers):
    if not papers:
        print("暂无论文数据。")
        return 
    else:
        for paper in papers:
            if paper["is_read"]:
                read_status = "已读"
            else:
                read_status = "未读"
            print(f"{paper['title']}|{paper['year']}|{read_status}")




def add_paper(papers):
    
        title=input("请输入论文标题").strip()
        if not title:
            print("标题不能为空，论文添加失败。")
            return
        year_text=input("请输入发表年份").strip()
        try:
            year=int(year_text)
        except ValueError:
                print("数据格式错误,年份必须是整数。")
                return
        new_paper={
        'title':title,
        'year':year,
        'is_read':False
        }
        papers.append(new_paper)
        save_papers(papers)
        print("论文保存成功！")



def mark_paper_as_read(papers):
    title=input("输入要标记的标题，标题不能为空").strip()
    if not title:
        print("标题不能为空！")
        return
    for paper in papers:
        if paper['title']==title:
            paper['is_read']=True
            save_papers(papers)
            print("标记成功")
            return
    print("没有找到该论文")





def search_papers(papers):
    keyword=input("请输入搜索关键词").strip()
    if not keyword:
        print("搜索词不能为空！")
        return
    matched_list=[]
    for paper in papers:
        if keyword.lower() in paper['title'].lower():
            matched_list.append(paper)
    if matched_list:
        show_papers(matched_list)
    else:
        print("没有找到匹配的论文！")


