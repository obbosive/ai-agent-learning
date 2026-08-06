import json
def save_papers(papers):
    with open("day04/papers.json","w",encoding="utf-8") as file:
        json.dump(papers,file,ensure_ascii=False,indent=4)


def load_papers():
    try:
        with open("day04/papers.json","r",encoding="utf-8")as file:
            return json.load(file)
    except FileNotFoundError:
        print("没有找到论文数据文件，暂时使用空列表")
        return []
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
def show_menu():
    print("\n--------------论文管理器-----------------")
    print("1.查看论文。")
    print("2.添加论文。")
    print("3.标记论文为已读。")
    print("4.退出程序。")
loaded_papers=load_papers()
while(True):
    show_menu()
    # choice=input("请输入用户选择，如果选择是字符串 "1"：查看论文否则如果是 "2"：添加论文否则如果是 "3"：标记论文为已读否则如果是 "4"：提示程序退出用 break 结束循环否则：提示无效选择")
    choice = input("请输入选择（1-4）：").strip()
    if choice=='1':
        show_papers(loaded_papers)
    elif choice=='2':
        add_paper(loaded_papers)
    elif choice=='3':
        mark_paper_as_read(loaded_papers)
    elif choice=='4':
        print("退出程序！")
        break
    else:
        print("无效选择，请重新输入。")

# loaded_papers = load_papers()
# show_papers(loaded_papers)

# # add_paper(loaded_papers)  # 暂时不调用添加功能
# mark_paper_as_read(loaded_papers)

# show_papers(loaded_papers)