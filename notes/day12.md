# Day 12 学习笔记：DeepSeek 原生 Tool Calling

## 一、今日完成情况

Day 12 用 DeepSeek 原生 Tool Calling 协议重写了 Day 11 的 Agent 决策过程。模型不再按照我们自定义的提示词返回 `action` JSON，而是通过专门的 `message.tool_calls` 字段提出工具调用申请。

今日主要文件：

```text
day12/
└── tool_call_demo.py    # 两个论文工具的原生Tool Calling完整闭环
```

今天已经完成：

- 使用 `tools` 参数向模型声明可用工具；
- 理解工具声明只是说明书，不是真实Python函数；
- 理解 Tool Calling 中字段名由协议预先规定；
- 认识 JSON Schema 中的 `type`、`properties`、`description` 和 `required`；
- 观察 `message.content` 与 `message.tool_calls`；
- 从工具调用对象中读取函数名、参数字符串和调用ID；
- 使用 `json.loads()` 把参数字符串转换成Python字典；
- 使用白名单分发器执行真实Python函数；
- 使用 `role="tool"` 和 `tool_call_id` 回传真实工具结果；
- 发起第二次模型请求并生成最终自然语言回答；
- 同时声明并执行 `search_papers` 与 `show_statistics`；
- 使用循环处理同一轮中的多个工具调用；
- 完成搜索、统计以及“搜索+统计”的三种测试。

## 二、Day 11 与 Day 12 的区别

Day 11 使用自定义协议：

```text
提示词要求模型输出JSON
→ message.content得到JSON字符串
→ Python读取action和arguments
→ Python自行分发工具
```

Day 12 使用原生协议：

```text
tools参数声明工具
→ 模型在message.tool_calls中申请调用
→ Python读取name和arguments
→ Python执行真实工具
→ role="tool"回传结果
→ 模型生成最终回答
```

两种方式的共同原则仍然是：

```text
模型负责提出调用建议
Python负责验证和真实执行
```

原生 Tool Calling 的优势是调用请求与普通文本分别存放在专门字段中，工具名称、参数和调用ID也采用统一协议，不需要我们在提示词中手写整套动作输出格式。

## 三、`tools` 是工具说明书

一个工具声明的基本结构：

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_papers",
            "description": "根据论文标题关键词搜索论文",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "要在论文标题中搜索的关键词"
                    }
                },
                "required": ["keyword"]
            }
        }
    }
]
```

翻译成人话：

```text
这里有一个函数工具
名字是search_papers
作用是按标题关键词搜索论文
调用时需要一个keyword参数
keyword必须是字符串并且不能省略
```

`tools` 不会自动创建下面这个函数：

```python
def search_papers(...):
```

也不会自动搜索数据。它只向模型描述“程序允许申请哪些工具以及参数格式”。真实函数仍须由开发者编写，调用也仍由Python控制。

## 四、普通Python字典外形与协议语义

工具声明在Python中只是嵌套的列表和字典。从Python语法看，下面两个字段是平等的同级键值对：

```python
"keyword": {
    "type": "string",
    "description": "论文标题搜索关键词"
}
```

仅看Python语法，无法推导谁负责约束、谁负责说明。它们的功能来自 JSON Schema 和 Tool Calling 协议的预先约定：

| 固定字段名 | 协议规定的含义 |
|---|---|
| `type` | 说明工具类型或数据类型，具体含义取决于所在层级 |
| `name` | 工具对模型公开的名字 |
| `description` | 用自然语言说明工具或参数的用途 |
| `parameters` | 描述函数的整个参数包 |
| `properties` | 描述参数包里允许有哪些字段 |
| `required` | 声明哪些参数不能省略 |

因此不能擅自把：

```python
"description"
```

改成：

```python
"explanation"
```

也不能把 `type` 改成自创的 `datatype`。这些字段名不是普通业务变量名，而是接口识别的标准词汇。

## 五、三个不同层级的 `type`

今天出现了多个 `type`：

```python
{
    "type": "function",
    "function": {
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string"
                }
            }
        }
    }
}
```

它们的含义由所在位置决定：

```text
外层type=function
    说明这是函数类型的工具

parameters中的type=object
    说明所有参数组成一个JSON对象

keyword中的type=string
    说明keyword的值必须是字符串
