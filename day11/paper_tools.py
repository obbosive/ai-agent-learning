def search_papers(papers,keyword):
    matched_papers=[]
    for paper in papers:
        if keyword.lower() in paper['title'].lower():
            matched_papers.append(paper)
    return matched_papers

def calculate_statistics(papers):
    total_count=len(papers)
    read_count=0
    for paper in papers:
        if paper['is_read']:
            read_count+=1
    not_read_count=total_count-read_count

    return {
        "total_count": total_count,
        "read_count": read_count,
        "not_read_count": not_read_count
    }

def execute_decision(decision,papers):
    action=decision['action']
    arguments=decision['arguments']

    if action=='search_papers':
        keyword=arguments['keyword']
        return search_papers(papers,keyword)

    if action=='show_statistics':
        return calculate_statistics(papers)

    if action=='unknown':
        return {
            "message": "无法识别这个论文管理需求"
        }