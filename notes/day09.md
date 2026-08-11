# Day 9 学习笔记：HTTP、API、JSON 与认证请求

## 一、今日完成情况

Day 9 第一次让 Python 程序通过网络与外部服务通信。学习对象是 GitHub REST API，最终完成了三个小程序：

```text
day09/
├── first_api_request.py  # 查询自己的GitHub仓库，处理状态码、异常和认证
├── token_check.py        # 安全验证.env中的Token能否被读取
└── params_demo.py        # 使用查询参数搜索GitHub仓库并解析嵌套JSON
```

今天已经完成：

- 理解客户端、服务器和 API 的关系；
- 使用 `requests.get()` 发送 HTTP GET 请求；
- 认识 `Response` 对象、状态码、响应头和响应体；
- 将网络返回的 JSON 转换成 Python 字典和列表；
- 区分连接失败与服务器返回 `403`、`404`；
- 使用 `raise_for_status()` 将错误 HTTP 状态转换成 Python 异常；
- 理解 `try` 和 `except` 在一次异常流程中可以先后执行；
- 创建最低权限的 GitHub Fine-grained Token；
- 使用 `.env` 和 `python-dotenv` 在代码外保存秘密；
- 使用 `Authorization` 请求头完成认证，API 限额从匿名的 60 提升至 5000；
- 使用 `params` 传递搜索条件并观察 URL 编码；
- 解析 GitHub 搜索接口返回的嵌套 JSON；
- 根据关键词、语言、Star 数和返回数量搜索真实开源仓库。

## 二、客户端、服务器与 API

当前程序中各角色是：

```text
Python程序                GitHub
客户端                    服务器
   │                         │
   ├── 发送HTTP请求 ────────> │
   │                         │ 处理请求
   │ <────── 返回HTTP响应 ───┤
   │
解析JSON并使用数据
```

API 是服务器专门提供给程序使用的接口。普通网页通常返回 HTML，交给浏览器渲染；REST API 通常返回 JSON，交给程序处理。

例如：

```text
https://api.github.com/repos/obbosive/ai-agent-learning
```

不是普通仓库网页，而是查询仓库信息的 API 地址。

## 三、URL 与 GET 请求

URL 可以拆成：

```text
https://api.github.com/repos/obbosive/ai-agent-learning
└─协议─┘ └──服务器地址──┘ └────────资源路径─────────┘
```

- `https`：通信协议；
- `api.github.com`：服务器主机名；
- `/repos/obbosive/ai-agent-learning`：要访问的资源路径。

发送请求：

```python
response = requests.get(url, timeout=10)
```

- `requests`：第三方 HTTP 客户端库；
- `get()`：发送 GET 请求；
- `url`：请求目标；
- `timeout=10`：避免网络异常时无限等待；
- 返回值 `response`：服务器响应对象，不是字典。

GET 的主要语义是获取资源，通常不应该修改服务器数据。查询不存在的仓库也是安全的 GET 操作，不会创建或删除任何内容。

## 四、HTTP 请求与响应的结构

一次认证搜索请求大致可以表示为：

```http
GET /search/repositories?q=rag&per_page=3 HTTP/1.1
Host: api.github.com
Accept: application/vnd.github+json
User-Agent: ai-agent-learning
Authorization: Bearer <Token>
```

请求包含：

- 方法：`GET`；
- 路径和查询参数；
- 请求头；
- 某些请求还可能包含请求体。

响应包含：

- 状态码；
- 响应头；
- 响应体。

在 `requests` 中：

```python
response.status_code       # 状态码
response.headers           # GitHub返回的响应头
response.text              # 原始文本响应体
response.json()            # 将JSON响应体转换成Python对象
response.request.headers   # 本程序发出去的请求头
response.url               # 最终实际请求URL
```

必须区分：

```text
response.request.headers  程序发给服务器的请求头
response.headers          服务器返回给程序的响应头
```

## 五、状态码及其数据类型

常见状态码：

