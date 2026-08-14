import os
from dotenv import load_dotenv
from openai import OpenAI,APIConnectionError,APIStatusError

load_dotenv()
api_key=os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise ValueError("没有读取到deepseekapikey")

client=OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)
messages=[{"role":"system",
           "content":(
               "你是一名耐心的计算机学习助手。"
               "回答时先解释原理，再给出简短示例。"
               "使用中文回答，不要一次提供过多内容。"
           )}]
while True:
    user_message=input("\n你（输入exit退出）：").strip()
    if user_message.lower()=="exit":
        print("聊天结束")
        break
    if not user_message:
        print("问题不能为空！")
        continue

    messages.append({
        "role":"user",
        "content":user_message
    })
    try:
        response=client.chat.completions.create(
            model='deepseek-v4-flash',
            messages=messages,
            stream=False,
            reasoning_effort='low',
            extra_body={
                "thinking":{
                    "type":"enabled"
                }
            }
        )
    except APIConnectionError:
        messages.pop()
        print("网络连接失败，请检查网络连接后重试！")
        continue
    except APIStatusError as error:
        messages.pop()
        print(f"API请求失败，状态码{error.status_code}")
        continue
    # answer=response.choices[0].message.content
    # usage=response.usage
    message=response.choices[0].message
    reasoning=message.reasoning_content
    answer=message.content
    usage=response.usage

    messages.append({
        'role':'assistant',
        'content':answer
    })

    print("\n模型思考过程：")
    print(reasoning)

    print("\n模型最终回答：")
    print(answer)

    print("\nToken 用量：")
    print(f"输入：{usage.prompt_tokens}")
    print(f"输出：{usage.completion_tokens}")
    print(f"总计：{usage.total_tokens}")