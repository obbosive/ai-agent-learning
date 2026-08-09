from job_manager import calculate_job_statistics


def check_statistics(jobs,expected):
    original_jobs=[]
    for job in jobs:
        original_jobs.append(job.copy())

    result=calculate_job_statistics(jobs)
    assert result==expected
    assert original_jobs==jobs


def test_empty():
    jobs=[]
    expected={'accept_count':0,'refuse_count':0}
    check_statistics(jobs,expected)

def test_half():
    jobs=[{'company':'alibaba','status':'接受'},
          {'company':'baidu','status':'拒绝'}]
    expected={'accept_count':1,'refuse_count':1}
    check_statistics(jobs,expected)

    
def test_accept():
    jobs=[{'company':'alibaba','status':'接受'},
          {'company':'baidu','status':'接受'}]
    expected={'accept_count':2,'refuse_count':0}
    check_statistics(jobs,expected)

def test_refuse():
    jobs=[{'company':'alibaba','status':'拒绝'},
          {'company':'baidu','status':'拒绝'}]
    expected={'accept_count':0,'refuse_count':2}
    check_statistics(jobs,expected)


def run_tests():
    test_empty()
    print("通过，空列表！")
    test_accept()
    print("通过全部接受！")
    test_refuse()
    print("通过全部拒绝！")
    test_half()
    print("通过一半接受一半拒绝！")

if __name__=="__main__":
    run_tests()
    
   