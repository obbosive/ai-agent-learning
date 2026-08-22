# Day 14 学习笔记：多轮对话记忆与安全历史裁剪

## 一、今日完成情况

Day 14 将 Day 13 的“单次用户任务Agent”升级成了可以持续对话的论文管理Agent。程序现在能在同一次运行中保留前面的用户问题、模型回答、工具调用和工具结果，从而理解“它是哪一年？”这类依赖历史上下文的追问。

今日主要文件：

```text
day14/
└── memory_agent.py    # 多轮对话、历史查看、重置、回滚、Token观察和安全裁剪
```

今天已经完成：

- 区分外层对话循环与内层Agent循环；
- 将 `messages` 从单轮函数内部移到整段对话生命周期；
- 将 `run_agent()` 改为 `run_agent_turn()`；
- 理解可变列表传入函数后的原地修改；
- 支持用户连续提出多个问题；
- 支持使用前文指代继续追问；
- 增加 `exit` 退出命令；
- 增加 `/history` 历史查看命令；
- 增加 `/reset` 对话重置命令；
- 理解本地命令为什么不能发给模型；
- 使用历史检查点回滚失败轮次；
- 使用 `response.usage` 观察输入和输出Token；
- 理解对话越长、每次重新发送的输入越多；
- 统一读取字典消息和SDK消息对象的角色；
- 实现只保留最近3个完整用户轮次的安全窗口；
- 保留system消息并避免切断Tool Calling消息配对；
- 通过真实对话验证旧轮次会被完整清理。

## 二、当前的“记忆”到底是什么

DeepSeek Chat Completions接口不会自动替我们的Python程序保存这段本地对话。模型能够理解前文，是因为程序每次请求都重新发送当前的：

```python
messages
```

例如第一次问题完成后：

```text
messages
├── system：Agent规则
├── user：搜索标题中带Agent的论文
├── assistant：申请search_papers
├── tool：搜索结果
└── assistant：找到Agent Survey
```

第二次用户追问：

```text
它是哪一年的？
```

Python把这条新消息追加到同一个列表，然后将完整列表再次发送。模型看到前面的搜索结果，才能判断“它”指的是《Agent Survey》。

因此现阶段的记忆本质是：

```text
Python进程内维护的消息历史
+
每次API请求重新发送这些历史
```

它不是模型服务器中的永久记忆，也不是数据库中的长期记忆。

## 三、外层对话循环与内层Agent循环

Day 14存在两个不同层级的循环。

### 外层对话循环

```python
while True:
    user_request = input(...)
```

职责：

- 连续接收用户问题；
- 识别 `exit`、`/history` 和 `/reset`；
- 为每个真实用户问题调用一次 `run_agent_turn()`；
- 在用户输入 `exit` 时结束程序。

### 内层Agent循环

```python
for step in range(1, max_steps + 1):
```

职责：

- 为当前一个用户问题请求模型；
- 执行零个、一个或多个工具；
- 回传Observation；
- 继续决策，直到获得最终回答；
- 达到最大步骤时停止。

关系：

```text
外层：整段用户会话
│
├── 用户问题1
│   └── 内层Agent第1、2……步
│
├── 用户问题2
│   └── 内层Agent第1、2……步
│
└── exit
```

每个新用户问题的Agent步骤都会从1重新计数，但 `messages` 会跨用户问题继续保留。

## 四、为什么Day 13每次都会失忆

Day 13在 `run_agent()` 内部创建：

```python
messages = [
    system消息,
    user消息
]
```

每次调用函数都会建立一份新列表。函数结束后，下一次问题不会继续使用上一份局部历史。

Day 14改为程序启动时创建一次：

```python
messages = create_messages()
```

然后每次调用：

```python
run_agent_turn(
    user_request,
    messages,
    papers
)
```

都传入同一份列表对象。

## 五、创建初始消息

```python
def create_messages():
    return [
        {
            "role": "system",
            "content": "……"
        }
    ]
```

函数说明：

- 输入：无；
- 动作：创建新的会话历史；
- 返回：只含system消息的新列表；
- 副作用：无；
- 使用场景：程序启动与 `/reset`。

