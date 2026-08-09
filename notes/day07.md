# Day 7 学习笔记：独立完成一个多模块 Python 项目

## 一、今日完成情况

Day 7 的任务不是继续照着示例补语法，而是独立设计并实现一个实习职位管理系统。项目最终拆分为以下文件：

```text
day07/
├── main.py             # 程序入口和菜单调度
├── job_manager.py      # 岗位相关的业务功能
├── storage.py          # JSON 数据的读取与保存
├── jobs.json           # 持久化数据
└── test_statistics.py  # 统计函数的自动测试
```

程序已经具备以下能力：

- 查看全部岗位；
- 添加岗位；
- 按公司名称搜索岗位；
- 修改岗位结果；
- 统计“接受”和“拒绝”的数量；
- 使用 JSON 保存数据；
- 处理文件不存在和 JSON 损坏；
- 使用自动测试验证统计函数；
- 通过 `main()` 和入口保护控制程序启动。

本项目主动把岗位状态缩小为“接受”和“拒绝”两种。这不是功能缺失，而是为了在当前阶段控制项目规模。先保证一个小系统完整、可靠，再扩展需求，是合理的软件开发方式。

## 二、数据结构与数据契约

每条岗位数据使用一个字典表示，多条岗位组成列表：

```python
jobs = [
    {
        "company": "tencent",
        "location": "shenzhen",
        "status": "拒绝"
    }
]
```

三个字段的含义必须在所有模块中保持一致：

- `company`：公司名称；
- `location`：工作地点；
- `status`：结果，只允许“接受”或“拒绝”。

这种约定称为数据契约。创建数据、搜索数据、修改数据、统计数据和测试数据都必须遵守同一契约。如果正式代码使用 `status`，某个功能却写成 `job`；或者正式数据使用“接受”，测试却写成 `accept`，程序之间就无法正确协作。

可以用常量集中保存合法状态：

```python
VALID_STATUS = ("接受", "拒绝")
```

这样可以避免在多个位置重复书写规则。

## 三、模块拆分与职责

项目变大以后，不应把菜单、业务功能和文件操作全部堆在一个文件里。本项目按照职责拆成三层：

```text
main.py
负责程序流程和调用功能
        ↓
job_manager.py
负责岗位的增、查、改、统计
        ↓
storage.py
负责 JSON 文件读取和保存
```

模块拆分的重点不是文件数量，而是每个模块只承担一类清晰的责任。

### `main.py` 的职责

- 加载数据；
- 展示菜单；
- 接收用户选项；
- 调用对应业务函数；
- 决定何时退出。

### `job_manager.py` 的职责

- 操作传入的岗位列表；
- 验证业务输入；
- 在真正修改数据后调用保存函数；
- 计算并展示统计结果。

### `storage.py` 的职责

- 把 Python 对象转换成 JSON 并写入文件；
- 从 JSON 文件恢复 Python 对象；
- 处理文件读取异常。

## 四、`main()`、局部变量和入口保护

早期版本在入口保护中创建全局变量：

```python
if __name__ == "__main__":
    loaded_job = load_job()
    main()
```

而 `main()` 又直接使用外部的 `loaded_job`。直接运行时可能正常，但导入模块后再调用 `main()`，这个变量并没有被创建，容易出现 `NameError`。

改进后的结构是：

```python
def main():
    loaded_jobs = load_job()
    # 后续流程都使用这个局部变量


if __name__ == "__main__":
    main()
```

此时数据由真正需要它的 `main()` 创建并管理，函数不再偷偷依赖外部全局状态。

入口保护的作用是区分两种使用方式：

- 直接运行文件：`__name__` 等于 `"__main__"`，启动程序；
- 被其他文件导入：条件不成立，只提供函数，不自动启动菜单。

## 五、输入清理和合法性验证

推荐的输入处理顺序是：

```text
接收输入 → 清理输入 → 验证输入 → 使用或保存
```

