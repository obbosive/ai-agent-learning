from agent_loop import execute_tool_safely,papers
print("\n参数不是合法json")
result=execute_tool_safely(
    "search_papers",
    '{"keyword":"Agent"',
    papers
)
print(result)

print("\n测试2：关键词是空字符串")
result=execute_tool_safely(
    "search_papers",
    '{"keyword":""}',
    papers
)
print(result)

print("\n测试3：模型申请未授权工具")
result=execute_tool_safely(
    "delete_all_papers" ,
    '{}',
    papers
)
print(result)