system消息只在会话初始化时添加一次。不能在每个用户问题之前重复添加，否则历史里会出现多份相同规则，浪费Token并可能干扰上下文。

## 六、`run_agent_turn()` 的职责

```python
def run_agent_turn(
    user_request,
    messages,
    papers,
    max_steps=5
):
    messages.append({
        "role": "user",
        "content": user_request
    })

    # 当前用户问题的Agent循环
```

函数说明：

- 输入：当前用户问题、共享消息列表、论文数据和最大步骤数；
- 动作：追加用户消息并完成本轮Agent决策；
- 返回：当前用户轮次的最终自然语言答案；
- 副作用：原地向 `messages` 追加user、assistant和tool消息；
- 异常：API失败、异常响应或超过步骤时抛出 `RuntimeError`。

这里的“turn”表示一次用户提问从开始到最终回答的完整轮次，不等于内部的一次模型请求step。

## 七、可变列表为什么能保留函数内修改

列表是可变对象：

```python
def add_message(history):
    history.append("新消息")


messages = ["旧消息"]
add_message(messages)

print(messages)
```

结果：

```python
["旧消息", "新消息"]
```

调用函数时没有复制一份完全独立的列表；函数参数和外部变量都引用同一个列表对象。`.append()` 修改该对象，所以外部能看到新增内容。

如果函数内部写：

```python
messages = []
```

它只是让局部变量重新指向新列表，并不会自动清空外部原列表。这就是“原地修改对象”和“给变量重新赋值”的区别。

## 八、本地命令为什么不能发送给模型

当前支持：

```text
exit        结束程序
/history    查看消息结构
/reset      重置对话记忆
```

它们在调用 `run_agent_turn()` 前处理：

```python
if user_request.lower() == "/history":
    show_history(messages)
    continue

if user_request.lower() == "/reset":
    messages = create_messages()
    print("对话记忆已清空")
    continue
```

`continue` 立即进入外层循环下一次输入，所以本地命令：

- 不会追加到 `messages`；
- 不会发送给DeepSeek；
- 不会触发工具；
- 不会消耗模型Token。

它们是Python界面层命令，而不是自然语言Agent任务。

## 九、`exit` 与空输入

```python
if user_request.lower() == "exit":
    print("对话结束")
    break
```

`break` 结束外层 `while` 循环，程序退出。

空输入：

```python
if not user_request:
    print("需求不能为空")
    continue
```

不会发送给模型，避免产生没有业务意义的API请求。

## 十、混合消息类型

当前 `messages` 中不是所有元素都属于同一种Python类型。

我们手动创建的消息通常是字典：

```python
{
    "role": "user",
    "content": "……"
}
```

模型返回的assistant消息是SDK对象：

```python
ChatCompletionMessage(...)
```

所以角色访问方式不同：

```python
message.get("role")   # 字典
message.role          # SDK对象
```

## 十一、统一读取消息角色

```python
def get_message_role(message):
    if isinstance(message, dict):
        return message.get("role", "unknown")

    return message.role
```

函数说明：

- 输入：字典消息或SDK消息对象；
- 动作：根据类型读取角色；
- 返回：消息角色字符串；
- 副作用：无。

`"unknown"` 不是DeepSeek规定的新角色，而是我们为缺少 `role` 字段时提供的本地备用字符串。

```python
message.get("role", "unknown")
```

表示：

- 字典存在 `role` 时返回真实值；
- 不存在时返回字符串 `"unknown"`；
- 不会把 `unknown` 写入原字典。

正常协议角色仍然是：

```text
system
user
assistant
tool
```

## 十二、查看历史结构

```python
def show_history(messages):
    print(f"当前共有{len(messages)}条消息：")

    for index, message in enumerate(messages):
        role = get_message_role(message)
        print(f"{index}：{role}")
```

`enumerate(messages)` 同时产生：

- `index`：消息索引；
- `message`：对应消息对象。

只打印角色而不打印完整content，可以更清楚地观察协议顺序，也避免工具结果和长文本让终端过于混乱。

## 十三、为什么三轮用户对话可能有十一条消息

“保留3个用户轮次”不等于“列表里只有3条消息”。

普通直接回答一轮通常有：

```text
user
assistant
```

一次工具调用轮次可能有：

