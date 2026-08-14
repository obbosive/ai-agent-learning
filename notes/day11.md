# Day 11 学习笔记：结构化输出与最小 Agent 闭环

## 一、今日完成情况

Day 11 从普通大模型聊天程序进入了最小 Agent。模型不再只生成一段供人阅读的文字，而是先输出结构化决策，由 Python验证并调用本地工具，再根据真实工具结果生成最终回答。

今日主要文件：

```text
day11/
├── json_basics.py       # JSON字符串与Python字典的转换实验
├── intent_parser.py     # 意图识别、验证、工具调用与最终回答
└── paper_tools.py       # 论文搜索、统计和动作分发工具
```

今天已经完成：

- 区分 JSON字符串与Python字典；
- 理解序列化与反序列化；
- 区分 `json.load()` 与 `json.loads()`；
- 使用 `json.dumps()` 将Python工具结果转换成JSON字符串；
- 使用 DeepSeek JSON Object模式生成结构化决策；
- 理解 `response_format` 只约束输出格式，不能替代业务验证；
- 使用 `isinstance()`、字典 `.get()` 和动作白名单验证模型输出；
- 将用户自然语言解析为 `action` 和 `arguments`；
- 将界面输入与业务工具参数分开；
- 编写论文搜索和阅读统计两个只读工具；
- 编写 `execute_decision()` 完成动作分发；
- 禁止使用 `eval()` 或 `exec()` 直接执行模型文本；
- 将工具结果视为 Observation（观察结果）；
- 第二次调用模型，将真实工具结果组织成自然语言回答；
- 跑通“目标→决策→行动→观察→最终回答”的最小 Agent闭环；
- 认识到一次 Agent任务可能包含两次模型调用和对应费用。

## 二、JSON字符串与Python字典

下面是Python字典：

```python
python_data = {
    "action": "search_papers"
}
```

它已经是Python内存中的数据结构，可以直接访问：

```python
python_data["action"]
```

下面则是字符串：

```python
json_text = '{"action": "search_papers"}'
```

尽管字符串的内容看起来像字典，但它的真实类型仍然是：

```python
type(json_text)  # str
```

可以类比为：

```text
JSON字符串 = 纸上写着的一张结构化表格
Python字典 = 程序内存中真正可以操作的表格对象
```

大模型的：

```python
response.choices[0].message.content
```

首先永远是一段文本。即使文本内容符合JSON语法，它也不会自动变成Python字典。

## 三、外层API响应与内层模型文字

Day 9使用过：

```python
data = response.json()
```

`requests` 帮助程序将HTTP响应体中的JSON解析为Python对象。

大模型SDK的响应存在两层：

```text
外层：DeepSeek API响应对象
└── choices[0].message.content
    └── 内层：模型生成的文字
```

SDK已经解析外层，所以可以用点和下标访问 `choices[0].message`；但SDK不会擅自猜测 `content` 中的文本是否需要再次解析。

因此结构化输出需要：

```python
model_text = response.choices[0].message.content
decision = json.loads(model_text)
```

## 四、`json.loads()`与`json.load()`

### 从字符串解析

```python
decision = json.loads(model_text)
```

`json.loads()` 可以帮助记忆为“load string”。

- 输入：符合JSON语法的字符串或字节；
- 动作：解析JSON的结构和值；
- 返回：Python字典、列表、字符串、数字等对象；
- 副作用：不联网、不修改文件；
- 异常：格式错误时抛出 `json.JSONDecodeError`。

### 从文件读取

```python
with open("decision.json", "r", encoding="utf-8") as file:
    decision = json.load(file)
```

`json.load()` 接收已经打开的文件对象，内部需要调用文件的 `.read()`。

实际出现过：

```python
decision = json.load(model_text)
```

`model_text` 是字符串，没有 `.read()` 方法，因此出现：

```text
AttributeError: 'str' object has no attribute 'read'
```

核心区别：

```text
json.load(文件对象)       从文件读取并解析JSON
json.loads(JSON字符串)    直接解析JSON字符串
```

## 五、JSON语法与Python语法

合法JSON示例：

```json
{
    "action": "search_papers",
    "arguments": {
        "keyword": "Agent"
    }
}
```

常见规则：

- 对象字段名使用双引号；
- JSON字符串使用双引号；
- 对象使用大括号；
- 数组使用方括号；
- 布尔值是 `true` 和 `false`；
- 空值是 `null`；
- 最后一项后面不能随意添加逗号。