| 状态码 | 含义 |
|---|---|
| `200` | 请求成功 |
| `401` | 身份认证失败 |
| `403` | 没有权限、受到限制或额度耗尽 |
| `404` | 资源不存在 |
| `500` | 服务器内部错误 |

`response.status_code` 是整数，不是字符串：

```python
response.status_code == 200    # 正确
response.status_code == "200"  # False
```

当天第一次程序只打印状态码、不进入成功分支，原因就是把整数 `200` 与字符串 `'200'` 比较。

这类问题不应简单归因于粗心，而应主动检查数据类型：

```python
print(type(response.status_code))
```

## 六、JSON 与 Python 对象

JSON 是跨语言的数据交换格式。服务器通过网络发送的是 JSON 文本，`response.json()` 将其解析成 Python 对象：

```text
JSON对象 {}   → Python字典 dict
JSON数组 []   → Python列表 list
JSON字符串    → Python字符串 str
JSON数字      → Python整数或浮点数
JSON布尔值    → Python True / False
JSON null     → Python None
```

查询单个仓库时，最外层是仓库对象，因此：

```python
data = response.json()
print(data["full_name"])
print(data["default_branch"])
print(data["language"])
print(data["stargazers_count"])
```

搜索仓库时，返回结构大致是：

```python
{
    "total_count": 1000,
    "incomplete_results": False,
    "items": [
        {"full_name": "仓库A", "language": "Python"},
        {"full_name": "仓库B", "language": "Python"},
        {"full_name": "仓库C", "language": "Python"}
    ]
}
```

解析层级：

```python
data = response.json()          # 最外层字典
repositories = data["items"]   # 字典中的列表

for repository in repositories:
    print(repository["full_name"])
```

命名时使用单复数可以帮助表达结构：

- `repositories`：仓库列表；
- `repository`：当前循环中的一个仓库字典。

## 七、连接失败与错误响应不是一回事

今天分别实验了本机不存在的端口和 GitHub 不存在的仓库。

### 情况一：没有获得响应

访问：

```text
http://127.0.0.1:1
```

本机 1 号端口没有服务器，因此连接阶段失败：

```text
requests.get()
→ ConnectionError
→ 没有创建response
→ 根本不存在可读取的HTTP状态码
```

处理方式：

```python
try:
    response = requests.get(url, timeout=10)
except requests.exceptions.RequestException as error:
    print(f"网络请求没有完成：{error}")
    return
```

`return` 很关键，因为请求失败后没有可用的 `response`，函数必须停止，不能继续访问 `response.status_code`。

### 情况二：获得了错误响应

查询不存在的 GitHub 仓库时：

```text
requests.get()
→ 成功获得Response
→ response.status_code == 404
```

这里网络通信已经完成，只是服务器明确表示资源不存在。

## 八、`raise_for_status()` 与异常转换

`requests.get()` 默认不会因为 `404` 或 `500` 自动抛出异常，因为这些仍是合法 HTTP 响应，程序可能希望自己检查响应内容。

主动调用：

```python
response.raise_for_status()
```

会产生以下行为：

```text
2xx → 正常通过
4xx → 抛出HTTPError
5xx → 抛出HTTPError
```

实验中先把它放在 `try` 外，观察到了未处理异常和完整 Traceback；随后放入 `try`：

```python
try:
    response.raise_for_status()
except requests.exceptions.HTTPError as error:
    print(f"捕获到HTTP异常：{error}")
```

异常被匹配的 `except` 捕获后，不会继续向外传播，因此程序不再显示未处理的 Traceback。

### `try` 和 `except` 不是简单二选一

正确流程是：

```text
先执行try
→ 没有异常：try全部执行完，except不执行
→ 中途有匹配异常：try剩余代码跳过，执行except
```

例如：

```python
try:
    print("A")
    number = 1 / 0
    print("B")
except ZeroDivisionError:
    print("C")

print("D")
```

输出：

```text
A
C
D
```

因此，一次异常流程中，`try` 前半部分和 `except` 可以先后执行；只是在异常点之后的 `try` 代码不再执行。

### 异常层级