例如：

```python
company = input("请输入公司名称：").strip()

if not company:
    print("公司名称不能为空！")
    return
```

`.strip()` 会去除字符串首尾的空白字符：

```python
"  tencent  ".strip()  # "tencent"
"    ".strip()         # ""
```

### 空字符串与 `None` 的区别

这是当天最重要的易错点之一：

```python
"" is None  # False
```

- `""` 是一个存在的字符串，只是长度为 0；
- `None` 表示没有有效对象或某次操作失败。

`input()` 返回字符串。用户只按回车时得到空字符串，因此通常使用：

```python
if not company:
```

`load_job()` 则由我们主动约定：JSON 损坏时返回 `None`，因此调用方应准确判断：

```python
if loaded_jobs is None:
```

不能写成 `if not loaded_jobs`，因为空列表 `[]` 也是假值，但它代表“成功加载，只是没有数据”，程序仍应正常启动。

## 六、查询功能：匹配方式和查找标记

本项目只按公司名称查询，这是明确的功能设计，不需要擅自增加地点查询。

完全匹配和部分匹配的区别：

```python
keyword == company  # 两边必须完全相同
keyword in company  # company 中包含 keyword 即可
```

忽略英文大小写时，应将两边转换成相同形式：

```python
if keyword.lower() in job["company"].lower():
```

使用布尔标记可以判断整个循环结束后是否找到过结果：

```python
found = False

for job in jobs:
    if keyword in job["company"].lower():
        print(job)
        found = True

if not found:
    print("没有找到")
```

查询只读取数据，不应调用 `save_job()`。

## 七、修改功能的数据流

修改功能需要区分成功与失败：

```text
找到目标 → 验证新状态 → 修改内存数据 → 保存文件 → 提示成功
没有找到 → 提示失败 → 不保存
```

只有数据真正发生变化后才有保存的必要。如果公司不存在仍然保存，文件内容虽然可能没变，但程序做了一次没有意义的写入，也无法清楚表达操作是否成功。

当前设计按公司名称精确匹配，并默认每家公司只有一条岗位记录。在这个前提下逻辑成立。如果以后允许同一家公司拥有多个岗位，则需要增加岗位名称或唯一编号，否则无法确定具体要修改哪一条。

## 八、JSON 持久化与异常处理

保存数据：

```python
with open("day07/jobs.json", "w", encoding="utf-8") as file:
    json.dump(jobs, file, ensure_ascii=False, indent=4)
```

- `"w"`：写入模式；
- `encoding="utf-8"`：使用 UTF-8；
- `ensure_ascii=False`：中文直接保存为中文；
- `indent=4`：格式化 JSON，便于阅读。

读取时处理两种失败：

```python
def load_job():
    try:
        with open("day07/jobs.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print("数据文件损坏！")
        return None
```

两种返回值表达不同语义：

| 返回值 | 含义 | 主程序行为 |
|---|---|---|
| `[]` | 文件不存在，可视为第一次运行 | 正常进入菜单 |
| `None` | 文件存在但内容损坏 | 停止运行，避免覆盖数据 |

异常处理不只是写 `try / except`。返回方必须用清晰的值说明结果，调用方也必须正确处理这个值。

## 九、统计函数与自动测试

统计函数应尽量保持纯粹：接收数据、计算结果、返回结果，不修改原列表，也不直接依赖 `input()`。

测试覆盖了四种情况：

- 空列表；
- 接受和拒绝各一条；
- 全部接受；
- 全部拒绝。

辅助检查函数同时验证结果与原输入：

```python
result = calculate_job_statistics(jobs)

assert result == expected
assert jobs == original_jobs
```

第二个断言验证统计函数没有偷偷修改传入的数据。

### 定义测试不等于执行测试

下面的代码只定义了函数，不会自动执行：

```python
def test_empty():
    ...
```