```text
user
assistant(tool_calls)
tool
assistant(final)
```

一次调用两个工具可能有：

```text
user
assistant(tool_calls)
tool
tool
assistant(final)
```

因此截图中：

```text
1条system
+ 3条user
+ 多条assistant和tool
= 11条完整消息
```

属于正常结果。窗口限制的是用户轮次，不是原始消息条数。

## 十四、失败轮次为什么会污染历史

`run_agent_turn()` 一开始就追加：

```python
messages.append({
    "role": "user",
    "content": user_request
})
```

之后还可能追加assistant工具申请和部分tool结果。如果本轮中途发生API错误，而这些半成品继续保留，下一轮模型可能看到：

- 没有回答的用户消息；
- 缺少工具结果的assistant工具申请；
- 不完整的Agent轨迹。

所以每个用户轮次需要一个类似事务的边界：

```text
开始 → 记录检查点
成功 → 提交并保留新增历史
失败 → 回滚本轮新增历史
```

## 十五、历史检查点与回滚

本轮开始前：

```python
history_checkpoint = len(messages)
```

发生 `RuntimeError`：

```python
except RuntimeError as error:
    del messages[history_checkpoint:]
    print(f"Agent运行失败：{error}")
```

如果检查点是6：

```python
del messages[6:]
```

表示删除索引6到末尾的所有本轮新增内容，保留之前索引0到5的完整历史。

今天曾写成：

```python
del messages[history_checkpoint]
```

它只删除检查点位置的一个元素，可能删掉本轮user，却留下assistant或tool半成品。冒号决定了是“一个元素”还是“从这里到末尾的一段切片”。

## 十六、工具失败与轮次回滚的区别

工具参数错误经过：

```python
execute_tool_safely()
```

返回：

```python
{
    "success": False,
    "error": "……"
}
```

它仍是一条正常Observation，Agent可以进入下一步修正或解释，所以不回滚。

以下情况会抛出 `RuntimeError` 并回滚：

- API连接失败；
- API返回错误状态；
- 模型既没有答案也没有工具调用；
- 当前用户问题超过最大Agent步骤。

区别：

```text
工具可预期失败 → Agent仍在正常运行
Agent流程中断     → 本轮历史不可提交
```

## 十七、`/reset` 与回滚为什么写法不同

回滚：

```python
del messages[history_checkpoint:]
```

目的是保留同一列表中之前成功的历史，只删除本轮新增部分。

重置：

```python
messages = create_messages()
```

目的是彻底放弃旧会话，改用一份只含system的新列表。此时没有正在运行的 `run_agent_turn()` 需要继续引用旧列表，所以重新赋值符合目标。

## 十八、Token为什么随历史增长

每次：

```python
call_model(messages)
```

都会发送当前完整历史和工具Schema。第二次用户问题不是只发送第二句话，而是发送：

```text
system
第1轮user
第1轮assistant工具申请
第1轮tool结果
第1轮最终回答
第2轮user
```

因此历史越长，输入Token通常越多。

观察代码：

```python
usage = response.usage

if usage:
    print(f"输入：{usage.prompt_tokens}")
    print(f"输出：{usage.completion_tokens}")
    print(f"总计：{usage.total_tokens}")
```

这里显示的是一次模型请求的Token，不是整段程序累计值。一个用户问题如果经过两个Agent步骤，会打印两组usage。

## 十九、为什么不能使用 `messages[-10:]`

简单截取最后10条：

```python
messages = messages[-10:]
```

可能造成：

1. system消息被删除；
2. 从一个工具调用轮次中间切开；
3. 保留tool结果却删除对应assistant调用；
4. 保留assistant的 `tool_calls` 却删除对应tool结果；
5. 后续API拒绝不符合协议的消息顺序。

Tool Calling消息属于有关系的结构，不能把每条消息当成相互独立文本。

## 二十、安全裁剪的基本策略

当前策略：

```text
保留system
+
保留最近3个完整user轮次及其全部后续消息
```

每个新用户轮次从 `role="user"` 开始，下一条user出现之前的assistant和tool都属于当前轮次。因此user索引可以作为安全边界。

## 二十一、安全裁剪函数

