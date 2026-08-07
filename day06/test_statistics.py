from paper_manager import calculate_statistics

def check_statistics(papers,expected):
    original_papers=[]
    for paper in papers:
        original_papers.append(paper.copy())
    result=calculate_statistics(papers)

    assert result==expected
    assert papers==original_papers


def test_empty_papers( ):
    papers=[]
   
    expected={
        "total_count":0,
        "read_count":0,
        "not_read_count":0,
        "read_rate":0
    }
    check_statistics(papers,expected)

def test_mixed_papers():
    papers = [
    {"title": "Paper A", "is_read": True},
    {"title": "Paper B", "is_read": False},
    ] 
    expected={
    "total_count": 2,
    "read_count": 1,
    "not_read_count": 1,
    "read_rate": 50.0,
    }
    check_statistics(papers,expected)

def test_all_read():
    papers = [
    {"title": "Paper A", "is_read": True},
    {"title": "Paper B", "is_read": True},
    ]     
  
    expected={
    "total_count": 2,
    "read_count": 2,
    "not_read_count": 0,
    "read_rate": 100.0,
    }
    check_statistics(papers,expected)

def test_all_unread():
    papers = [
    {"title": "Paper A", "is_read": False},
    {"title": "Paper B", "is_read": False},
    ]     
   
    expected={
    "total_count": 2,
    "read_count": 0,
    "not_read_count": 2,
    "read_rate": 0.0,
    }
    check_statistics(papers,expected)

def run_tests():
    test_empty_papers()
    print("通过：空列表")

    test_mixed_papers()
    print("通过：混合状态")

    test_all_read()
    print("通过：全部已读")

    test_all_unread()
    print("通过：全部未读")

    print("全部统计测试通过！")


if __name__ == "__main__":
    run_tests()