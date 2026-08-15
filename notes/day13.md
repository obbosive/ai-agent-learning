# Day 13 学习笔记：有界 Agent 循环与分层异常处理

## 一、今日完成情况

Day 13 将 Day 12 固定的“两次模型请求”升级成了可以连续决策的 Agent 循环。程序不再假设第二次模型响应必然是最终答案，而是每轮都重新检查模型是否还需要调用工具，直到模型返回普通答案或达到最大轮数。

今日主要文件：

```text
day13/
├── agent_loop.py          # 有界Agent循环、工具执行和API异常处理
└── test_tool_errors.py    # 不调用API的工具失败路径测试
```

今天已经完成：

- 将固定两次请求重构为通用Agent循环；
- 使用 `max_steps` 限制模型请求轮数；
- 支持模型第一轮直接回答；
- 支持一轮调用一个或多个工具；
- 支持工具执行后进入下一轮继续决策；
- 把 `messages` 作为一次Agent任务的运行状态；
- 使用统一的成功/失败Observation信封；
- 区分JSON解析错误、参数错误和未授权工具；
- 只捕获可以合理处理的预期异常；
- 使用 `if __name__ == "__main__":` 保护程序入口；
- 在不调用API的情况下测试失败路径；
- 增加Agent的system行为规则；
- 区分system软规则、工具Schema和Python硬权限；
- 将模型请求封装为 `call_model()`；
- 区分工具执行错误与模型API错误；
- 捕获连接异常和API状态异常；
- 理解异常沿函数调用链向外传播的过程；
- 正常验证直接回答、组合工具和最终回答路径。

## 二、Day 12 固定流程的限制

Day 12 的程序写死了：

```text
第一次请求模型
→ 执行工具
→ 第二次请求模型
→ 直接读取第二次响应的content
```

它隐含假设：

```text
第二次模型响应必然是最终答案，不会再次调用工具。
```

真实任务可能需要多轮行动。例如：

```text
第1轮：搜索论文
第2轮：根据搜索结果继续查询统计或其他信息
第3轮：组织最终回答
```

如果第二次响应仍包含 `tool_calls`，Day 12 程序只读取 `content` 就会遗漏新的工具申请。因此真正通用的Agent不能按固定次数编排，而要根据每一轮响应决定下一步。

## 三、Agent循环的核心状态机

Day 13 的流程：

```text
初始化messages
        ↓
请求模型
        ↓
保存assistant消息
        ↓
检查message.tool_calls
   ├── 没有：content是最终答案，return
   └── 有：逐个执行工具并追加tool消息
                         ↓
                     下一轮
```

对应骨架：

```python
def run_agent(user_request, papers, max_steps=5):
    messages = [...]

    for step in range(1, max_steps + 1):
        response = call_model(messages)
        message = response.choices[0].message
        messages.append(message)

        if not message.tool_calls:
            return message.content

        for tool_call in message.tool_calls:
            # 解析、执行并回传每个工具结果

    raise RuntimeError("Agent超过最大轮数")
```

它不是一个只重复执行代码的普通循环，而是一个由模型响应驱动状态转换的循环。

## 四、`messages` 为什么是Agent运行状态

`messages` 在循环外创建：

```python
messages = [
    {"role": "system", "content": "..."},
    {"role": "user", "content": user_request}
]
```

每轮继续追加：

```text
assistant：模型本轮决定
tool：工具执行结果
assistant：下一轮决定或最终回答
```

示例：

```text
messages
├── system：Agent行为规则
├── user：搜索Agent论文并统计阅读情况
├── assistant：申请search_papers和show_statistics
├── tool：search_papers的结果
├── tool：show_statistics的结果
└── assistant：最终自然语言答案
```

模型没有程序内存，下一轮只能通过我们重新发送的消息历史知道之前发生了什么。因此：

```text
messages = Agent当前任务的可见记忆和运行轨迹
```

如果错误地在循环内部重新创建 `messages`，每一轮都会忘掉之前的工具申请和Observation，Agent无法形成连续推理过程。

## 五、一次任务、一轮和一次工具调用