```python
def trim_history(messages, max_user_turns=3):
    if max_user_turns < 1:
        raise ValueError("至少需要保留一个用户轮次")

    user_indexes = []

    for index, message in enumerate(messages):
        if get_message_role(message) == "user":
            user_indexes.append(index)

    if len(user_indexes) <= max_user_turns:
        return 0

    first_kept_index = user_indexes[-max_user_turns]
    removed_count = first_kept_index - 1

    del messages[1:first_kept_index]

    return removed_count
```

函数说明：

- 输入：完整消息列表和最多保留的用户轮数；
- 动作：保留system和最近若干完整用户轮次；
- 返回：被删除的消息数量；
- 副作用：原地修改消息列表；
- 异常：保留轮数小于1时抛出 `ValueError`。

## 二十二、`user_indexes` 存的是什么

假设历史角色为：

```text
0 system
1 user
2 assistant
3 tool
4 assistant
5 user
6 assistant
7 user
8 assistant
9 tool
10 assistant
```

遍历后：

```python
user_indexes = [1, 5, 7]
```

列表里存的是每条user消息在完整 `messages` 中的索引，不是用户问题内容。

判断是否需要裁剪必须比较数量：

```python
if len(user_indexes) <= max_user_turns:
```

今天曾写成：

```python
if user_indexes <= max_user_turns:
```

这是列表和整数比较，会产生 `TypeError`。我们需要的是列表长度，而不是拿列表本身和数字比较。

## 二十三、负数索引如何找到最早保留轮次

假设：

```python
user_indexes = [1, 5, 7, 11]
max_user_turns = 3
```

```python
user_indexes[-3]
```

从倒数第3个元素取值，结果是：

```python
5
```

所以：

```python
first_kept_index = 5
```

表示从索引5的第二个用户轮次开始保留，索引1开始的第一个旧轮次应被删除。

## 二十四、为什么删除 `messages[1:first_kept_index]`

```python
del messages[1:first_kept_index]
```

- 起点是1：保留索引0的system消息；
- 终点不包含 `first_kept_index`：保留最早需要留下的user消息；
- 中间内容属于更早的完整用户轮次，整体删除。

如果：

```python
first_kept_index = 5
```

实际删除索引：

```text
1、2、3、4
```

删除数量：

```python
removed_count = first_kept_index - 1
```

即：

```python
5 - 1 == 4
```

## 二十五、为什么只在成功轮次后裁剪

主入口成功路径：

```python
final_answer = run_agent_turn(...)

removed_count = trim_history(
    messages,
    max_user_turns=3
)
```

只有 `run_agent_turn()` 正常返回，才说明当前user、assistant、tool和最终答案已经形成完整轮次。此时从旧user边界裁剪安全。

如果在工具调用执行到一半时裁剪，可能误删当前请求仍需参考的内容或破坏协议配对。

## 二十六、截图结果如何解释

截图显示：

```text
已清理2条旧信息
当前共11条信息
其中有3条user
```

这说明：

- 最旧轮次是普通一问一答，所以删除2条消息；
- system仍保留；
- 最近3个用户轮次仍保留；
- 某些轮次调用工具，因此包含更多assistant和tool消息；
- 算法限制用户轮次，而不是强行限制总消息数。

## 二十七、当前安全窗口的局限

当前算法比按消息条数截断安全，但并不完美。

### 1. 按轮数不等于按Token

三个很长的用户轮次可能比三十个简短问答消耗更多Token。生产系统更适合按Token预算决定是否压缩。

### 2. 可能丢失指代来源

如果最早保留的轮次是：

```text
它是哪一年？
```

而“它”对应的实体只出现在被删除的更早轮次中，模型会失去指代来源。协议结构仍完整，但语义上下文可能不完整。

### 3. 当前记忆只在内存中

关闭Python程序后，`messages` 消失。它不是跨进程、跨设备或跨日期的长期记忆。

### 4. 没有摘要

更成熟的方案会在删除旧历史前生成摘要，把关键实体、用户偏好和未完成任务压缩成更短内容。

### 5. 没有外部长期记忆

论文数据、长期用户偏好和历史事实更适合保存到JSON、数据库或向量数据库，需要时再检索，而不是无限堆积在聊天上下文中。

## 二十八、短期记忆、长期记忆与业务数据