Python打印字典时可能显示：

```python
{'is_read': False}
```

而标准JSON应该是：

```json
{"is_read": false}
```

两者表达的信息相似，但语法和数据载体不同。

## 六、序列化与反序列化

今天学习的两个方向：

```text
JSON字符串
   │ json.loads()
   ▼
Python对象
   │ json.dumps()
   ▼
JSON字符串
```

### 反序列化

```python
decision = json.loads(model_text)
```

将文字恢复成Python对象，便于程序读取字段、验证和执行。

### 序列化

```python
result_text = json.dumps(result, ensure_ascii=False)
```

`json.dumps()`：

- 输入：Python字典、列表等对象；
- 动作：按照JSON规则序列化；
- 返回：JSON字符串；
- 副作用：不会自动写文件；
- 异常：对象无法JSON序列化时可能抛出 `TypeError`。

`ensure_ascii=False` 保留中文字符，避免显示为大量 `\uXXXX` 转义。

## 七、结构化输出模式

第一次模型调用：

```python
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
```

如果只在提示词中说“返回JSON”，模型可能额外输出说明或Markdown代码块，使整个字符串无法被 `json.loads()` 直接解析。

```python
response_format={"type": "json_object"}
```

用于要求输出采用JSON对象形式。不过它不能保证：

- `action` 一定属于程序允许的动作；
- 所有字段都存在；
- 参数类型符合业务要求；
- 模型不会选择危险动作；
- 字段值一定符合真实业务含义。

因此必须区分：

```text
格式正确 ≠ 业务正确 ≠ 可以安全执行
```

## 八、模型决策协议

本次规定的统一决策格式：

```json
{
    "action": "search_papers",
    "arguments": {
        "keyword": "Agent"
    }
}
```

- `action`：模型建议程序执行的动作；
- `arguments`：执行该动作需要的参数；
- `keyword`：论文搜索工具需要的关键词。

当前允许：

```text
search_papers      按标题关键词搜索论文
show_statistics    查看阅读统计
unknown            无法识别用户需求
```

不需要参数的动作也返回空字典：

```json
{
    "action": "show_statistics",
    "arguments": {}
}
```

统一格式可以让Python后续逻辑更简单，也便于测试和扩展。

## 九、为什么模型输出必须视为不可信输入

下面也是合法JSON：

```json
{
    "action": "delete_all_files",
    "arguments": {}
}
```

JSON解析器只能判断格式，不能判断动作是否安全。

正确原则：

```text
模型负责提出建议
Python负责验证、授权和执行
```

禁止：

```python
eval(model_text)
exec(model_text)
```

也不应该根据任意模型字符串动态取得并运行系统中的任意函数。工具范围必须由程序提前定义。

## 十、决策验证

验证函数：

```python
def validate_decision(decision):
    if not isinstance(decision, dict):
        return "决策最外层必须是字典"

    action = decision.get("action")
    arguments = decision.get("arguments")

    allowed_actions = [
        "search_papers",
        "show_statistics",
        "unknown"
    ]

    if action not in allowed_actions:
        return f"不允许执行动作：{action}"

    if not isinstance(arguments, dict):
        return "arguments必须是字典"

    if action == "search_papers":
        keyword = arguments.get("keyword")

        if not isinstance(keyword, str):
            return "搜索关键词必须是字符串"

        if not keyword.strip():
            return "搜索关键词不能为空"

    return None
```

### `isinstance()`

```python
isinstance(decision, dict)
```

检查对象是否属于指定类型，返回布尔值，不修改对象。

### 字典 `.get()`

```python
action = decision.get("action")
```

字段存在时返回值，不存在时默认返回 `None`。验证外部数据时，它比立即使用 `decision["action"]` 更适合，因为缺少字段不会立刻触发 `KeyError`。

### 验证函数的返回约定

```text
验证失败 → 返回错误字符串
验证成功 → 返回None
```

调用：

```python
validation_error = validate_decision(decision)

if validation_error:
    print(f"决策验证失败：{validation_error}")
else:
    # 只有这里允许执行工具
```

## 十一、工具函数为什么要显式接收参数

Day 6版本的搜索函数会在函数内部再次调用 `input()`：

```python
def search_papers(papers):
    keyword = input("请输入关键词")
```

Agent已经从用户自然语言中提取出关键词，因此工具更适合写成：

