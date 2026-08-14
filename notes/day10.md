# Day 10 学习笔记：大模型 API、对话上下文与思考模式

## 一、今日完成情况

Day 10 第一次让 Python 程序调用真正的大语言模型，并从一次最小请求逐步扩展成可以连续聊天的命令行程序。

今日主要文件：

```text
day10/
└── deepseek_chat.py    # DeepSeek命令行多轮聊天程序
```

今天已经完成：

- 使用 OpenAI Python SDK 调用兼容 OpenAI 接口的 DeepSeek 服务；
- 理解 SDK、API 地址、模型服务商和 API Key 之间的关系；
- 将 `DEEPSEEK_API_KEY` 安全保存在 `.env` 中；
- 理解 `.env.example` 只能保留变量名称，不能填写真实秘密；
- 创建并验证 `OpenAI` 客户端对象；
- 使用 `client.chat.completions.create()` 发起第一次付费模型请求；
- 理解 `model`、`messages`、`stream` 和 `extra_body` 的作用；
- 从 `response.choices[0].message.content` 读取最终回答；
- 从 `response.usage` 读取输入、输出和总 Token；
- 使用 `input()`、`while True`、`break` 和 `continue` 实现连续问答；
- 使用 `messages` 列表保存 `system`、`user` 和 `assistant` 消息；
- 理解所谓“记忆”其实是本地程序重新发送历史记录；
- 使用 system 消息规定模型身份、回答风格和行为规则；
- 使用 `APIConnectionError` 与 `APIStatusError` 处理常见请求失败；
- 请求失败时使用 `messages.pop()` 回滚未完成的用户消息；
- 开启 DeepSeek 思考模式并区分 `reasoning_content` 与 `content`；
- 观察到思考模式和历史记录都会增加 Token 消耗。

## 二、为什么 OpenAI SDK 可以调用 DeepSeek

这里安装的是：

```powershell
python -m pip install openai
```

但实际调用和收费方仍然是 DeepSeek。原因是 OpenAI SDK 本质上是一个可以配置的 HTTP 客户端，而 DeepSeek 实现了与 OpenAI Chat Completions 相兼容的接口格式。

```text
Python程序
   │
   │ 使用OpenAI SDK组织请求
   ▼
client = OpenAI(base_url="https://api.deepseek.com")
   │
   │ 请求实际发送到base_url
   ▼
DeepSeek服务器
   │
   ├── 使用DeepSeek API Key认证
   ├── 运行deepseek-v4-flash
   └── 从DeepSeek账户扣费
```

因此必须区分：

- `OpenAI`：这里是 Python 客户端类；
- `base_url`：决定请求真正发往哪家服务器；
- `api_key`：由目标服务商验证身份；
- `model`：目标服务商提供的模型 ID。

## 三、依赖与秘密配置

安装依赖后执行：

```powershell
python -m pip freeze > requirements.txt
```

当前项目使用的关键依赖包括：

```text
openai==2.53.0
python-dotenv==1.2.2
```

真实配置：

```env
# .env，不提交Git
DEEPSEEK_API_KEY=<真实Key>
```

公开模板：

```env
# .env.example，可以提交Git
DEEPSEEK_API_KEY=
```

`.env.example` 的作用是告诉其他开发者“程序需要什么变量”，不是提供可用秘密。即使 `.env` 已被忽略，也不能在终端、截图、日志或报错中打印真实 Key。

## 四、创建客户端对象

```python
load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    raise ValueError("没有读取到DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)
```

`OpenAI()` 的四个角度：

- 输入：API Key、基础地址和其他可选配置；
- 动作：创建一个知道如何认证、向哪里请求的客户端对象；
- 返回：`OpenAI` 客户端对象；
- 副作用：仅创建客户端时通常不会发送模型请求，也不会产生模型调用费用。

验证对象类型：

```python
print(type(client))
```

结果类似：

```text
<class 'openai.OpenAI'>
```

## 五、第一次聊天请求

```python
response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[
        {
            "role": "user",
            "content": "请用一句话解释什么是AI Agent。"
        }
    ],
    stream=False,
    extra_body={
        "thinking": {
            "type": "disabled"
        }
    }
)
```

调用链可以从左到右理解：

```text
client          已配置好的客户端
.chat           聊天资源
.completions    聊天补全资源
.create()       创建一次模型回复，真正联网并产生费用
```

主要参数：

- `model`：要使用的模型 ID；
- `messages`：完整对话消息列表；
- `stream=False`：等待生成完成后一次性返回结果；
- `extra_body`：向兼容服务传递额外参数；
- `thinking.type`：控制是否启用 DeepSeek 思考模式。

请求过程：

