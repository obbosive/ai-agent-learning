from storage import load_papers
from paper_manager import(
    add_paper,
    mark_paper_as_read,
    search_papers,
    show_papers
)
def show_menu():
    print("\n--------------论文管理器-----------------")
    print("1.查看论文。")
    print("2.添加论文。")
    print("3.标记论文为已读。")
    print("4.搜索论文。")
    print("5.退出程序。")

def main():
    loaded_papers=load_papers()
    while(True):
        show_menu()
        choice = input("请输入选择（1-5）：").strip()
        if choice=='1':
            show_papers(loaded_papers)
        elif choice=='2':
            add_paper(loaded_papers)
        elif choice=='3':
            mark_paper_as_read(loaded_papers)
        elif choice=='4':
            search_papers(loaded_papers)
        elif choice=='5':
            print("退出程序！")
            break
        else:
            print("无效选择，请重新输入。")
if __name__=="__main__":
    main()