`requests` 常见异常大致是：

```text
RequestException
├── ConnectionError
├── Timeout
└── HTTPError
```

`RequestException` 是共同父类，适合统一兜底；具体异常类适合给出更精确的提示。

## 九、请求头 Headers

Python 使用字典表示要发送的请求头：

```python
headers = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "ai-agent-learning"
}
```

`requests` 将字典转换成真正的 HTTP 请求头：

```text
Python字典
→ requests准备请求
→ Accept: application/vnd.github+json
→ User-Agent: ai-agent-learning
```

- `Accept`：希望服务器返回什么数据格式；
- `User-Agent`：说明请求来自什么程序；
- 二者都不能证明用户身份。

函数调用：

```python
response = requests.get(url, headers=headers, timeout=10)
```

如果把变量改名为 `my_headers`，应写：

```python
requests.get(url, headers=my_headers, timeout=10)
```

左边的 `headers` 是函数规定的参数名，右边是程序自己的变量。

## 十、GitHub Token 与安全认证

### Token 的作用

匿名 GitHub API 请求按公网 IP 计算额度。当天使用共享 VPN 出口时，遇到：

```text
API rate limit exceeded
limit = 60
remaining = 0
```

创建 Fine-grained Personal Access Token 后，请求可被识别为账号的认证请求。当前只读取公开仓库元数据，没有添加写入权限。

Token 通过请求头发送：

```http
Authorization: Bearer <Token>
```

对应 Python：

```python
headers = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "ai-agent-learning",
    "Authorization": f"Bearer {token}"
}
```

认证成功的证据是 GitHub 返回：

```text
X-RateLimit-Limit: 5000
```

Token 被称为 Bearer Token，意味着持有者可能使用它所拥有的权限。因此必须像密码一样保护。

### `.env` 与 `.env.example`

真实秘密保存在项目根目录的 `.env`：

```text
GITHUB_TOKEN=真实Token
```

`.gitignore` 必须包含：

```gitignore
.env
```

可提交的 `.env.example` 只记录变量名称和填写示例，不能包含真实值：

```text
GITHUB_TOKEN=在这里填写自己的GitHubToken
```

职责区别：

```text
.env          真实秘密，本地使用，不提交
.env.example  配置模板，可以提交，不含秘密
```

### `load_dotenv()` 与 `os.getenv()`

Python 默认不会自动读取 `.env`。安装 `python-dotenv` 后：

```python
import os

from dotenv import load_dotenv


load_dotenv()
token = os.getenv("GITHUB_TOKEN")
```

数据流：

```text
.env文件
→ load_dotenv()加载到当前Python进程的环境变量
→ os.getenv("GITHUB_TOKEN")按名称取值
→ token变量保存真实字符串
```

`load_dotenv()` 的主要用途是执行加载动作。它的返回值是是否加载到配置的布尔结果，不是 Token。不能写成：

```python
GITHUB_TOKEN = load_dotenv()  # 得到的不是Token
```

这种误写的根本原因是第一次接触新函数时没有先明确输入、动作和返回值。以后学习陌生函数，应先回答：

1. 它接收什么参数？
2. 它执行什么动作或副作用？
3. 它返回什么？
4. 它可能抛出什么异常？

安全检查可以使用：

```python
print(bool(token))
```

这只说明是否读取到非空字符串，不会展示真实 Token，也不能证明 Token 必然有效。是否有效需要通过认证请求验证。

绝对不要执行：

```python
print(token)
print(headers)
print(response.request.headers)
```

后两项可能连同 `Authorization` 一起泄露。

## 十一、查询参数 `params`

搜索接口的基础地址是：

```text
https://api.github.com/search/repositories
```

查询条件用字典表示：

```python
params = {
    "q": "ai agent language:python",
    "sort": "stars",
    "order": "desc",
    "per_page": 3
}
```

调用：

```python
response = requests.get(url, params=params, timeout=10)
```

`requests` 自动编码成：

```text
?q=ai+agent+language%3Apython&sort=stars&order=desc&per_page=3
```