```text
Python参数
→ SDK序列化为JSON
→ 添加认证信息
→ 发送HTTP请求
→ DeepSeek运行模型
→ 返回JSON
→ SDK转换为Python响应对象
```

## 六、响应对象的层级

完整响应不是普通字符串，而是一个结构化对象：

```text
response
├── id
├── model
├── choices
│   └── [0]
│       ├── finish_reason
│       └── message
│           ├── reasoning_content
│           └── content
└── usage
    ├── prompt_tokens
    ├── completion_tokens
    └── total_tokens
```

读取最终答案：

```python
answer = response.choices[0].message.content
```

逐层含义：

```text
response
→ choices生成结果列表
→ [0]第一个生成结果
→ message模型消息
→ content最终回答文字
```

对象属性使用点，列表下标使用方括号：

```python
response.choices    # response是对象
choices[0]          # choices是列表
```

读取 Token：

```python
usage = response.usage

print(usage.prompt_tokens)
print(usage.completion_tokens)
print(usage.total_tokens)
```

`usage` 属于整次 `response`，不属于其中的一条 `message`，所以不能写成：

```python
usage = message.usage  # 错误层级
```

## 七、单轮输入与连续循环

获取并清理输入：

```python
user_message = input("你：").strip()
```

- `input()` 暂停程序，等待键盘输入，返回字符串；
- `.strip()` 返回删除首尾空白后的新字符串。

连续聊天框架：

```python
while True:
    user_message = input("\n你（输入exit退出）：").strip()

    if user_message.lower() == "exit":
        print("聊天结束")
        break

    if not user_message:
        print("问题不能为空")
        continue
```

控制流：

- `while True`：持续进入下一轮；
- `break`：结束整个循环；
- `continue`：结束当前轮，回到循环开头；
- 退出和空值判断必须放在 API 请求之前，避免无效调用。

实际出现过：

```python
if user_message.lower == "exit":  # 错误
```

`user_message.lower` 只是方法对象，`user_message.lower()` 才会执行方法并返回小写字符串。

```python
user_message.lower       # 方法对象
user_message.lower()     # 小写字符串
```

## 八、多轮对话与“记忆”的本质

初始化消息列表：

```python
messages = []
```

用户提问后：

```python
messages.append({
    "role": "user",
    "content": user_message
})
```

发送完整历史：

```python
response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=messages,
    stream=False,
    extra_body={"thinking": {"type": "disabled"}}
)
```

回答成功后：

```python
messages.append({
    "role": "assistant",
    "content": answer
})
```

`messages=messages` 左右含义不同：

- 左边：`create()` 规定的参数名；
- 右边：本地维护的聊天历史变量。

模型并没有在服务器上永久记住本程序的对话。每次请求都必须重新发送完整的 `messages`。程序关闭后，内存中的列表消失，当前版本的聊天记录也随之消失。

## 九、三种消息角色

```python
messages = [
    {
        "role": "system",
        "content": (
            "你是一名耐心的计算机学习助手。"
            "回答时先解释原理，再给出简短示例。"
            "使用中文回答，不要一次提供过多内容。"
        )
    }
]
```

三种角色：

- `system`：规定身份、任务、规则和回答风格；
- `user`：用户发送的消息；
- `assistant`：模型以前生成的回答。

system 消息通常位于列表最前面，每轮请求都会重新发送，因此也会消耗输入 Token。

### 相邻字符串与元组陷阱

正确的自动拼接没有逗号：

```python
content = (
    "第一句话。"
    "第二句话。"
)
```

结果是一个字符串：

```text
第一句话。第二句话。
```

如果加入逗号：

```python
content = (
    "第一句话。",
    "第二句话。",
)
```

结果是元组。元组发送到 JSON 后类似字符串数组，不符合普通文本消息的 `content` 格式，服务器会报告 `messages[0]` 类型错误。

Python 创建元组的关键是逗号，而不是圆括号：

```python
("a", "b")  # tuple
("a" "b")   # str，结果是"ab"
```

## 十、API异常与历史回滚

导入异常类型：

```python
from openai import OpenAI, APIConnectionError, APIStatusError
```

处理请求：

```python
messages.append({
    "role": "user",
    "content": user_message
})

try:
    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=messages,
        stream=False,
        extra_body={"thinking": {"type": "disabled"}}
    )

except APIConnectionError:
    messages.pop()
    print("网络连接失败，请检查网络后重试")
    continue

except APIStatusError as error:
    messages.pop()
    print(f"API请求失败，状态码：{error.status_code}")
    continue
```

- `APIConnectionError`：没有正常连接到服务器；
- `APIStatusError`：服务器返回失败状态；
- `messages.pop()`：删除列表最后一条刚加入但未得到回答的用户消息；
- `continue`：回到下一轮，不继续读取不存在的 `response`。