这三个概念不能混淆：

- 一次任务：从用户提出需求到Agent最终回答的完整过程；
- 一轮：Agent向模型发送一次请求并收到一次响应；
- 一次工具调用：某轮响应中的一个 `tool_call`。

一轮可以同时包含多个工具调用：

```text
Agent第1轮
├── search_papers
└── show_statistics
```

它仍然只消耗一次模型请求轮次，但Python会执行两个真实工具。工具执行完成后，Agent进入第2轮请求模型生成最终答案。

## 六、为什么使用有界循环

没有边界的写法：

```python
while True:
```

在Agent中有风险，因为模型可能持续申请工具：

```text
调用工具 → 返回结果 → 再次调用 → 再次调用……
```

每轮都可能产生Token费用和网络等待，因此使用：

```python
for step in range(1, max_steps + 1):
```

达到上限仍没有答案时：

```python
raise RuntimeError(
    f"Agent在{max_steps}轮内没有完成任务"
)
```

`max_steps` 限制的是模型请求轮数，不是工具数量。一轮即使调用两个工具，也只占用一个step。

有界循环体现了一个重要工程原则：

```text
Agent自主性必须存在资源和权限边界。
```

## 七、直接回答路径

模型不一定需要工具。例如用户询问：

```text
你好，请介绍你能做什么。
```

如果模型返回：

```python
message.tool_calls is None
message.content == "我是一个论文管理Agent……"
```

程序直接返回：

```python
if not message.tool_calls:
    if not message.content:
        raise RuntimeError("模型既没有返回答案，也没有调用工具")

    return message.content
```

这里使用 `return` 而不是单纯 `break`：

- `break` 只结束当前循环；
- `return` 同时结束循环和整个 `run_agent()`，并把最终答案交给调用者。

如果既没有工具调用也没有普通答案，响应不满足程序预期，因此抛出运行错误，而不是静默返回 `None`。

## 八、成功和失败Observation信封

真实工具成功时统一返回：

```python
{
    "success": True,
    "result": 实际工具结果
}
```

预期失败时统一返回：

```python
{
    "success": False,
    "error": "失败原因"
}
```

这种结构可以称为“结果信封”：外层字段先说明状态，内部再携带结果或错误。

成功与失败字段必须保持语义一致。今天曾经出现：

```python
{
    "success": True,
    "error": result
}
```

它在Python语法上合法，但业务语义矛盾。正确写法是：

```python
{
    "success": True,
    "result": result
}
```

这类错误说明：

```text
语法正确 ≠ 数据协议正确 ≠ 业务含义正确
```

## 九、安全执行函数

```python
def execute_tool_safely(function_name, arguments_text, papers):
    try:
        arguments = json.loads(arguments_text)

        if not isinstance(arguments, dict):
            raise ValueError("工具参数最外层必须是JSON对象")

        result = execute_tool(
            function_name,
            arguments,
            papers
        )

        return {
            "success": True,
            "result": result
        }

    except json.JSONDecodeError as error:
        return {
            "success": False,
            "error": f"工具参数不是合法JSON：{error.msg}"
        }

    except ValueError as error:
        return {
            "success": False,
            "error": str(error)
        }
```

函数说明：

- 输入：函数名字符串、参数JSON字符串、程序内部论文数据；
- 动作：解析、验证并执行白名单工具；
- 成功返回：带 `success=True` 的字典；
- 预期失败返回：带 `success=False` 的字典；
- 副作用：当前工具为只读，不修改论文列表；
- 未捕获异常：真正的代码Bug仍然暴露为Traceback。

## 十、为什么要先验证参数最外层

`json.loads()` 成功不代表结果一定是字典：

```python
json.loads('["Agent"]')   # list
json.loads('123')         # int
json.loads('"Agent"')     # str
```

Tool Calling参数协议要求参数包是JSON对象，所以解析后继续检查：

```python
if not isinstance(arguments, dict):
    raise ValueError("工具参数最外层必须是JSON对象")
```

只有格式和最外层类型都符合要求，才进入白名单工具分发。

## 十一、异常捕获顺序

