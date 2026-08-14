import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from paper_tools import execute_decision

def validate_decision(decision):
    if not isinstance(decision,dict):
        return "决策最外层必须是字典！"
    action=decision.get("action")
    arguments=decision.get("arguments")

    allowed_actions=[
        "search_papers",
        "show_statistics",
        "unknown"
    ]
    if action not in allowed_actions:
        return f"不允许执行动作{action}"
    if not isinstance(arguments,dict):
        return "arguments必须是字典！" 

    if action=="search_papers":
        keyword=arguments.get("keyword")
        if not isinstance(keyword,str):
            return "搜索关键词必须是字符串！"
        if not keyword.strip():
            return "搜索关键词不能为空！"
    return None

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    raise ValueError("没有读取到DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

papers = [
    {
        "title": "ReAct",
        "year": 2022,
        "is_read": True
    },
    {
        "title": "AutoGen",
        "year": 2023,
        "is_read": False
    },
    {
        "title": "Agent Survey",
        "year": 2024,
        "is_read": False
    }
]

user_request=input("请输入你的论文管理需求").strip()
if not user_request:
    raise ValueError("需求不能为空！")

messages = [
    {
        "role": "system",
        "content": """
你是一个论文管理系统的意图识别器。

你必须只输出json对象，不能输出解释或markdown代码块。

action只能是下面三个值之一：
1. search_papers：用户想根据关键词搜索论文
2. show_statistics：用户想查看论文阅读统计
3. unknown：无法识别用户意图

输出格式：
{
    "action": "search_papers",
    "arguments": {
        "keyword": "从用户需求中提取的关键词"
    }
}

如果动作不需要参数，arguments返回空对象：
{
    "action": "show_statistics",
    "arguments": {}
}
"""
    },
    {
        "role": "user",
        "content": user_request
    }
]

response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=messages,
    response_format={
        "type": "json_object"
    },
    stream=False,
    extra_body={
        "thinking": {
            "type": "disabled"
        }
    }
)

model_text = response.choices[0].message.content

print("\n模型返回的原始内容：")
print(model_text)
print(type(model_text))

decision = json.loads(model_text)

print("\n解析后的Python数据：")
print(decision)
print(type(decision))

validation_error=validate_decision(decision)
if validation_error:
    print(f"\n决策验证失败:{validation_error}")
else:
    print("\n决策验证通过")
    print(f"动作：{decision['action']}")
    print(f"参数：{decision['arguments']}")

    result = execute_decision(decision, papers)

    print("\n工具执行结果：")
    print(result)

    result_text=json.dumps(result,ensure_ascii=False)

    final_messages=[
        {
            "role":"system",
            "content":("你是一个论文管理助手。"
            "请根据用户的原始需求和工具执行结果，用简洁的中文回答用户。"
            "只能使用工具结果中存在的信息，不能编造论文或统计数据。"
                       )
                       
        },
        {"role":"user",
         "content":f"""
用户原始需求：
{user_request}

工具执行结果：
{result_text}

请生成最终回答。


"""}
    ]

    final_response=client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=final_messages,
        stream=False,
        extra_body={
            "thinking":{
                "type":"disabled"
            }
        }
    )

    final_answer=final_response.choices[0].message.content
    print("\nagent最终回答")
    print(final_answer)