三者应区分：

```text
短期对话记忆
→ 当前messages，用于理解最近对话和指代

长期记忆
→ 文件或数据库中的用户偏好、任务摘要和历史记录

业务数据
→ papers等真实论文数据，应通过工具读取和修改
```

不能把模型上下文当成可靠数据库。上下文被裁剪后会消失，模型也可能误解或总结错误；真实业务状态必须保存在受控数据源中。

## 二十九、个人复盘与注意事项

1. 模型能理解前文，是因为Python重新发送messages，不是API自动永久记住。
2. 外层 `while` 管理用户对话，内层 `for` 管理当前问题的Agent步骤，两个循环职责不同。
3. system消息只在会话开始时创建一次，不应每个用户问题重复加入。
4. `run_agent_turn()` 通过 `.append()` 原地修改共享列表，所以历史能跨函数调用保留。
5. 给局部变量重新赋新列表与原地修改旧列表是两件不同的事。
6. `exit`、`/history`、`/reset` 是本地命令，应在调用模型前拦截。
7. 本地命令不进入messages、不调用API，也不产生Token费用。
8. `unknown` 只是 `.get()` 的默认显示字符串，不是协议角色。
9. messages中同时存在字典和SDK对象，不能假设全部支持同一种访问语法。
10. 一次用户轮次可能包含多条assistant和tool消息，所以3轮不等于3条消息。
11. 本轮开始前用 `len(messages)` 记录检查点，运行中断后删除检查点到末尾。
12. `del messages[index]` 只删一个元素，`del messages[index:]` 才删到末尾。
13. 工具返回 `success=False` 是Observation，不等于整个Agent轮次中断。
14. 每次模型请求都会重新发送当前历史，输入Token通常随对话增长。
15. usage显示的是单次模型请求，不是整段会话自动累计值。
16. 不应按固定消息条数从任意位置截断Tool Calling历史。
17. 安全裁剪必须保留system，并从完整user轮次边界开始。
18. `user_indexes` 是列表，比较轮次数量时必须使用 `len(user_indexes)`。
19. 负数索引 `[-3]` 表示倒数第3个元素，可用于找到最近3轮中最早的一轮。
20. 裁剪只应在当前轮次成功结束后执行，失败时先回滚。
21. 结构完整不代表语义完整；删除前文可能让“它”等指代失去来源。
22. 当前messages属于会话短期记忆，退出程序后不会保留。

## 三十、当前版本的限制与后续方向

当前多轮Agent已经具备短期记忆管理，但仍有这些限制：

- 退出程序后历史丢失；
- 只按用户轮数裁剪，不按实际Token预算；
- 删除旧历史前没有生成摘要；
- 没有把关键实体和用户偏好保存为长期记忆；
- 没有区分不同用户或会话ID；
- 没有将消息历史保存到文件或数据库；
- 没有为裁剪和回滚函数编写完整自动化测试；
- 所有功能仍集中在一个Python文件；
- 对话历史中保存完整工具结果，真实项目可能过长；
- 没有统计整段会话累计Token与费用。

这些会连接到后续的模块化、持久化、摘要、RAG和数据库学习。

## 三十一、独立综合复习题

### 题目 1：多轮客服Agent

背景：订单客服Agent需要连续处理“查询订单A1024”“它什么时候到？”“换成订单B2048看看”等追问。订单数据必须通过工具获取，用户输入 `exit` 时结束。

任务：设计外层对话循环和内层Agent循环，并说明messages的生命周期。

验收标准：

- system消息只初始化一次；
- 外层循环连续接收用户问题；
- 内层循环允许当前问题调用多个工具步骤；
- 每次新问题追加到同一messages；
- 后续追问能看到之前的订单工具结果；
- `exit` 不发送给模型；
- 每个用户问题拥有独立的最大Agent步骤限制；
- 能解释为什么关闭程序后当前记忆会消失。

### 题目 2：失败轮次的状态回滚

背景：旅行Agent已成功完成两轮对话。第三轮追加了user消息、assistant工具申请和一个tool结果后，模型API连接失败。程序仍要继续接受第四轮问题，但不能保留第三轮半成品。

任务：使用列表检查点设计本轮事务式回滚。