```python
except json.JSONDecodeError as error:
    ...

except ValueError as error:
    ...
```

`JSONDecodeError` 本身属于 `ValueError` 的更具体子类。因此必须先捕获具体异常，再捕获范围更广的异常。

如果顺序反过来：

```python
except ValueError:
    ...
except json.JSONDecodeError:
    ...
```

JSON解析错误会提前被第一个 `ValueError` 分支接住，后面的专门分支永远没有机会执行。

可以记忆为：

```text
具体异常在前，宽泛异常在后。
```

## 十二、为什么不捕获所有 `Exception`

看似省事的写法：

```python
except Exception as error:
    return {"success": False, "error": str(error)}
```

会把开发者自己的Bug也包装成普通工具失败。例如：

- 论文字段名拼错导致 `KeyError`；
- 变量名写错导致 `NameError`；
- SDK对象层级写错导致 `AttributeError`。

如果全部吞掉，程序可能继续运行，但真实Bug被隐藏。当前只捕获：

- 模型参数JSON错误；
- 已知业务验证与白名单错误。

其余异常保留Traceback，便于开发阶段定位。

## 十三、工具失败为什么仍然回传模型

无论成功或失败，循环都会追加：

```python
messages.append({
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": json.dumps(
        tool_observation,
        ensure_ascii=False
    )
})
```

失败不是“什么也没发生”，而是一条真实Observation。例如：

```python
{
    "success": False,
    "error": "搜索关键词必须是非空字符串。"
}
```

下一轮模型可以根据它：

- 修正参数后重新调用；
- 选择其他工具；
- 无法修正时向用户解释原因。

这体现Agent循环与普通函数调用的重要差别：环境反馈不仅包括成功数据，也包括失败信息。

## 十四、system规则、工具Schema和Python权限

Day 13 增加了system消息：

```text
涉及论文数据时使用真实工具
success=True时根据result回答
success=False时根据error判断是否重试
不能凭空编造数据
使用简洁中文回答
```

三层职责：

```text
system消息
→ 规定Agent整体行为方式，是语言层面的软规则

tools Schema
→ 描述工具能力、参数结构和字段语义

Python验证与白名单
→ 决定真实权限和是否执行，是硬安全边界
```

system和Schema可以提高模型遵守规则的概率，但不能替代Python验证。安全性不能建立在“模型应该听话”上。

## 十五、主入口保护与可导入模块

```python
if __name__ == "__main__":
    user_request = input(...)
    final_answer = run_agent(...)
```

直接执行：

```powershell
python .\day13\agent_loop.py
```

此时：

```python
__name__ == "__main__"
```

所以运行交互入口。

测试文件导入：

```python
from agent_loop import execute_tool_safely, papers
```

此时模块中的 `__name__` 是模块名，不等于 `"__main__"`，所以不会触发 `input()` 和API请求，只加载函数与数据供测试使用。

主入口保护实现了：

```text
同一个文件既可以作为程序直接运行
也可以作为模块安全地被其他文件导入
```

## 十六、失败路径测试为什么不需要API

`test_tool_errors.py` 直接调用：

```python
execute_tool_safely(
    function_name,
    arguments_text,
    papers
)
```

测试了：

1. 参数JSON缺少右大括号；
2. 搜索关键词为空字符串；
3. 申请未授权的 `delete_all_papers`。

这些逻辑全部发生在本地Python中，不需要调用DeepSeek，也不会产生Token费用。测试关注的是确定性代码，就应尽量避免把不稳定且收费的外部API引入测试。

## 十七、相邻字符串自动拼接

第三个测试曾写成：

```python
execute_tool_safely(
    "delete_all_papers,"
    '{}',
    papers
)
```

逗号被写进第一个字符串内容，而不是放在引号外分隔参数。

Python允许相邻字符串字面量自动拼接：

```python
text = (
    "Hello, "
    "world!"
)

# 等价于
text = "Hello, world!"
```

因此原代码被解释为：

```python
"delete_all_papers,{}"
```

函数实际只收到两个位置参数，最终报：