历史记录必须保持完整：

```text
成功：追加user → 请求成功 → 追加assistant
失败：追加user → 请求失败 → pop删除user → 下一轮
```

`pop()` 会修改原列表并返回被删除元素。空列表调用可能出现 `IndexError`，但此处刚执行过 `append()`，所以末尾必然存在本轮用户消息。

## 十一、思考模式

开启低强度思考：

```python
response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=messages,
    stream=False,
    reasoning_effort="low",
    extra_body={
        "thinking": {
            "type": "enabled"
        }
    }
)
```

- `thinking.type="enabled"`：开启思考模式；
- `reasoning_effort="low"`：设置较低的思考强度；
- 复杂推理、代码分析和 Agent 规划更可能受益；
- 简单问答不一定需要开启，因为思考会增加输出 Token 和费用。

读取两部分内容：

```python
message = response.choices[0].message
reasoning = message.reasoning_content
answer = message.content
usage = response.usage
```

必须区分：

```text
reasoning_content：模型思考模式生成的推理内容
content：最终交给用户的回答
```

历史记录中仍然只把最终回答保存为普通 assistant 消息：

```python
messages.append({
    "role": "assistant",
    "content": answer
})
```

不能把 `reasoning_content` 随意拼入普通 `content`，否则会增加后续 Token，并把内部推理文字错误地当成模型正式说过的话。

本次实际观察：同类题目关闭思考时输出约 364 Token，开启低强度思考并返回两部分内容后输出约 563 Token。速度仍然较快，因为使用的是 Flash 模型、思考强度低且问题简单。

## 十二、Token增长与上下文成本

第一轮和第二轮的输入 Token 曾出现：

```text
第一轮：40
第二轮：235
```

第二轮增长不是异常，因为发送内容已经变为：

```text
system规则
+ 第一轮用户问题
+ 第一轮模型回答
+ 第二轮用户问题
```

随着聊天历史增长：

- `prompt_tokens` 通常逐轮增加；
- 每轮费用可能增加；
- 请求时间可能增加；
- 最终可能接近模型上下文限制。

真实聊天产品通常需要限制历史轮数、总结旧消息或使用其他上下文管理方法。当前版本先保留完整历史，用于理解最基本的多轮机制。

## 十三、当前程序的数据流

```text
启动程序
→ 加载.env
→ 验证DEEPSEEK_API_KEY
→ 创建client
→ 初始化system消息
→ 等待用户输入
→ 检查exit或空值
→ append用户消息
→ 调用DeepSeek
   ├── 失败：pop用户消息并进入下一轮
   └── 成功：提取reasoning、answer、usage
→ append最终回答
→ 输出回答和Token
→ 回到下一轮
```

这已经是一个基础大模型应用的完整闭环：配置、输入、上下文、请求、响应解析、异常处理和成本观察都已包含。

## 十四、个人复盘与注意事项

1. 学习 SDK 时，必须先明确新函数的输入、动作、返回值和异常，不能只照着示例复制。
2. `OpenAI` 只是客户端类，不能仅根据类名判断实际服务商；真正目标由 `base_url`、Key和模型共同决定。
3. `response`、`message` 和 `usage` 有明确层级。`content` 属于消息，Token统计属于整次响应。
4. `lower` 与 `lower()` 不相同。看到点号后的方法名时，要判断自己是想取得方法，还是立即调用方法。
5. Python元组由逗号形成。为了排版而给相邻字符串加逗号，会悄悄改变数据类型，并最终导致 API 格式错误。
6. 多轮“记忆”不是模型永久记忆，而是本地 `messages` 列表每轮重新携带历史。程序退出后，当前内存记录消失。
7. 每次用户问题和模型回答必须成对保存。请求失败时如果不回滚用户消息，历史就会出现一个没有回答的悬空问题。
8. system 提示可以稳定影响输出方式，但它并不能保证模型绝对服从，也不会自动替代业务代码中的验证。
9. 思考模式与最终答案是两个字段。看到最终答案写了计算过程，不代表已经观察到了 `reasoning_content`。
10. 历史越长、system越长、思考越多，Token通常越多。开发大模型应用时必须同时关注正确性、延迟和成本。
11. 使用 AI 辅助写代码时，应通过响应结构、类型、Token和故障分支验证理解，而不是只以“程序运行了”作为掌握标准。

## 十五、独立综合复习题

### 题目 1：命令行语言学习助手

背景：你需要编写一个命令行英语学习助手。程序从环境变量读取模型 Key，用户可以连续提问，输入 `quit` 时退出。模型应始终用中文解释英语知识，并先给规则、再给两个简短例句。