```python
def search_papers(papers, keyword):
```

职责分离：

```text
意图识别器：理解自然语言并提取参数
工具函数：接收明确参数并完成业务操作
界面代码：负责input和print
```

显式输入和返回值让函数更容易：

- 被Agent调用；
- 被普通菜单调用；
- 编写自动化测试；
- 在不同界面中复用；
- 理解副作用。

## 十二、论文工具

### 搜索工具

```python
def search_papers(papers, keyword):
    matched_papers = []

    for paper in papers:
        if keyword.lower() in paper["title"].lower():
            matched_papers.append(paper)

    return matched_papers
```

- 输入：论文列表和关键词字符串；
- 动作：遍历论文并匹配标题；
- 返回：所有匹配论文组成的新列表；
- 副作用：不修改原论文列表，不写文件。

`return` 必须位于循环结束之后。若放在 `if` 内，函数找到第一篇匹配论文就结束，无法收集后续匹配项；完全不匹配时还可能隐式返回 `None`。

### 统计工具

```python
def calculate_statistics(papers):
    total_count = len(papers)
    read_count = 0

    for paper in papers:
        if paper["is_read"]:
            read_count += 1

    return {
        "total_count": total_count,
        "read_count": read_count,
        "not_read_count": total_count - read_count
    }
```

输入论文列表，返回结构化统计结果，不修改数据。

## 十三、动作分发器

```python
def execute_decision(decision, papers):
    action = decision["action"]
    arguments = decision["arguments"]

    if action == "search_papers":
        keyword = arguments["keyword"]
        return search_papers(papers, keyword)

    if action == "show_statistics":
        return calculate_statistics(papers)

    if action == "unknown":
        return {
            "message": "无法识别这个论文管理需求"
        }
```

分发器把模型生成的符号动作：

```text
"search_papers"
```

映射为程序提前允许的函数调用：

```python
search_papers(papers, keyword)
```

模型不能直接执行函数，真正的控制权仍在Python代码中。

## 十四、Observation：工具观察结果

模型决定搜索后，真实结果来自Python数据：

```python
result = execute_decision(decision, papers)
```

例如：

```python
[
    {
        "title": "Agent Survey",
        "year": 2024,
        "is_read": False
    }
]
```

这份工具结果就是 Agent工作流中的 Observation。它不是模型凭记忆编写的答案，而是本地工具对真实数据执行后得到的证据。

## 十五、为什么需要第二次模型调用

程序内部列表和字典适合机器处理，但最终用户更希望看到自然语言：

```text
找到1篇匹配论文：Agent Survey，发表于2024年，目前未读。
```

所以需要将：

```text
用户原始需求 + 工具真实结果
```

发送给第二次模型调用，让模型只负责表达，不允许编造工具结果之外的信息。

```python
result_text = json.dumps(result, ensure_ascii=False)

final_messages = [
    {
        "role": "system",
        "content": (
            "你是一个论文管理助手。"
            "请根据用户原始需求和工具执行结果，用简洁中文回答。"
            "只能使用工具结果中存在的信息，不能编造数据。"
        )
    },
    {
        "role": "user",
        "content": f"""
用户原始需求：
{user_request}

工具执行结果：
{result_text}

请生成最终回答。
"""
    }
]
```

第二次请求不再设置JSON Object模式，因为这次需要普通自然语言答案。

## 十六、为什么使用两套消息

第一次system职责：

```text
只输出JSON决策
```

第二次system职责：

```text
根据工具结果输出自然语言回答
```

如果继续使用第一套messages，模型可能继续遵守“只能输出JSON”，与最终回答任务冲突。因此建立独立的 `final_messages`，让两个模型调用各自职责明确。

## 十七、最小Agent完整数据流

```text
用户自然语言需求
        ↓
第一次模型调用：意图识别
        ↓
JSON字符串
        ↓ json.loads()
Python决策字典
        ↓ validate_decision()
白名单和参数验证
        ↓
execute_decision()
        ↓
Python工具执行真实操作
        ↓
Observation列表或字典
        ↓ json.dumps()
Observation JSON字符串
        ↓
第二次模型调用：组织最终回答
        ↓
面向用户的自然语言答案
```

这与 Agent研究中的基本结构已经对应：

```text
Goal → Action → Observation → Answer
```

当前版本由Python手动编排这些步骤，尚未使用原生Tool Calling协议，但核心思想已经出现。

## 十八、两次调用与费用