```text
missing 1 required positional argument: 'papers'
```

正确写法：

```python
execute_tool_safely(
    "delete_all_papers",
    '{}',
    papers
)
```

这说明有些漏逗号不会成为语法错误，因为Python恰好存在另一种合法解释，问题只能在运行时暴露。

## 十八、模型API错误与工具错误的区别

工具错误：

```text
模型已经返回工具调用
→ Python解析或执行工具失败
→ 可以形成role="tool"的失败Observation
```

模型API错误：

```text
网络请求本身失败
→ 没有收到assistant消息
→ 不存在tool_call_id和可回传Observation
→ Python只能向用户报告Agent运行失败
```

两种错误不能使用同一处理方式。

## 十九、封装模型请求

```python
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
```

函数说明：

- 输入：当前消息历史；
- 动作：向DeepSeek发起一次模型请求；
- 返回：SDK的ChatCompletion对象；
- 副作用：联网、产生延迟、可能消耗Token；
- 异常：将底层SDK错误转换为程序层面的 `RuntimeError`。

封装后：

```python
response = call_model(messages)
```

让 `run_agent()` 聚焦于循环控制，而 `call_model()` 聚焦于API通信。

## 二十、连接异常与状态异常

```python
APIConnectionError
```

表示没有正常获得HTTP响应，常见原因：

- 网络中断；
- VPN或代理没有工作；
- DNS解析失败；
- 连接或读取超时。

```python
APIStatusError
```

表示服务器已经返回错误HTTP状态，例如：

- 401：身份验证或Key问题；
- 429：请求频率或额度限制；
- 5xx：服务器内部错误。

`error.status_code` 用于读取具体HTTP状态码。

## 二十一、异常传播与 `as error`

入口调用链：

```text
主程序try
└── run_agent()
    └── call_model()
        └── SDK网络请求
```

网络失败时：

```text
SDK抛出APIConnectionError
→ call_model捕获
→ call_model抛出RuntimeError
→ run_agent没有捕获，继续向外传播
→ 主程序except RuntimeError捕获
```

语法：

```python
except RuntimeError as error:
```

含义：

- `except RuntimeError`：只处理这种类型的异常；
- `as error`：把本次异常对象绑定到局部变量 `error`；
- `str(error)` 或f字符串会显示创建异常时的消息。

变量名不是固定的，也可以写成 `as e` 或 `as runtime_error`。

## 二十二、`raise ... from error`

```python
raise RuntimeError("无法连接DeepSeek API") from error
```

表示：

1. 对上层抛出更符合当前应用语义的 `RuntimeError`；
2. 保留原来的SDK异常作为新异常的原因。

如果异常最终未被捕获并显示完整Traceback，Python可以同时展示底层原因和上层解释，方便诊断。

这叫异常转换或异常链：底层库描述技术原因，上层应用描述对用户和业务的影响。

## 二十三、程序入口的最终处理

```python
try:
    final_answer = run_agent(
        user_request,
        papers
    )

    print("\nAgent最终回答：")
    print(final_answer)

except RuntimeError as error:
    print(f"\nAgent运行失败：{error}")
```

成功路径：

```text
run_agent正常return
→ 打印最终答案
→ except不执行
```

失败路径：

```text
run_agent内部抛出RuntimeError
→ try剩余代码立即停止
→ 进入except
→ 打印清楚的失败原因
```

入口只捕获程序能够合理展示的运行错误。其他未预料的开发错误保留Traceback。

## 二十四、关于自动重试

SDK本身会对部分临时网络错误、限流和服务器错误进行有限重试。如果应用层再随意添加重试循环，可能形成：

```text
SDK内部重试次数 × 应用外部重试次数
```

从而产生超出预期的请求次数、等待时间和Token费用。

此外，请求超时不一定表示服务器完全没有处理请求，也可能只是客户端没有收到响应。对具有修改副作用的工具或接口盲目重试，还可能造成重复操作。

当前策略是先使用SDK默认能力，重试后仍失败则向用户报告，不额外实现复杂重试。

## 二十五、个人复盘与注意事项