任务：设计客户端初始化、system消息、输入循环、请求与输出流程。

验收标准：

- Key不写死在代码中，缺少时不会发送请求；
- system、user和assistant角色使用正确；
- 空输入不会调用模型；
- `quit` 在大小写不同或两侧带空格时仍能退出；
- 每轮保存用户问题和模型最终回答；
- 能解释为什么客户端初始化本身通常不产生模型费用。

### 题目 2：保证聊天历史的一致性

背景：客服机器人先把用户问题加入 `messages`，随后请求模型。网络偶尔中断，程序会捕获异常并继续下一轮。如果失败消息没有清理，模型下一次会看到一个从未回答的问题。

任务：设计成功和失败两条控制流，保证历史中始终是完整的 user/assistant 对话对。

验收标准：

- 请求前追加用户消息；
- 成功后才追加assistant消息；
- 连接失败和HTTP状态失败都能被处理；
- 失败时删除且只删除本轮用户消息；
- 异常后不会继续访问不存在的响应对象；
- 能说明 `pop()` 的动作、返回值和可能异常。

### 题目 3：诊断消息格式错误

背景：程序向兼容 Chat Completions 的服务发送以下system消息，服务器报告 `messages[0]` 类型错误：

```python
messages = [
    {
        "role": "system",
        "content": (
            "回答必须使用中文。",
            "回答不超过三句话。",
        )
    }
]
```

任务：判断 `content` 的真实 Python 类型，解释它进入JSON后的形态，并修复为一个字符串。

验收标准：

- 指出当前值是元组而不是字符串；
- 说明逗号在元组创建中的作用；
- 给出删除逗号自动拼接的写法；
- 额外给出使用 `+` 或 `"".join(...)` 的一种可行写法；
- 能解释为什么圆括号本身不一定创建元组。

### 题目 4：分析多轮对话的Token增长

背景：某聊天程序第一轮输入为50 Token，第二轮输入为310 Token。程序每轮都发送system消息和完整聊天历史，没有保存文件，也没有服务端会话ID。

任务：解释第二轮输入增长的组成，并提出两种控制长期Token成本的方法。

验收标准：

- 明确第二轮包含system、第一轮问答和第二轮问题；
- 不把Token增长错误归因于模型“偷偷记忆”；
- 能说明程序退出后内存历史为何消失；
- 至少提出限制最近轮数、总结旧消息中的一种方案；
- 说明减少上下文可能损失哪些信息。

### 题目 5：区分思考过程与最终答案

背景：一个推理模型返回 `reasoning_content`、`content` 和 `usage`。产品界面只应展示最终答案，但开发阶段希望观察思考模式是否启用，并统计调用成本。

任务：设计字段读取、终端调试输出和历史保存策略。

验收标准：

- 从消息对象读取 `reasoning_content` 与 `content`；
- 从外层响应读取 `usage`；
- 用户界面默认只展示最终 `content`；
- 普通assistant历史只保存最终回答；
- 能说明思考模式为何可能增加延迟和输出Token；
- 简单问答与复杂规划能够选择不同思考强度。

## 十六、复习题参考思路

### 题目 1 参考思路

使用 `.env` 和 `os.getenv()` 读取Key，创建带目标 `base_url` 的客户端。`messages` 首项放system规则，在循环中对输入执行 `strip()`，使用 `lower() == "quit"` 判断退出。有效问题先作为user加入历史，请求成功后把最终回答作为assistant加入历史。

### 题目 2 参考思路

把本轮user消息追加后进入 `try`。请求成功时提取答案并追加assistant；`APIConnectionError` 或 `APIStatusError` 中调用一次 `messages.pop()`，随后 `continue`。这样异常点后不会访问 `response`，历史也不会留下悬空user消息。

### 题目 3 参考思路

带逗号的多个字符串形成元组，序列化后类似JSON数组。删除字符串之间的逗号即可利用Python相邻字面量拼接；也可以写成 `"第一句" + "第二句"`，或对字符串列表调用 `"".join(...)`。圆括号主要用于分组，逗号才是元组的关键。

### 题目 4 参考思路

第二轮必须重新发送system、第一轮user、第一轮assistant和第二轮user，因此输入明显增长。可以只保留最近若干轮，也可以把早期对话总结成短消息；代价是模型可能忘记被删除的细节，或总结过程遗漏信息。

### 题目 5 参考思路

先取得 `message = response.choices[0].message`，从中读取思考和最终回答；Token必须从 `response.usage` 读取。调试时可以分别打印两部分，面向普通用户时只展示最终答案。历史中保存普通assistant的 `content`，并根据任务难度决定关闭思考或设置较低/较高强度。