```

模型不会只提交：

```json
"Agent"
```

而会提交带参数名的参数包：

```json
{
    "keyword": "Agent"
}
```

这个整体是JSON对象，对应Python字典，所以 `parameters` 中需要：

```python
"type": "object"
```

`properties` 描述对象内部字段，`required` 决定其中哪些字段必须出现。

## 六、`description` 的作用

`type` 负责结构约束：

```python
"type": "string"
```

`description` 负责语义说明：

```python
"description": "要在论文标题中搜索的关键词"
```

两者格式上是平级字段，但协议功能不同。`description` 不会成为真实函数参数。模型实际生成的是：

```json
{
    "keyword": "Agent"
}
```

而不是把 `type` 和 `description` 一起传给函数。一个好的参数说明应清楚表达值的业务含义，帮助模型从自然语言中提取正确内容。

## 七、无参数工具

统计工具不需要模型提供参数：

```python
{
    "type": "function",
    "function": {
        "name": "show_statistics",
        "description": "统计论文总数、已读数量和未读数量",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
}
```

`parameters` 仍然是对象，但内部没有字段：

```python
"properties": {}
```

模型生成的参数字符串通常是：

```json
{}
```

这说明“统一使用参数对象”与“工具实际没有参数”并不冲突。

## 八、第一次模型请求

```python
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
```

核心新增参数是：

```python
tools=tools
```

左边是SDK规定的请求参数名，右边是当前程序保存工具说明书的Python变量。

Day 12 先关闭思考模式，是为了集中理解基础调用协议。思考模式与工具调用结合时，后续请求还需要完整处理 `reasoning_content`，不应在基础闭环尚未掌握时同时增加这个变量。

## 九、`content` 与 `tool_calls` 可以同时存在

第一次响应：

```python
message = response.choices[0].message
```

需要观察：

```python
message.content
message.tool_calls
```

模型可能只返回工具调用，此时 `content` 可能是 `None`；也可能同时返回一句说明和工具调用，例如：

```text
content：我来帮你搜索相关论文。
tool_calls：search_papers(keyword="Agent")
```

所以 `content is None` 不是工具调用成功的必要条件。真正判断模型是否申请调用工具，应检查：

```python
message.tool_calls
```

模型在普通文字中说“我会搜索”也不代表真实函数已经执行。

## 十、工具调用对象的层级

单个调用对象的结构：

```text
tool_call
├── id
├── type
└── function
    ├── name
    └── arguments
```

正确访问方式：

```python
tool_call.id
tool_call.type
tool_call.function.name
tool_call.function.arguments
```

今天出现过：

```python
tool_call.function.id
```

这会报错，因为 `id` 不属于内层 `function`，而属于外层 `tool_call`。读取SDK对象时应根据打印出的真实结构逐层访问，不能只凭字段名字猜路径。

## 十一、为什么 `arguments` 看起来像字典却是字符串

```python
arguments_text = tool_call.function.arguments
```

示例内容：

```python
'{"keyword": "Agent"}'
```

真实类型：

```python
str
```

解析：

```python
arguments = json.loads(arguments_text)
```

得到：

```python
{"keyword": "Agent"}
```

真实类型：

```python
dict
```

然后才能安全地读取：

```python
keyword = arguments["keyword"]
```

这与 Day 11 的JSON知识完全相同：外观像结构化数据，不代表它已经是Python对象。

## 十二、真实工具与安全分发器

工具说明中的名字只是字符串：

```python
"search_papers"
```

它不是Python函数，不能写成：

```python
function_name(keyword)
```

也不能使用 `eval()` 或 `exec()` 动态执行模型内容。正确做法是白名单分发：

```python
def execute_tool(function_name, arguments, papers):
    if function_name == "search_papers":
        keyword = arguments.get("keyword")

        if not isinstance(keyword, str) or not keyword.strip():
            raise ValueError("搜索关键词必须是非空字符串")

        return search_papers(papers, keyword)

    if function_name == "show_statistics":
        return show_statistics(papers)

    raise ValueError(f"不允许调用工具：{function_name}")
```

工具声明和真实函数之间的连接由程序明确建立：

```text
模型返回工具名称字符串
→ Python检查白名单和参数
→ Python调用提前定义的真实函数
```

模型生成了符合 Schema 的参数，也仍应视为外部输入并进行业务验证。

## 十三、`return` 与 `print` 的区别

真实搜索函数：

```python
return matched_papers
```

`return` 是把值交给调用者，不会自动显示在终端。调用：

```python
tool_result = search_papers(papers, keyword)
```

结果被保存到 `tool_result`。只有执行：

```python
print(tool_result)
```

终端才会显示它。今天曾经因为函数内部没有打印而误以为函数没有执行，这说明调试时需要区分“程序是否产生返回值”和“终端是否显示返回值”。

## 十四、为什么需要回传完整 assistant 消息

Python执行工具后，需要先把模型原始消息加入历史：

```python
messages.append(message)
```

不能只追加：

```python
message.content
```

因为完整 `message` 中还保存了模型提出的 `tool_calls`。后续 `role="tool"` 消息必须有一条先前的工具调用申请可以对应。

## 十五、`role="tool"` 与 `tool_call_id`

工具结果首先需要转换成字符串：

```python
tool_result_text = json.dumps(
    tool_result,
    ensure_ascii=False
)
```

再加入消息：

```python
messages.append({
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": tool_result_text
})
```

字段作用：

- `role="tool"`：说明这不是用户文字或模型回答，而是工具执行结果；
- `tool_call_id`：说明结果对应模型提出的哪一次调用；
- `content`：工具执行结果的JSON文本。

`tool_call_id` 可以类比为取餐号：模型提出调用时获得一个编号，Python回传结果时携带相同编号，避免多个调用结果相互混淆。

## 十六、为什么需要第二次模型请求

第一次模型请求负责选择工具和生成参数，不能提前知道Python执行结果。Python执行完成并追加工具消息后，第二次请求：

```python
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
```

此时消息历史为：

```text
user：用户原始需求
assistant：模型提出工具调用
tool：Python返回真实结果
```

模型据此生成最终自然语言回答。一次完整任务通常会产生至少两次API调用，因此需要考虑两次请求的Token、费用和延迟。

## 十七、多个工具调用

`message.tool_calls` 是列表，因为一轮中可能有多个调用：

```text
tool_calls
├── search_papers(keyword="Agent")
└── show_statistics()
```

不能只处理：

```python
message.tool_calls[0]
```

完整处理方式：

```python
messages.append(message)

for tool_call in message.tool_calls:
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    tool_result = execute_tool(function_name, arguments, papers)

    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps(tool_result, ensure_ascii=False)
    })