符号含义：

- `?`：查询字符串开始；
- `=`：参数名与值之间的分隔；
- `&`：多个参数之间的分隔；
- `+`：编码后的空格；
- `%3A`：编码后的冒号 `:`。

参数解释：

- `q`：搜索表达式；
- `language:python`：GitHub 搜索语法中的语言限制；
- `sort=stars`：按照 Star 数排序；
- `order=desc`：降序；
- `per_page=3`：本页返回三条结果。

必须准确区分：

| Python参数 | 最终位置 | 例子 |
|---|---|---|
| `params` | URL的查询字符串 | `?q=rag&per_page=3` |
| `headers` | HTTP请求头 | `Authorization: Bearer ...` |

记忆方式：

```text
params：这次具体查询什么
headers：请求格式、程序身份和认证信息
```

## 十二、交互式仓库搜索

将固定关键词改成用户输入：

```python
keyword = input("请输入仓库搜索关键词：").strip()

params = {
    "q": f"{keyword} language:python",
    "sort": "stars",
    "order": "desc",
    "per_page": 3
}
```

输入 `rag` 后：

```text
用户输入rag
→ f-string生成rag language:python
→ params字典
→ requests编码查询字符串
→ GitHub筛选Python仓库并按Star降序
→ 返回三条JSON数据
→ Python解析并循环输出
```

这已经具备一个基础 API 客户端的完整数据流。

## 十三、个人复盘与注意事项

1. 学习新库时，不能只照着函数名猜用途。`load_dotenv()` 的误用说明，必须先学习函数的输入、动作、返回值和异常，再要求独立编写。
2. “列出需要调用哪些函数”不等于真正教学。以后遇到完全陌生的 API，应先使用最小实验观察行为，再逐步组合进项目。
3. `response.status_code` 是整数。看到值相同但条件不成立时，应检查类型，而不是重复修改外观相似的代码。
4. 连接失败时没有 `response`，自然也没有状态码；`404` 则表示已经收到了带错误状态的响应。这是网络异常与 HTTP 业务错误的核心区别。
5. `try` 总是先执行；发生匹配异常后，才由 `except` 接管。它不像 `if/else` 那样一开始就简单二选一。
6. `params` 和 `headers` 曾经发生混淆。看到实际 `response.url` 是最直接的证据：`params` 被编码到 URL，Token 则位于 `Authorization` 请求头。
7. 第三方库、Token、网络代理和 API 服务都是项目的外部依赖。程序不能假设它们永远存在，必须验证并处理失败。
8. `.env` 被忽略不代表 Token 可以随便展示。终端、截图、日志和报错信息同样可能泄密。
9. 使用 AI 辅助时，陌生代码不能仅复制运行。应要求解释每个新函数的数据流，并用类型、状态码和最小实验验证理解。

## 十四、独立综合复习题

### 题目 1：图书搜索 API 客户端

背景：某图书 API 规定搜索地址为：

```text
https://example.com/api/books
```

支持参数：`q` 表示关键词，`language` 表示语言，`limit` 表示返回数量。成功响应最外层是字典，其中 `items` 是图书列表，每本书包含 `title`、`author` 和 `year`。

任务：编写 `search_books(keyword)`，搜索中文图书并返回前五条，输出最终 URL、状态码以及每本书的信息。

验收标准：

- 使用 `params` 字典，不手工拼接 `?` 和 `&`；
- 请求设置合理的超时；
- 只有成功响应才解析 JSON；
- 正确识别最外层字典和 `items` 列表；
- 空关键词不会发送请求；
- 能解释关键词中的空格为什么会被 URL 编码。

### 题目 2：区分三种失败

背景：订单查询程序可能遇到三种情况：无法连接服务器、服务器返回 `404`、服务器返回 `200`。

任务：设计请求与异常处理流程，并说明每种情况下 `response` 是否存在、能否读取状态码、程序应该向用户显示什么。

验收标准：