需要使用 `run_tests()` 主动调用：

```python
def run_tests():
    test_empty()
    test_mixed()


if __name__ == "__main__":
    run_tests()
```

“程序没有报错”不一定表示测试通过，也可能是测试根本没有运行。必须看到测试确实被调用，最好再故意写错一次预期值，确认断言能够产生 `AssertionError`。

### 测试数据也必须遵守数据契约

正式程序使用“接受”和“拒绝”，测试却使用 `accept` 和 `refuse`，测试的就不是实际系统的数据。更危险的是，错误数据有时会碰巧得到正确结果，形成“假通过”。测试不是随便制造几个字典，而是使用可控数据验证正式规则。

## 十、UTF-8 文件编码与终端编码

文件编码和终端显示编码是两个不同问题：

- 文件编码决定字节如何保存在硬盘；
- 终端编码决定程序输出的字节如何显示。

如果程序按照 GBK 输出，而捕获工具按照 UTF-8 解读，就可能出现 `鎺ュ彈` 一类乱码，但源文件内容不一定损坏。

VS Code 用户设置已经加入：

```json
"files.encoding": "utf8",
"terminal.integrated.env.windows": {
    "PYTHONUTF8": "1"
}
```

新建 VS Code 终端后，可以检查：

```powershell
python -c "import sys; print(sys.stdout.encoding); print('中文测试：接受、拒绝')"
```

预期编码为 `utf-8`，中文正常显示。

## 十一、个人复盘与注意事项

1. 本次已经能够从空白开始设计多模块项目，而不是只在现有代码中填空，说明前六天的知识开始发生迁移。
2. 遇到的主要困难已经从“完全不知道 Python 语法”转变为模块之间如何协调、字段如何统一、异常如何传递和边界输入如何处理。这属于项目设计能力，而不只是语法记忆。
3. 开始写项目时压力较大，中途多次想放弃，但最终独立搭出了菜单、模块、JSON 和统计功能。以后遇到混乱时，应先写出数据结构和功能清单，再逐个实现，不需要在脑中同时维护整个项目。
4. 不要简单地把所有错误归因于“粗心”。例如 `None` 与空字符串的错误，本质上是没有分清返回值语义；理解原理比提醒自己细心更有效。
5. 功能范围由项目目标决定。只搜索公司、只保留两种状态都是合理的主动简化。重要的是把规则说明清楚，并让所有模块遵守规则。
6. 测试代码本身也可能写错或根本没有运行。看到退出码为 0 时，还要确认测试入口、测试数据和断言是否真实有效。
7. 使用 AI 时，应让 AI 帮助解释、审查和定位问题，但核心函数最好先自己设计和尝试，这样才能逐步恢复独立编程能力。

## 十二、独立综合复习题

### 题目 1：图书借阅记录管理

背景：某个命令行程序用列表保存图书，每本书的数据格式如下：

```python
{"title": "Python入门", "borrower": "小李", "status": "借出"}
```

`status` 只能是“在馆”或“借出”。

任务：实现 `add_book(books)`，接收书名、借阅人和状态。所有输入需要去除首尾空格；书名不能为空；状态必须合法；验证全部通过后才能把新字典加入列表。

验收标准：

- 空书名不会新增数据；
- 非法状态不会新增数据；
- 正常输入会新增一条字段完整的字典；
- 输入前后的多余空格不会保存进字典。

### 题目 2：安全读取配置文件

背景：程序从 `config.json` 读取配置。文件不存在表示用户第一次启动，可以使用空配置；文件存在但 JSON 格式错误表示配置损坏，程序必须停止，不能覆盖原文件。

任务：实现 `load_config()`，并在 `main()` 中正确处理其返回值。

验收标准：

- 正常 JSON 返回对应 Python 对象；
- 文件不存在返回空字典 `{}`；
- JSON 损坏时打印提示并返回 `None`；
- `main()` 收到 `{}` 时继续运行，收到 `None` 时立即结束。

