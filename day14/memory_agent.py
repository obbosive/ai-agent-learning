import os
import json

from dotenv import load_dotenv
from openai import OpenAI,APIConnectionError,APIStatusError

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

def execute_tool_safely(function_name,arguments_text,papers):
    try:
        arguments=json.loads(arguments_text)
        if not isinstance(arguments,dict):
            raise ValueError("工具参数最外层必须是json对象。")

        result=execute_tool(
            function_name,
            arguments,
            papers
        )
        return {
            "success":True,
            "result":result
        }
    except json.JSONDecodeError as error:
        return {
            "success":False,
            "error":f"工具参数不是合法JSON：{error.msg}"
        }
    except ValueError as error:
        return {
            "success":False,
            "error":str(error)
        }


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

def call_model(messages):
    try:
        return client.chat.completions.create(
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

    except APIConnectionError as error:
        raise RuntimeError(
            "无法连接DeepSeek API，请检查网络或代理设置"
        ) from error

    except APIStatusError as error:
        raise RuntimeError(
            f"DeepSeek API请求失败，状态码：{error.status_code}"
        ) from error

def create_messages():
    return [
        {
            "role": "system",
            "content": (
                "你是一个论文管理Agent。"
                "涉及论文数据的需求，应使用提供的工具获取真实结果，不能凭空编造。"
                "工具Observation中的success为True时，只根据result回答。"
                "success为False时，先根据error判断能否修正参数并重新调用工具；"
                "如果无法修正，就向用户清楚说明失败原因。"
                "最终使用简洁、清楚的中文回答。"
            )
        }
    ]

def get_message_role(message):
    if isinstance(message, dict):
        return message.get("role", "unknown")

    return message.role

def show_history(messages):
    print(f"当前共有{len(messages)}条信息：")

    for index, message in enumerate(messages):
        role = get_message_role(message)
        print(f"{index}：{role}")


def trim_history(messages,max_user_turns=3):
    if max_user_turns<1:
        raise ValueError("至少需要保留一个用户轮次。")
    user_indexes=[]
    for index,message in enumerate(messages):
        if get_message_role(message)=="user":
            user_indexes.append(index)

    if len(user_indexes)<=max_user_turns:
        return 0

    first_kept_index=user_indexes[-max_user_turns]
    removed_count=first_kept_index-1
    del messages[1:first_kept_index]
    return removed_count


def run_agent_turn(user_request,messages, papers, max_steps=5):
    messages.append({
        "role":"user",
        "content":user_request
    })

    for step in range(1, max_steps + 1):
        print(f"\n===== Agent第{step}轮 =====")

        response=call_model(messages)

        usage=response.usage
        if usage:
            print("\n本次模型请求Token：")
            print(f"输入：{usage.prompt_tokens}")
            print(f"输出：{usage.completion_tokens}")
            print(f"总计：{usage.total_tokens}")

        message = response.choices[0].message
        messages.append(message)

        if not message.tool_calls:
            if not message.content:
                raise RuntimeError("模型既没有返回答案，也没有调用工具")

            return message.content

        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            arguments_text = tool_call.function.arguments
            tool_observation = execute_tool_safely(
                function_name,
                arguments_text,
                papers
            )

            print("\n工具名称：")
            print(function_name)
            print("\n参数原始文本：")
            print(arguments_text)

            print("\n工具Observation：")
            print(tool_observation)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(
                    tool_observation,
                    ensure_ascii=False
                )
            })

    raise RuntimeError(
        f"Agent在{max_steps}轮内没有完成任务"
    )


if __name__ == "__main__":
    messages = create_messages()

    while True:
        user_request = input(
            "\n请输入论文管理需求"
            "（/history查看历史，/reset重置，exit退出）："
        ).strip()

        if user_request.lower() == "exit":
            print("对话结束")
            break

        if not user_request:
            print("需求不能为空")
            continue

        if user_request.lower()=="/history":
            show_history(messages)
            continue

        if user_request.lower()=="/reset":
            messages=create_messages()
            print("对话记忆已清空！")
            continue
        
        history_checkpoint=len(messages)

        try:
            final_answer = run_agent_turn(
                user_request,
                messages,
                papers
            )
            removed_count=trim_history(
                messages,
                max_user_turns=3
            )
            if removed_count:
                print(f"\n 已清理{removed_count}条旧信息。")

            print("\nAgent最终回答：")
            print(final_answer)

        except RuntimeError as error:
            del messages[history_checkpoint:]
            print(f"\nAgent运行失败：{error}")