一次用户任务包含：

1. 决策模型调用；
2. 本地工具执行；
3. 最终回答模型调用。

本地工具本身不产生模型Token费用，但两次模型请求分别计费。实际项目需要衡量：

- 是否所有结果都需要第二次模型润色；
- 简单统计能否由Python模板直接输出；
- 是否需要思考模式；
- system和工具结果是否过长；
- 能否缓存或复用某些内容。

## 十九、控制流与缩进

最终回答必须位于验证成功分支中：

```python
if validation_error:
    print("验证失败")
else:
    result = execute_decision(decision, papers)
    result_text = json.dumps(result, ensure_ascii=False)
    final_messages = [...]
    final_response = client.chat.completions.create(...)
    final_answer = final_response.choices[0].message.content
```

如果第二次请求放在 `else` 外面，验证失败时 `final_messages` 根本没有创建，却仍然会被使用，可能引发 `NameError`。更重要的是，验证失败就不应该继续执行工具或额外调用模型。

## 二十、响应字段复盘

错误写法：

```python
final_response.choice[0].message.content
```

正确写法：

```python
final_response.choices[0].message.content
```

`choices` 是复数，因为API结果设计为候选回答列表。当前取第一个候选：

```text
final_response
└── choices
    └── [0]
        └── message
            └── content
```

错误信息中的：

```text
Did you mean: 'choices'?
```

是Python提供的有效诊断线索，应结合Traceback中的代码行定位问题。

## 二十一、个人复盘与注意事项

1. 新函数必须先弄清输入类型。`json.load()` 和 `json.loads()` 名字只差一个字母，但前者接收文件，后者接收字符串。
2. 模型输出的JSON首先仍是字符串；“看起来结构化”不等于已经是Python数据结构。
3. JSON Object模式只解决格式的一部分问题，不能代替字段、类型、动作权限和业务含义验证。
4. 模型输出属于外部不可信输入。任何动作都必须经过白名单，不能直接 `eval()`、`exec()` 或动态执行任意名字。
5. 工具应显式接收参数并返回数据，不应把 `input()`、业务逻辑和打印全部绑在一个函数里。
6. 搜索函数要在遍历全部数据后返回结果；单个成功案例可能掩盖只能返回第一项的控制流问题。
7. 工具结果是Agent回答的事实基础。模型只能组织表达，不能补造结果中不存在的信息。
8. 第一次模型调用负责决策，第二次负责表达。两个system职责不同，应该使用不同消息列表。
9. 一次Agent任务可能包含多次模型调用，设计时必须关注成本和延迟。
10. `choice` 与 `choices` 的错误说明，读取SDK对象时必须尊重真实层级，不能仅凭单词含义猜字段。
11. 成功路径能运行不等于失败路径安全。缩进和变量创建位置决定验证失败后是否仍会继续执行。
12. 使用AI辅助时，不仅要看最终输出，还要打印中间类型、决策、参数和工具结果，用证据理解每一步。

## 二十二、当前版本的限制与后续方向

当前程序已经形成最小闭环，但仍有这些限制：

- 使用的是内存模拟论文，不是真实 `papers.json`；
- 每次运行只处理一个用户请求；
- `json.loads()` 尚可进一步增加 `JSONDecodeError` 处理；
- 两次模型调用都可以补充连接与API状态异常处理；
- 只支持两个只读工具和一个unknown分支；
- 没有对修改或删除动作加入用户确认；
- 由Python手写JSON决策协议，尚未学习原生Tool Calling；
- 没有自动记录每次动作、参数、结果和耗时；
- 没有针对工具函数和验证函数编写完整测试。

这些不是当天失败，而是下一阶段可以逐步扩展的工程方向。

## 二十三、独立综合复习题

### 题目 1：智能图书查询路由器

背景：图书管理程序支持 `search_books`、`show_statistics` 和 `unknown` 三个动作。用户通过自然语言提出需求，模型返回包含 `action` 与 `arguments` 的JSON对象。

任务：设计决策格式、system规则、JSON解析与验证流程，但暂时不执行工具。

验收标准：

- 能区分模型 `content` 字符串与解析后的Python字典；
- 使用JSON Object模式并在提示词中明确字段和示例；
- `action` 只允许三个白名单值；
- `arguments` 必须是字典；
- 搜索动作必须包含非空字符串关键词；
- 不使用 `eval()` 或 `exec()`；
- 能解释格式正确为什么不代表业务安全。