### 题目 3：员工查询工具

背景：员工列表中的每条数据包含 `name`、`department` 和 `level`。系统规定只按员工姓名搜索，支持部分匹配并忽略英文大小写。

任务：实现 `search_employee(employees, keyword)`，返回所有匹配的员工列表。关键词为空时返回空列表，并打印“关键词不能为空”；没有结果时打印“未找到员工”。

验收标准：

- `"ali"` 能找到姓名为 `"Alice"` 的员工；
- 搜索不修改原员工列表；
- 一个关键词可以返回多条匹配结果；
- 空关键词与无结果能够得到不同提示。

### 题目 4：修改订单状态

背景：每个订单包含唯一的 `order_id` 和状态。合法状态为“待支付”“已支付”“已取消”。只有找到目标订单并且新状态合法时，才能修改并调用 `save_orders(orders)`。

任务：实现 `change_order_status(orders, order_id, new_status)`。

验收标准：

- 找不到订单时提示失败，不调用保存；
- 新状态非法时不修改、不保存；
- 修改成功时只改变目标订单；
- 成功后只调用一次保存函数并给出成功提示。

### 题目 5：为统计函数设计有效测试

背景：函数 `calculate_score_statistics(records)` 接收成绩列表，每条记录包含 `name` 和 `passed`，其中 `passed` 是布尔值。函数返回：

```python
{"passed_count": 2, "failed_count": 1}
```

任务：不使用第三方测试框架，为该函数编写可直接运行的自动测试文件。

验收标准：

- 覆盖空列表、通过与未通过混合、全部通过、全部未通过；
- 每个场景都有明确预期结果；
- 验证统计函数没有修改原记录列表；
- 运行测试文件时所有测试会被真正调用；
- 故意写错一个预期结果时会触发 `AssertionError`。

## 十三、复习题参考思路

### 题目 1 参考思路

先对三个输入调用 `.strip()`，再依次检查书名和状态。任何检查失败都立即 `return`。所有验证完成后再创建字典并 `append()`，避免先修改列表再发现输入非法。

### 题目 2 参考思路

在 `json.load()` 外使用 `try / except`。分别捕获 `FileNotFoundError` 和 `json.JSONDecodeError`。调用方必须使用 `is None` 判断损坏，不能使用 `if not config`，因为空字典也是假值。

### 题目 3 参考思路

先清理关键词并转换为小写，遍历员工列表，用 `keyword in employee["name"].lower()` 判断。将匹配项加入结果列表，循环结束后根据列表是否为空决定是否提示未找到。

### 题目 4 参考思路

先验证状态，再遍历查找唯一编号。找到后修改、保存、提示并 `return`；只有循环完整结束仍未返回，才说明订单不存在。可以用模拟保存函数记录调用次数。

### 题目 5 参考思路

编写一个公共检查函数，先复制输入记录，再调用统计函数，分别断言返回值和原输入。用四个无参数测试函数准备不同场景，再由 `run_tests()` 统一调用，最后使用入口保护启动测试。

## 十四、Git 与 GitHub 发布补充

### 1. Git、GitHub 与 GitHub CLI

- Git 是本地版本管理软件，断网时仍能执行 `status`、`add`、`commit`、`log` 和 `diff`。
- GitHub 是远程仓库托管与协作平台，提供代码浏览、Pull Request、Issue、Actions 和 Release 等功能。
- `gh` 是 GitHub CLI，用来登录 GitHub、创建远程仓库和操作 Pull Request 等网站功能；它不能替代 Git 的本地版本管理。

### 2. 从本地文件到 GitHub 的完整路径

```text
工作区
  ↓ git add
暂存区
  ↓ git commit
本地仓库与本地分支
  ↓ git push
GitHub远程仓库与远程分支
```

保存文件、暂存、提交和推送是四个不同动作：