1. 固定“两次请求”只是演示闭环，通用Agent必须每轮重新检查 `tool_calls`。
2. `messages` 必须创建在循环外，否则模型每轮都会失去之前的工具调用和结果。
3. assistant消息每轮追加一次；该轮所有工具结果分别追加；完成后再进入下一轮。
4. 一轮可以包含多个工具调用，`max_steps` 限制模型轮数而不是工具数。
5. 没有 `tool_calls` 时才把 `content` 当作最终答案；既没有调用也没有答案属于异常响应。
6. 无限Agent循环会带来费用风险，必须设置最大轮数或其他资源预算。
7. 工具失败也是Observation，不应让所有可预期参数错误直接终止Agent。
8. 成功信封使用 `result`，失败信封使用 `error`；字段语义写反不会触发Python语法错误。
9. JSON解析成功后仍须检查最外层是否为字典，不能只验证语法。
10. 具体异常必须写在宽泛异常前面；`JSONDecodeError` 应早于 `ValueError`。
11. 不要用 `except Exception` 掩盖未知代码Bug，开发阶段的Traceback有重要价值。
12. system提示是行为软规则，工具Schema是接口说明，Python白名单才是真正权限边界。
13. 主入口保护使程序既能直接运行，也能被测试文件安全导入。
14. 本地确定性逻辑应尽量离线测试，避免无意义地调用收费API。
15. 逗号放在引号里面会成为字符串内容；相邻字符串自动拼接可能让漏逗号问题延迟到运行时暴露。
16. 工具错误发生在模型响应之后，可以回传Observation；模型API错误发生在响应之前，无法伪造工具结果。
17. `as error` 只是给异常对象起局部变量名，不是提前创建或主动监控一个错误。
18. 异常会沿未处理的函数调用链向外传播，直到遇到匹配的 `except`。
19. `raise ... from error` 在提供应用层说明的同时保留底层原因。
20. 自动重试会影响费用和重复执行风险，不能简单认为次数越多越可靠。

## 二十六、当前版本的限制与后续方向

当前Agent已能处理多轮工具决策和分层异常，但仍有以下限制：

- 每次程序运行只接受一个用户任务；
- 不同用户任务之间没有持续对话记忆；
- 工具、Schema、模型调用和界面仍集中在一个文件；
- `papers` 仍是内存数据，没有连接真实JSON文件；
- API失败只做友好提示，没有可配置重试、退避和日志；
- 没有记录每轮耗时、Token使用和工具调用审计；
- 尚未为 `run_agent()` 编写不依赖真实模型的自动化测试；
- 当前工具全是只读操作，尚未设计修改工具的确认与幂等性；
- 没有为不同错误定义自定义异常类型；
- 没有控制单次工具结果大小和完整messages长度。

这些将成为后续工程化、记忆管理、测试和安全设计的基础。

## 二十七、独立综合复习题

### 题目 1：有界旅行规划Agent

背景：旅行Agent拥有天气、火车票和酒店三个工具。一次任务可能需要连续多轮查询，也可能在第一轮直接回答常识问题。每次模型请求都产生费用。

任务：设计一个最多运行6轮的Agent循环，说明消息状态、停止条件和工具结果追加顺序。

验收标准：

- `messages` 在循环外初始化；
- 每轮只请求模型一次并保存完整assistant消息；
- 没有工具调用时返回普通答案；
- 一轮多个工具调用全部执行并分别回传；
- 每个结果使用对应的 `tool_call_id`；
- 下一轮能看到全部历史结果；
- 6轮仍未结束时主动停止；
- 能区分任务数、模型轮数和工具调用数。

### 题目 2：安全的工具结果信封

背景：库存Agent允许查询商品库存。模型可能传入非法JSON、列表而不是对象、空商品编号或未授权的删除工具。程序希望把可预期失败交给模型解释，同时保留真正代码Bug的Traceback。

任务：设计 `execute_tool_safely()` 和统一Observation格式。

验收标准：

