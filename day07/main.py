from storage import load_job
from job_manager import (
    show_job,
    add_job,
    search_job,
    change_job_status,
    calculate_job_statistics,
    show_job_statistics,
    show_menu
)


def main():
    loaded_jobs=load_job()

    if loaded_jobs is None:
        print("程序无法加载数据，已停止运行！")
        return


    while True:
        show_menu()
        choice=input("请输入1-6的选项").strip()
        if choice=='1':
            show_job(loaded_jobs)
        elif choice=='2':
            add_job(loaded_jobs)
        elif choice=='3':
            search_job(loaded_jobs)
        elif choice=='4':
            change_job_status(loaded_jobs)
        elif choice=='5':
            show_job_statistics(loaded_jobs)
        elif choice=='6':
            print("退出程序")
            break
        else:
            print("输入不符合系统规定，请重新输入!")
if __name__=='__main__':
    main()