验收标准：

- 调用本轮Agent前记录 `len(messages)`；
- 成功时保留本轮所有新增消息；
- `RuntimeError` 时删除检查点到末尾的切片；
- 不只删除单个user消息；
- 保留之前两轮完整历史；
- 工具返回结构化失败时不立即回滚；
- 能说明为什么半个Tool Calling轮次可能导致后续协议错误。

### 题目 3：本地会话控制命令

背景：学习助手需要支持 `/history`、`/reset` 和 `exit`。历史中同时包含字典消息和SDK对象，查看历史时只显示索引和角色。

任务：实现角色读取、历史显示和命令分发。

验收标准：

- 字典角色使用 `.get()`；
- SDK对象角色使用点号属性；
- 缺失角色时显示本地默认值；
- `/history` 不修改历史；
- `/reset` 生成只含system的新历史；
- `exit` 结束外层循环；
- 三个命令都不调用模型、不消耗Token；
- 能解释默认字符串为什么不是协议中的新角色。

### 题目 4：安全的工具消息窗口

背景：天气Agent的每个用户轮次可能直接回答，也可能产生 `user → assistant(tool_calls) → tool → assistant`。程序希望最多保留最近4个用户轮次，但必须始终保留system。

任务：根据user消息索引实现安全裁剪函数。

验收标准：

- 验证保留轮数至少为1；
- 正确识别字典和SDK消息角色；
- 收集所有user在完整历史中的索引；
- 用户轮次不超过4时不修改历史；
- 使用负数索引找到最早保留轮次；
- 删除从索引1到该user之前的完整旧历史；
- system和最近4轮全部保留；
- 返回实际删除消息数量；
- 不从assistant与tool配对中间截断。

### 题目 5：记忆成本与方案选择

背景：论文Agent已经支持多轮对话，但有的用户每轮只输入几个字，有的用户会粘贴数千字论文摘要。产品希望控制费用，同时尽量保留重要上下文。

任务：比较固定消息数、固定用户轮数、Token预算、历史摘要和外部长期记忆五种策略，并给出组合方案。

验收标准：

- 说明每次请求为什么会重复计算历史输入Token；
- 指出固定消息数可能破坏工具消息配对；
- 指出固定轮数不能准确代表Token数量；
- 说明摘要可以压缩但可能损失或扭曲细节；
- 区分短期对话上下文与真实业务数据；
- 长期事实保存到文件或数据库，而不是只依赖messages；
- 提出至少一种“完整轮次边界+Token预算+摘要”的组合方案。

## 三十二、复习题参考思路

### 题目 1 参考思路

程序启动时创建包含system的messages。外层 `while` 读取每次用户输入，拦截本地退出命令，再把同一列表交给 `run_agent_turn()`。内层按最大步骤请求模型、执行工具并追加Observation，直到返回最终答案。因为历史只存在当前Python进程内，退出后变量消失。

### 题目 2 参考思路

每轮调用前记录 `checkpoint = len(messages)`。如果本轮正常返回，不做回滚；如果出现可继续运行的 `RuntimeError`，执行 `del messages[checkpoint:]`。工具业务失败已经变成普通tool Observation，应让Agent继续处理，不能和整个运行中断混为一谈。

### 题目 3 参考思路

编写 `get_message_role()`，字典用 `.get("role", "unknown")`，SDK对象用 `.role`。`show_history()` 使用 `enumerate()` 显示索引与角色。本地命令在追加user和调用模型前处理，并用 `continue` 返回下一次输入；重置重新调用初始消息函数。

### 题目 4 参考思路

遍历历史收集user索引。若数量不超过4，返回0；否则取 `user_indexes[-4]` 作为最早保留位置，计算删除数量，并执行 `del messages[1:first_kept_index]`。从user边界裁剪可完整删除旧轮次，索引0的system始终保留。

### 题目 5 参考思路

先按完整user轮次组织消息，避免破坏协议；请求前估算Token，当超出预算时删除最旧完整轮次。对仍有长期价值的旧内容生成摘要并保留关键实体，但真实论文、订单等业务状态应存入可靠数据源，通过工具重新读取。摘要和外部记忆都需要验证，不能把模型概括当作绝对真实记录。
