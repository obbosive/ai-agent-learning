from storage import save_job
VALID_STATUS=('接受','拒绝')
def show_menu():
    print("----------------求职系统-------------------------")
    print('1.查看岗位')
    print('2.添加岗位')
    print('3.搜索岗位')
    print('4.修改投递状态')
    print('5.查看状态统计')
    print('6.退出系统')
    

def show_job(jobs):
    for job in jobs:
        print(f"公司:{job['company']}-位置：{job['location']}-状态：{job['status']}")


def add_job(jobs):
    company=input("请输入公司名称").strip()
    if not company:
        print("公司名称不能为空！")
        return
    
    location=input("请输入公司位置").strip()
    if not location:
        print("公司位置不能为空！")
        return
    status=input("请输入当前的状态").strip()
    if status not in VALID_STATUS:
        print("状态只能是拒绝或接受")
        return
    new_job={'company':company,
             'location':location,
             'status':status}
    jobs.append(new_job)
    save_job(jobs)

def search_job(jobs):
    search_company=input("请输入要寻找的公司职位的名称！").lower().strip()
    if not search_company:
        print("搜索词不能为空！")
        return
    if_find=False
    for job in jobs:
        if search_company in job['company'].lower():
            print(f"公司:{job['company']}-位置：{job['location']}-状态：{job['status']}")
            if_find=True
    if not if_find:
        print("没有找到")



def change_job_status(jobs):
    company=input("请输入想要改变工作职位状态的公司名称！").strip()
    if_find=False
    for job in jobs:
        if company==job['company']:
            if_find=True
    if not if_find:
        print("没找到要修改公司状态的公司名称")
        return


    change_status=input("请输入更改之后的状态").strip()
    if change_status not in VALID_STATUS:
        print("状态只能是拒绝或接受")
        return
    for job in jobs:
        if company==job['company']:
            job['status']=change_status
    save_job(jobs)
    print("状态修改成功！")

def calculate_job_statistics(jobs):
    accept_count=0
    refuse_count=0
    for job in jobs:
        if job['status']=='接受':
            accept_count+=1
    refuse_count=len(jobs)-accept_count
    return {
        f"accept_count":accept_count,
        f"refuse_count":refuse_count
    }

def show_job_statistics(jobs):
    statistics=calculate_job_statistics(jobs)
    print(statistics)
    

    