- 成功使用 `success=True` 与 `result`；
- 失败使用 `success=False` 与 `error`；
- 捕获JSON解析异常；
- 验证解析结果最外层是字典；
- 验证商品编号和工具白名单；
- 具体异常位于宽泛异常之前；
- 不使用 `except Exception`；
- 无论成功失败都能序列化为 `role="tool"` 消息。

### 题目 3：可导入的命令行程序

背景：一个课程查询程序既需要通过终端运行，也需要让独立测试文件导入其中的搜索函数。当前只要导入模块就立刻出现 `input()`，导致测试卡住。

任务：重构程序入口并设计三个不联网的失败测试。

验收标准：

- 使用 `if __name__ == "__main__":`；
- 直接运行仍能询问用户；
- 被导入时不执行输入和网络请求；
- 测试文件能导入函数和模拟数据；
- 覆盖非法JSON、业务参数错误和未授权动作；
- 测试结果不出现意外Traceback；
- 能解释直接运行与导入时 `__name__` 的不同。

### 题目 4：分层处理模型API异常

背景：客服Agent使用第三方模型SDK。连接失败时没有HTTP状态码；认证、限流和服务器错误则会返回状态码。业务层不希望了解SDK的所有底层异常类型。

任务：设计 `call_model()` 和程序入口的异常转换流程。

验收标准：

- 区分连接异常与状态异常；
- 状态异常能够读取状态码；
- 底层异常转换为程序层 `RuntimeError`；
- 使用异常链保留原始原因；
- `run_agent()` 只负责循环，不重复API异常代码；
- 入口捕获运行错误并友好显示；
- 未知开发错误仍保留Traceback；
- 能说明为什么API失败不能伪装成 `role="tool"` 结果。

### 题目 5：定位一个没有语法错误的参数Bug

背景：开发者调用 `send_message(channel, content, metadata)` 时写成：

```python
send_message(
    "alerts,"
    "服务器异常",
    metadata
)
```

程序没有语法报错，却提示缺少一个位置参数。

任务：解释Python如何解析这段代码，修复问题，并设计一种能快速发现真实实参的调试方法。

验收标准：

- 指出逗号位于字符串内部；
- 说明相邻字符串字面量会自动拼接；
- 写出Python实际形成的第一个参数；
- 将参数分隔逗号移动到引号外；
- 能通过打印参数或最小函数复现实参个数；
- 说明为什么这是运行时错误而不是语法错误。

## 二十八、复习题参考思路

### 题目 1 参考思路

用 `for step in range(1, 7)` 限制轮数。每轮请求模型后立即追加完整assistant消息；无 `tool_calls` 时验证并返回 `content`。有调用时循环执行全部白名单工具，每个结果用自己的ID追加。只有进入下一轮时才再次请求模型，超限后抛出清楚的运行错误。

### 题目 2 参考思路

先对参数文本使用 `json.loads()`，再检查结果是字典，然后调用只允许已注册名称的分发器。分别捕获 `JSONDecodeError` 和业务 `ValueError`，返回统一结果信封。未知的 `KeyError`、`AttributeError` 等不统一吞掉，以便暴露代码缺陷。

### 题目 3 参考思路

把 `input()`、调用主函数和最终打印放进主入口保护。测试文件导入模块时只执行定义和安全初始化，不进入交互流程。直接调用安全工具执行函数，用构造的参数字符串覆盖三类错误，无需真实API。

### 题目 4 参考思路

在 `call_model()` 中捕获SDK连接异常和状态异常，转换为包含用户可理解信息的 `RuntimeError`，使用 `raise ... from error` 保留原因。`run_agent()` 调用它并让异常继续传播，命令行入口只捕获运行错误。连接失败发生在模型响应形成之前，因此没有真实assistant调用和工具ID可用于回传。

### 题目 5 参考思路

`"alerts,"` 与紧随其后的 `"服务器异常"` 都是字符串字面量，中间没有参数分隔逗号，所以Python将它们拼接为 `"alerts,服务器异常"`，再把 `metadata` 作为第二个参数。正确写成 `"alerts",`。可以用一个接收 `*args` 的临时函数打印参数数量和值，或者直接检查Traceback中的缺失位置参数。