- 保存文件只改变工作区；
- `git add` 选择下一次提交的内容；
- `git commit` 创建本地历史快照；
- `git push` 才把本地提交上传到 GitHub。

GitHub 不会获得未提交、未推送或被 `.gitignore` 忽略的文件。

### 3. `origin`、`main`、`origin/main` 与 `HEAD`

`origin` 是远程仓库网址在本地的简称，不是分支，也不是 GitHub 的固定关键字：

```text
origin → https://github.com/obbosive/ai-agent-learning.git
```

- `main`：本地分支；
- GitHub 上的 `main`：远程服务器上的分支；
- `origin/main`：本地保存的“上次已知的远程 main 位置”；
- `HEAD`：当前正在操作的位置，通常指向当前分支。

`origin/main` 不是 GitHub 的实时画面。只有 `fetch`、`pull` 或成功的 `push` 等网络操作才会更新它。

### 4. 第一次推送与上游关系

第一次推送使用：

```powershell
git push -u origin main
```

其中：

- `origin main` 说明这一次把本地 `main` 推到哪个远程和分支；
- `-u` 是 `--set-upstream`，让 Git 记住本地 `main` 默认跟踪 `origin/main`。

建立上游关系后，通常可以简写为：

```powershell
git push
git pull
```

如果第一次忘记 `-u`，提交仍可能成功上传，只是后续直接执行 `git push` 或 `git pull` 时可能无法确定默认目标。可以再次执行 `git push -u origin main` 补上关系。

### 5. `fetch` 与 `pull`

`git fetch origin` 会真实下载远程新增的提交、目录和文件内容，保存进本地 `.git` 数据库，并更新 `origin/main`，但不会移动当前 `main`，也不会修改工作区文件。

下载后可以先安全检查：

```powershell
git status -sb
git log --oneline --decorate --graph --all
git diff main..origin/main
```

`git pull` 大致等于：

```text
git fetch
+
将远程变化合入当前分支
```

如果本地没有额外提交，Git 可以进行 `Fast-forward`：只把本地分支指针向前移动，不额外创建合并提交。

### 6. `clone` 与下载 ZIP

`git clone` 会创建本地目录、下载完整提交历史与标签、创建 `.git` 数据库、检出默认分支，并自动把远程地址保存为 `origin`。它适合继续开发项目。

下载 ZIP 只获得某一个版本的普通文件，没有 `.git`、提交历史和远程关系，适合只查看或运行代码。

Clone 只配置 Git 层面的项目，不会自动安装 Python、第三方依赖、VS Code 插件、虚拟环境、数据库和环境变量。真实项目仍需根据 README 配置运行环境。

### 7. 分支与 Pull Request

分支本质上是指向某个提交的可移动指针，不是复制一整份项目文件。

```powershell
git switch -c agent/github-notes
```

会从当前位置创建新分支并让 `HEAD` 切换过去。创建瞬间，新分支和 `main` 指向同一个提交；在新分支产生提交后，新分支向前移动，而 `main` 保持原位。

典型团队流程是：

```text
从main创建功能分支
→ 在功能分支修改与提交
→ push功能分支
→ 创建Pull Request
→ 检查差异与自动测试
→ 合并回main
```

Pull Request 不是下载代码，而是一份“请求把某个分支的修改合并进目标分支”的协作记录。它集中展示提交、文件差异、讨论和检查结果。

### 8. 当前项目的发布结果

- GitHub 仓库：`obbosive/ai-agent-learning`；
- 远程简称：`origin`；
- 默认分支：`main`；
- `main` 已与 `origin/main` 建立上游关系；
- `v0.1.0` 标签固定指向 Day 6 里程碑；
- Day 7 项目、每日笔记和完整提交历史已经上传；
- GitHub CLI 通过临时 Clash HTTP 代理完成登录和发布，代理环境变量只在当前 PowerShell 窗口生效。
