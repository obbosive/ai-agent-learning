import os
import json

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise ValueError("没有读取到DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

papers = [
    {"title": "ReAct", "year": 2022, "is_read": True},
    {"title": "AutoGen", "year": 2023, "is_read": False},
    {"title": "Agent Survey", "year": 2024, "is_read": False}
]


def search_papers(papers, keyword):
    matched_papers = []

    for paper in papers:
        if keyword.lower() in paper["title"].lower():
            matched_papers.append(paper)

    return matched_papers

def show_statistics(papers):
    total_count = len(papers)
    read_count = 0

    for paper in papers:
        if paper["is_read"]:
            read_count += 1

    not_read_count = total_count - read_count

    return {
        "total_count": total_count,
        "read_count": read_count,
        "not_read_count": not_read_count
    }

def execute_tool(function_name,arguments,papers):
    if function_name=="search_papers":
        keyword=arguments.get("keyword")
        if not isinstance(keyword,str) or not keyword.strip():
            raise ValueError("搜索关键词必须是非空字符串。")
        return search_papers(papers,keyword)

    if function_name=="show_statistics":
        return show_statistics(papers)
    raise ValueError(f"不允许调用工具{function_name}")

tools=[{
    "type":"function",
    "function":{
        "name":"search_papers",
        "description":"根据论文标题关键词搜索论文。",
        "parameters":{
            "type":"object",
            "properties":{
                "keyword":{
                    "type":"string",
                    "description":"要在论文标题中搜索关键词"
                }
            },"required":["keyword"]        }
    }
},
{"type":"function",
 "function":{
     "name":"show_statistics",
     "description":"统计论文总数，已读数量和未读数量。",
     "parameters":{
         "type":"object",
         "properties":{}
     }
 }}
]

user_request = input("请输入你的论文管理需求：").strip()

if not user_request:
    raise ValueError("需求不能为空")

messages = [
    {
        "role": "user",
        "content": user_request
    }
]

response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=messages,
    tools=tools,
    stream=False,
    extra_body={
        "thinking": {
            "type": "disabled"
        }
    }
)

message = response.choices[0].message

print("\n模型的普通文本回答：")
print(message.content)

print("\n模型生成的工具调用请求：")
print(message.tool_calls)

if not message.tool_calls:
    raise ValueError("模型没有生成工具调用请求")


messages.append(message)

for tool_call in message.tool_calls:
    function_name = tool_call.function.name
    arguments_text = tool_call.function.arguments
    arguments = json.loads(arguments_text)

    tool_result = execute_tool(
        function_name,
        arguments,
        papers
    )

    print("\n工具名称：")
    print(function_name)

    print("\n解析后的参数：")
    print(arguments)

    print("\n真实工具执行结果：")
    print(tool_result)

    tool_result_text = json.dumps(
        tool_result,
        ensure_ascii=False
    )

    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": tool_result_text
    })
final_response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=messages,
    tools=tools,
    stream=False,
    extra_body={
        "thinking": {
            "type": "disabled"
        }
    }
)

final_answer = final_response.choices[0].message.content

print("\nAgent最终回答：")
print(final_answer)