### 题目 2：文件与字符串的JSON读取

背景：程序同时接收两种数据：模型返回的JSON字符串，以及磁盘上的 `config.json` 文件。开发者混用了 `json.load()` 与 `json.loads()`。

任务：分别为两种输入选择正确函数，并设计异常提示。

验收标准：

- 字符串使用 `json.loads()`；
- 已打开文件对象使用 `json.load()`；
- 能解释字符串没有 `.read()` 为什么会报错；
- 捕获并说明 `JSONDecodeError`；
- 能将Python结果重新用 `json.dumps()` 转成JSON字符串；
- 中文序列化时合理使用 `ensure_ascii=False`。

### 题目 3：安全的天气工具执行器

背景：天气Agent允许模型选择 `get_current_weather`、`get_forecast` 或 `unknown`。天气工具要求城市名称字符串，预报工具还要求1到7之间的整数天数。

任务：编写验证器与分发器，确保模型不能调用其他动作，也不能传入错误参数。

验收标准：

- 检查最外层对象、动作和参数类型；
- 城市不能为空；
- 预报天数必须是整数且位于1到7；
- 验证失败不会执行任何工具；
- 分发器使用明确的白名单分支；
- 工具函数显式接收参数，不在内部重新询问用户；
- 能说明模型为何没有直接执行函数的权限。

### 题目 4：多结果搜索函数诊断

背景：商品搜索函数在找到第一条结果后立刻 `return`，单条测试可以通过，但实际数据库可能有多个匹配商品；无匹配时程序收到 `None`。

任务：定位控制流问题并改写函数，使其总是返回列表。

验收标准：

- `return` 位于整个循环结束之后；
- 多条匹配全部收集；
- 无匹配返回空列表而不是 `None`；
- 原始数据不会被修改；
- 至少设计“多个匹配”和“零个匹配”两个测试场景；
- 能解释为什么单个成功案例没有发现问题。

### 题目 5：工具结果驱动的客服Agent

背景：订单客服Agent先识别用户意图，再调用订单查询工具。工具返回订单状态、物流公司和预计时间组成的字典。用户需要一段简洁自然语言，而模型不得编造工具未返回的信息。

任务：设计“决策→工具→Observation→最终回答”的两次模型调用流程。

验收标准：

- 第一次模型调用只负责结构化决策；
- 决策验证通过后才执行订单工具；
- 使用 `json.dumps()` 将工具结果转换成字符串；
- 第二套system明确禁止编造；
- 第二次调用接收用户原始问题和真实工具结果；
- 最终回答读取 `choices[0].message.content`；
- 验证失败时不会执行工具或第二次模型调用；
- 能说明两次模型调用带来的成本和职责差异。

## 二十四、复习题参考思路

### 题目 1 参考思路

要求模型统一返回 `{"action": ..., "arguments": ...}`，设置JSON对象输出，再对 `content` 使用 `json.loads()`。验证最外层是字典，使用 `.get()` 取字段，通过允许动作列表检查权限；搜索动作额外验证关键词类型和空值。任何验证失败都只输出错误，不进入执行阶段。

### 题目 2 参考思路

模型结果已经在内存中，是字符串，因此使用 `json.loads(model_text)`；文件需要先 `open()`，再把文件对象交给 `json.load(file)`。两者都可能因为JSON语法问题产生 `JSONDecodeError`。需要交给模型或网络传输的Python对象可以用 `json.dumps(data, ensure_ascii=False)` 序列化。

### 题目 3 参考思路

允许动作写死在程序中。先检查 `decision` 和 `arguments` 的字典类型，再按动作检查城市和天数。只有验证函数返回成功时，分发器才通过 `if/elif` 调用提前定义的两个天气函数；`unknown` 返回明确消息，其他动作被拒绝。

### 题目 4 参考思路

建立空结果列表，完整遍历所有商品，只在匹配时 `append()`，循环结束后统一 `return matched_items`。用两条都含同一关键词的数据验证返回长度为2，再用不存在的关键词验证结果严格等于空列表。

### 题目 5 参考思路

第一次调用使用意图识别system和JSON模式。解析、验证后调用订单工具，将结果序列化。第二次使用全新的消息列表，其中system要求只依据Observation回答；user消息同时包含原问题和结果JSON。第二次不需要JSON模式，直接提取自然语言 `content`。整个第二阶段放在验证成功分支内。