- 连接失败时不会继续访问不存在的 `response`；
- `404` 被识别为已收到的错误响应；
- 使用 `raise_for_status()` 时能捕获对应 `HTTPError`；
- 成功时正常解析数据；
- 能解释 `try` 中异常点之后的代码为什么不会执行。

### 题目 3：安全调用需要 API Key 的服务

背景：天气 API 需要通过请求头 `Authorization: Bearer <API_KEY>` 认证。项目将上传到公开 Git 仓库。

任务：设计本地秘密文件、配置模板、忽略规则和 Python 读取代码，随后构造认证请求头。不得在任何输出中展示真实 Key。

验收标准：

- 真实 `.env` 被 Git 忽略；
- `.env.example` 只包含变量名称和占位说明；
- 使用 `load_dotenv()` 加载，使用 `os.getenv()`取值；
- 缺少 Key 时停止请求并提示；
- Key 位于请求头而不是 URL；
- 能说明 `bool(key)` 能验证什么、不能验证什么。

### 题目 4：分析一条完整 HTTP 交互

背景：某程序最终发送：

```http
GET /api/articles?q=agent&limit=2 HTTP/1.1
Accept: application/json
Authorization: Bearer <Token>
```

服务器返回状态码 `200`、响应头 `Content-Type: application/json`，响应体为包含 `items` 列表的 JSON。

任务：把这次交互分别映射到 `requests.get()` 的 `url`、`params`、`headers`、`response.status_code`、`response.headers` 和 `response.json()`。

验收标准：

- `q` 和 `limit` 被归入 `params`；
- `Accept` 和 `Authorization` 被归入 `headers`；
- 能区分 `response.request.headers` 与 `response.headers`；
- 能说明 Token 为什么不应该出现在 URL；
- 能从解析后的 `items` 列表中遍历两篇文章。

### 题目 5：诊断一个看似成功的程序

背景：程序执行后没有 Traceback，但也没有输出结果：

```python
response = requests.get(url, timeout=10)

if response.status_code == "200":
    data = response.json()
    print(data["name"])
```

任务：定位问题，解释为什么程序安静结束，并提出兼顾状态码、数据类型和失败提示的修改方案。

验收标准：

- 指出字符串 `"200"` 与整数状态码的区别；
- 能说明条件为假且没有 `else` 时为何无输出；
- 修改后成功分支能够执行；
- 非成功状态有明确提示；
- 不把该问题笼统归因于“粗心”。

## 十五、复习题参考思路

### 题目 1 参考思路

先清理并验证关键词，再创建 `params = {"q": keyword, "language": "zh", "limit": 5}`，交给 `requests.get()`。成功后调用 `response.json()`，从最外层字典取出 `items`，循环访问每本书的字段。使用 `response.url` 检查最终编码结果。

### 题目 2 参考思路

连接失败发生在 `requests.get()` 阶段，没有 `response`，捕获后应 `return`。`404` 已经存在响应和状态码，可用 `raise_for_status()` 转换为 `HTTPError`。`200` 才进入 JSON 解析。`try` 中异常点后面的语句会被跳过，控制流转到匹配的 `except`。

### 题目 3 参考思路

将真实 `API_KEY` 写入 `.env` 并忽略该文件；提交只含占位符的 `.env.example`。先 `load_dotenv()`，再 `key = os.getenv("API_KEY")`，检查 `if not key`。认证头写成 `{"Authorization": f"Bearer {key}"}`。`bool(key)` 只验证取到非空值，不能证明密钥有效或权限足够。

### 题目 4 参考思路

基础地址作为 `url`，`q` 和 `limit` 放进 `params`，两个请求头放进 `headers`。服务器返回的状态通过 `response.status_code` 查看，`Content-Type` 通过 `response.headers` 查看，JSON 正文通过 `response.json()` 解析。发出的请求头保存在 `response.request.headers`。

### 题目 5 参考思路

`response.status_code` 是整数，必须与 `200` 比较。原条件为假，且没有 `else`，所以程序正常结束但不输出。修复比较类型并增加失败分支；调试时可以打印 `type(response.status_code)`，用事实确定原因。