```

关键顺序：

1. 完整的 assistant 消息只追加一次；
2. 循环处理每一个工具调用；
3. 每个调用都追加一条带自己ID的工具结果；
4. 循环结束后才发起第二次模型请求。

如果第二次请求错误地放进循环，每执行一个工具就会请求一次模型；既破坏完整的结果集合，又增加费用。

## 十八、当前完整数据流

```text
用户自然语言需求
        ↓
第一次DeepSeek请求（携带tools）
        ↓
assistant message.tool_calls
        ↓
逐个读取name、arguments、id
        ↓ json.loads()
Python参数字典
        ↓ execute_tool()
白名单验证与真实函数执行
        ↓
Python工具结果
        ↓ json.dumps()
role="tool" + tool_call_id
        ↓
第二次DeepSeek请求
        ↓
Agent最终自然语言回答
```

## 十九、语法报错位置为什么不一定是根因

工具 Schema 是多层嵌套字典，今天出现过：

```python
"description": "统计论文数量"
"parameters": {
```

真正错误是上一行缺少英文逗号，但编辑器可能标记 `parameters` 或后面的括号。原因是解析器从上向下读取，直到遇见下一个不能合法接续的符号时，才确定语法已经无法成立。

排查原则：

```text
报错位置 = 解析器发现无法继续的位置
不一定等于真正写错的位置
```

当错误落在新字段、冒号或右括号上时，应优先检查上一行的英文逗号、引号和括号。多个红线可能是同一个早期错误造成的级联现象，应先修最靠上的第一处问题。

## 二十、VS Code 类型提示的边界

OpenAI SDK 返回的是第三方库定义的复杂对象。Pylance有时可以根据类型定义提示 `id`、`name` 和 `arguments`，但不能保证每次都自动弹出补全。

项目曾短暂启用：

```json
"python.analysis.typeCheckingMode": "basic"
```

它能发现一部分属性错误，但也会把普通 `messages` 和 `tools` 字典与SDK的严格类型声明进行比较，产生大量不影响实际运行的红线。为了不干扰当前学习，已经恢复原设置。

现阶段更可靠的调试方式：

- 打印完整对象观察层级；
- 对中间变量使用 `type()`；
- 读取Traceback最靠后的异常类型和代码行；
- 在输入 `.` 后使用 `Ctrl + Space` 尝试补全；
- 修改后保存文件，再重新运行验证。

## 二十一、个人复盘与注意事项

1. `tools` 看起来是普通字典，但字段名属于协议，不能随意创造或替换。
2. 相同的 `type` 出现在不同层级会有不同含义，必须先判断它在描述工具、参数包还是单个参数。
3. `keyword` 内同时存在 `type` 与 `description`；它们语法平级，但一个负责约束，一个负责解释。
4. `parameters` 描述整个参数包，所以即使只有一个关键词，也要说明参数包是 `object`。
5. 无参数工具通常使用空的 `properties`，模型参数会是 `{}`；不能假设所有工具都有 `keyword`。
6. `message.content` 可以与 `message.tool_calls` 同时存在，不能用 `content is None` 判断是否调用工具。
7. `tool_call.id` 属于外层调用对象，不属于 `tool_call.function`。对象字段路径应以真实打印结构为依据。
8. `tool_call.function.arguments` 是JSON字符串，必须 `json.loads()` 后才能按字典取参数。
9. 模型只申请调用，不执行函数；看到工具名和参数不等于工具已经运行。
10. `return` 不负责显示。判断函数是否执行，应检查调用语句、返回值和后续打印，而不是只看函数内部有没有输出。
11. 工具名必须经过白名单分发，禁止用 `eval()`、`exec()` 执行模型生成的名字或代码。
12. 先追加完整 assistant 消息，再追加工具结果；不能只保存普通 `content`。
13. 每条工具结果必须带对应的 `tool_call_id`，多个工具不能共用或混淆ID。
14. assistant消息只追加一次，工具结果在循环中逐条追加，第二次模型请求在循环结束后执行。
15. 编辑器标出的语法位置可能是发现问题的位置，缺逗号时要优先检查上一行。
16. 更强的静态类型检查不一定适合所有学习阶段；大量第三方SDK类型提示可能遮蔽真正需要关注的问题。

## 二十二、当前版本的限制与后续方向

当前程序已经支持同一轮中的多个工具调用，但仍有这些工程限制：

- 每次运行只接收一个用户请求；
- 模型没有申请工具时，目前按错误处理，尚未优雅支持直接回答；
- `json.loads()` 可以补充 `JSONDecodeError` 处理；
- 两次API请求尚未统一处理连接异常和状态码异常；
- 当前只处理一轮工具调用，第二次响应若再次要求调用工具，还没有继续循环；
- 论文数据仍是内存列表，没有连接 Day 6 的真实JSON文件；
- 工具定义、业务函数、分发器和主流程仍在同一文件；
- 只读工具风险较低，未来修改和删除工具需要权限边界与用户确认；
- 尚未记录工具名称、参数、结果、耗时和异常等运行日志。

这些限制不会否定今天的成果。Day 12 的目标是理解并跑通标准 Tool Calling协议，而不是一次写出完整生产级Agent框架。

## 二十三、独立综合复习题

### 题目 1：天气助手的工具声明

背景：程序有一个真实函数 `get_weather(city, unit)`，其中城市必填，温度单位只能由程序后续验证为 `celsius` 或 `fahrenheit`。模型需要根据用户问题生成原生工具调用。

任务：设计完整的 `tools` 声明，并解释每一层 `type`、`properties`、`description` 和 `required` 的作用。

验收标准：

- 外层声明函数工具；
- 参数包声明为对象；
- `city` 和 `unit` 都声明为字符串；
- 两个参数都有清楚的语义说明；
- `city` 被声明为必填；
- 能说明Python字典语法为什么不能自行决定这些字段的协议含义；
- 能写出模型调用参数可能形成的JSON对象。

### 题目 2：识别工具申请而不是假装执行

背景：客服模型返回普通文字“我正在查询订单”，同时 `tool_calls` 中申请调用 `get_order(order_id="A1024")`。新开发者把普通文字当成查询已经完成。

任务：设计一段观察与判断逻辑，正确区分普通文字、工具调用申请和真实工具结果。

验收标准：

- 分别读取 `message.content` 与 `message.tool_calls`；
- 不用 `content is None` 作为唯一判断依据；
- 能从第一个调用中读取 `id`、函数名和参数文本；
- 使用 `json.loads()` 得到参数字典；
- 明确说明模型没有执行真实订单函数；
- 只有Python函数返回后才称为真实查询结果。

### 题目 3：安全的校园信息工具分发器

背景：校园助手允许 `search_courses(keyword)` 和 `show_calendar()` 两个只读工具。模型也可能生成未授权的 `delete_course` 或把关键词生成为数字。

任务：编写安全分发器，将工具名称和参数映射到真实Python函数。

验收标准：

- 使用明确的 `if/elif` 白名单；
- 搜索关键词必须是非空字符串；
- 无参数日历工具不读取不存在的 `keyword`；
- 未授权名称抛出清楚异常；
- 不使用 `eval()`、`exec()` 或任意动态执行；
- 函数通过返回值提供结果，不依赖内部打印；
- 能解释 Schema约束为什么仍不能替代Python验证。

### 题目 4：多工具结果关联

背景：旅行助手在一条assistant消息中同时申请 `get_weather(city="北京")` 和 `search_trains(origin="保定", destination="北京")`。两个工具返回不同数据，必须一起交给模型生成行程建议。

任务：设计从遍历 `message.tool_calls` 到发起第二次模型请求的消息组织流程。

验收标准：

- 完整assistant消息只追加一次；
- 使用循环处理两个工具调用；
- 每个调用分别解析参数并执行白名单函数；
- 每个结果都转成JSON字符串；
- 每条 `role="tool"` 消息使用自己的 `tool_call_id`；
- 第二次模型请求位于循环之后；
- 能画出最终messages中的角色顺序；
- 能解释错配ID可能造成什么问题。

### 题目 5：工具调用程序的故障诊断

背景：一个工具Agent出现四个问题：`tool_call.function.id` 报属性错误、参数看起来像字典却无法按键读取、工具函数返回了结果但终端没有显示、嵌套字典在 `parameters` 处出现语法红线。

任务：分别定位四类问题并给出验证办法。

验收标准：

- 正确区分 `tool_call.id` 与 `tool_call.function.name/arguments`；
- 使用 `type()` 证明参数文本是字符串；
- 使用 `json.loads()` 完成转换；
- 区分 `return` 与 `print`；
- 对语法红线优先检查上一行逗号、引号和括号；
- 先处理最靠上的语法错误，避免被级联红线误导；
- 能说明静态提示、运行时异常和打印调试各自能发现什么问题。

## 二十四、复习题参考思路

### 题目 1 参考思路

使用函数工具外层结构，`parameters` 的根类型为 `object`。在 `properties` 中分别描述 `city` 与 `unit`，每个参数包含 `type="string"` 和业务说明；`required` 至少包含 `city`。模型参数可能是 `{"city": "北京", "unit": "celsius"}`。字段的含义来自JSON Schema协议，而不是Python缩进本身。

### 题目 2 参考思路

先保留并打印完整 `message`。普通 `content` 只表示模型的表达；`tool_calls` 才是正式调用申请。读取 `tool_call.function.name` 和 `arguments`，把参数文本解析成字典，再由Python白名单调用 `get_order()`。函数返回值才是Observation，不能把“我正在查询”当成结果。

### 题目 3 参考思路

分发器接收 `function_name`、`arguments` 和程序内部数据。搜索分支使用 `.get()` 读取并验证关键词，再调用真实搜索函数；日历分支不读取关键词；其余名称统一拒绝。Schema帮助模型生成参数，Python验证决定是否授权执行。

### 题目 4 参考思路

先把包含两个调用的assistant消息追加到历史。遍历调用列表，分别解析、执行并构造 `role="tool"` 消息，每条消息使用当前调用的ID。全部结果追加完成后再请求模型。角色顺序是 `user → assistant(tool_calls) → tool(weather) → tool(trains)`。

### 题目 5 参考思路

根据对象树可知ID位于外层，函数名和参数位于 `function` 内层。参数使用 `type()` 检查后由 `json.loads()` 解析。函数的 `return` 只把值交给调用者，需要显式 `print()` 才显示。语法分析器往往在无法继续解析的位置报错，所以新字段或括号被标红时，应检查上一行缺少的逗号、引号或括号；修复第一个错误后再重新观察其余诊断。
