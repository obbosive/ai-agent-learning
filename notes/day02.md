# Day 2 学习笔记：VS Code、Python 基础恢复与 Git 差异检查

> 学习日期：2026-08-04 至 2026-08-05  
> 学习方式：基础诊断 + 逐步修错 + 原理复述  
> 完成程序：`day02/diagnostic.py` 论文数据诊断程序

## 一、今天的学习结论

今天不是从零学习 Python，而是通过一个小任务检查以前学过的基础知识还能否主动写出来。

诊断结果是：

- 列表、字典、循环、判断、计数等解题思路仍然存在；
- 面对空白文件时，Python 的具体语法提取不够熟练；
- 容易把以前接触过的 Java 或 JavaScript 语法混入 Python；
- 得到提示后能够理解原因并独立修改；
- 已经能够通过程序输出判断逻辑是否正确，而不只看“有没有报错”；
- 已完成一次 VS Code 编辑、Python 运行、错误排查和 Git 提交的完整流程。

因此，后续重点不是机械重学所有入门章节，而是通过连续的小项目恢复主动编码能力，并针对暴露出来的漏洞补习。

---

## 二、VS Code、PowerShell 和 Python 的分工

今天正式改用 VS Code 开发。

三个工具的职责不同：

```text
VS Code：编辑代码、管理项目文件、展示提示和集成终端
PowerShell：接收命令并启动其他程序
Python 解释器：真正读取和执行 Python 代码
```

运行命令：

```powershell
python .\day01\hello.py
```

真正执行 `hello.py` 的是 Python 解释器。VS Code 只是提供工作界面，PowerShell 负责接收命令。

### VS Code 的主要区域

- 左侧资源管理器：查看项目中的文件夹和文件。
- 中间编辑区：查看和修改代码。
- 底部终端：输入 PowerShell 命令并查看程序输出。
- 底部状态栏：显示 Git 分支、编码、换行符、语言类型和 Python 解释器。

今天状态栏中接触到：

- `main`：当前 Git 分支。
- `UTF-8`：当前文件编码。
- `CRLF`：Windows 常见换行格式。
- `Python 3.12.10`：VS Code 当前选择的 Python 解释器。

### Python 插件和 Python 解释器不是同一个东西

Microsoft Python 插件为 VS Code 提供语法提示、解释器选择、运行和调试支持，但它本身不是负责执行程序的 Python。

可以理解为：

```text
Python 插件：让 VS Code 更懂 Python
Python 解释器：真正运行 Python
```

中文语言包只改变 VS Code 的界面语言，不会改变 Python 代码、解释器或 Git。

### 工作区信任

VS Code 第一次打开文件夹时可能进入 Restricted Mode（受限模式）。信任自己创建的项目后，插件、运行和调试功能才能完整启用。

陌生来源的项目不能不经检查就随便信任，因为受信任的工作区可能运行任务、脚本或插件相关操作。

---

## 三、为什么 `python .` 会报错

今天曾执行：

```powershell
python .
```

其中 `.` 表示当前文件夹，而不是一个具体的 `.py` 文件。Python 会尝试把这个文件夹当作可运行模块，并寻找特殊入口文件 `__main__.py`。

当前项目根目录没有这个入口，因此出现类似：

```text
can't find '__main__' module
```

改为指定具体文件后运行成功：

```powershell
python .\day01\hello.py
```

需要记住：

```text
python 文件路径    → 执行该脚本文件
python 文件夹路径  → 尝试寻找该文件夹中的模块入口
```

这个报错不是 Python 没安装，也不是 VS Code 损坏，而是传给解释器的目标不对。

Windows 中还可以使用 `py` 启动器运行 Python，但当前学习阶段统一使用 `python`，避免同时引入不必要的概念。

---

## 四、VS Code 中的文件状态提示

今天在文件标签和资源管理器中看到过：

### 白色圆点

文件标签旁边的白色圆点表示编辑内容尚未保存到磁盘。

```text
Ctrl + S：保存当前文件
```

运行代码前要确认文件已经保存，否则解释器可能运行的是磁盘上的旧内容。

### `U`

`U` 是 Untracked 的缩写，表示这是一个 Git 尚未跟踪的新文件。

它不是 Python 报错，也不代表文件有问题。执行 `git add` 后，Git 才开始跟踪并暂存该文件。

---

## 五、数据建模：为什么使用“列表中放字典”

任务需要保存多篇论文，每篇论文又包含标题、年份和阅读状态。

可以拆成两个问题：

```text
有多篇同类数据       → 使用列表
每篇数据有多个属性   → 使用字典
```

数据结构：

```python
papers = [
    {"title": "ReAct", "year": 2022, "is_read": True},
    {"title": "AutoGen", "year": 2023, "is_read": False},
    {"title": "MetaGPT", "year": 2023, "is_read": False},
]
```

### 外层列表

```python
[第一篇论文, 第二篇论文, 第三篇论文]
```

列表保存一组有顺序的元素，适合后续使用 `for` 依次处理。

### 内层字典

```python
{"title": "ReAct", "year": 2022, "is_read": True}
```

字典使用键值对描述一件事物的属性：

| 键 | 值 | 含义 |
|---|---|---|
| `"title"` | `"ReAct"` | 论文标题 |
| `"year"` | `2022` | 发表年份 |
| `"is_read"` | `True` | 是否已读 |

### 为什么字典键需要引号

```python
{"title": "ReAct"}
```

`"title"` 是字符串键，表示这个属性的名字。

如果写成：

```python
{title: "ReAct"}
```

Python 会把 `title` 当作变量名，并尝试寻找这个变量，而不是把它当作文字属性名。

### 布尔值

```python
True
False
```

布尔值用于表达“是或否”。Python 中首字母必须大写，而且不能加引号。

```python
True       # 布尔值
"True"     # 字符串
```

二者含义不同。

---

## 六、Python 与 Java/JavaScript 语法混淆

第一次独立编写时出现过类似写法：

```text
for (...) { ... }
!条件
变量++
p.isread
```

这些写法更接近 Java 或 JavaScript，不是当前任务需要的 Python 写法。

对应关系：

| 想表达的意思 | 容易混入的写法 | Python 写法 |
|---|---|---|
| 标记代码块 | `{ ... }` | 冒号加缩进 |
| 逻辑取反 | `!condition` | `not condition` |
| 数值增加 1 | `count++` | `count += 1` |
| 读取字典的键 | `paper.is_read` | `paper["is_read"]` |
| 输出变量内容 | `"paper.title"` | 变量或 f-string |

这不说明完全不懂编程，而是多种语言的语法记忆互相干扰。恢复阶段要先判断自己当前写的是哪一种语言。

---

## 七、Python 依靠缩进表示代码块

Python 不使用大括号包围 `for`、`if` 和 `else` 的代码块，而使用冒号和缩进。

```python
for paper in papers:
    if not paper["is_read"]:
        not_read_num += 1
```

层级关系：

```text
for 循环
    if 判断
        条件成立时执行的语句
```

通常每深入一级缩进 4 个空格。VS Code 中可以使用 `Tab` 增加缩进、`Shift + Tab` 减少缩进。

### 今天的 `else` 报错原因

曾经出现：

```python
if not paper["is_read"]:
    not_read_num += 1

read_status = "未读"
else:
    read_status = "已读"
```

`read_status = "未读"` 与 `if` 处于同一层级，意味着 `if` 已经结束。随后出现 `else` 时，Python 无法把它与前面的 `if` 连接起来。

正确结构：

```python
if not paper["is_read"]:
    not_read_num += 1
    read_status = "未读"
else:
    read_status = "已读"
```

需要记住：

- `if` 和它的 `else` 必须对齐。
- `if` 与 `else` 之间不能插入其他同级语句。
- 属于分支的语句需要比 `if` 或 `else` 多缩进一级。
- 报错可能标在 `else`，但根因可能是它前一行缩进错误。

---

## 八、循环、判断和计数

遍历论文：

```python
for paper in papers:
```

每轮循环会从 `papers` 列表中取出一个字典，并暂时交给变量 `paper`。

判断论文是否未读：

```python
if not paper["is_read"]:
```

假设当前值是 `False`：

```text
paper["is_read"] → False
not False        → True
```

因此进入 `if` 并增加未读计数：

```python
not_read_num += 1
```

它等价于：

```python
not_read_num = not_read_num + 1
```

Python 不使用 `not_read_num++`。

---

## 九、函数、参数、调用与返回值

今天定义了：

```python
def get_read_status(is_read):
    if not is_read:
        return "未读"
    else:
        return "已读"
```

函数可以理解为给一段功能起名字。

### `def`

```python
def get_read_status(...):
```

`def` 用来定义函数。执行到函数定义时，Python 记住这段功能，但不会立刻执行函数体。

### 参数

```python
is_read
```

这是函数内部接收数据的参数名。

### 调用

```python
get_read_status(paper["is_read"])
```

调用时才真正执行函数体。`paper["is_read"]` 是传进去的实际值。

### 返回值

```python
return "未读"
```

`return` 会结束当前函数调用，并把结果交回调用位置。

```python
read_status = get_read_status(paper["is_read"])
```

最终，函数返回的 `"已读"` 或 `"未读"` 会赋给 `read_status`。

---

## 十、条件逻辑曾经写反

曾出现：

```python
if not is_read:
    return "已读"
else:
    return "未读"
```

如果 `is_read` 是 `False`，那么 `not is_read` 是 `True`，程序会错误返回“已读”。

正确写法可以是正向判断：

```python
if is_read:
    return "已读"
else:
    return "未读"
```

也可以保留取反判断，但返回值要对应：

```python
if not is_read:
    return "未读"
else:
    return "已读"
```

个人提醒：看到 `not` 时，不要只凭直觉读代码。可以代入 `True` 和 `False` 各走一次。

---

## 十一、为什么程序能运行仍可能是错的

今天接触到三类问题：

### 1. 语法错误

Python 无法理解代码结构，程序不能正常启动，例如大括号、`++`、错误缩进。

### 2. 运行时错误

语法能够解析，但执行到某一步时失败，例如访问不存在的字典键。

### 3. 逻辑错误

程序能完整运行，但输出不符合需求，例如：

- 已读和未读状态写反；
- 只输出最后一篇论文；
- 变量保留了上一轮循环的旧值。

逻辑错误往往比语法错误更危险，因为程序不会主动崩溃提醒。

因此不能只检查“有没有红线”和“能不能运行”，还要把实际输出与预期输出进行比较。

---

## 十二、缩进如何决定每条语句执行几次

最终循环结构：

```python
for paper in papers:
    if not paper["is_read"]:
        not_read_num += 1

    read_status = get_read_status(paper["is_read"])
    title = paper["title"]
    year = paper["year"]
    print(f"{title}-{year}-{read_status}")

print(f"未读论文数量:{not_read_num}")
```

执行次数：

| 语句 | 位置 | 执行次数 |
|---|---|---:|
| 未读数量加一 | `if` 内 | 仅未读时 |
| 获取阅读状态 | `for` 内、`if` 外 | 每篇一次 |
| 获取标题与年份 | `for` 内 | 每篇一次 |
| 输出论文信息 | `for` 内 | 每篇一次 |
| 输出最终数量 | `for` 外 | 全部结束后一次 |

### 为什么获取状态不能放在 `else` 中

获取显示状态是每一篇论文都必须进行的操作，不只属于“已读”分支。

如果放在 `else` 中：

```python
if 当前论文未读:
    增加计数
else:
    获取状态
```

未读论文不会重新给 `read_status` 赋值。Python 变量不会在每轮循环开始时自动删除，于是可能继续使用上一轮留下的状态。

原则：

```text
只在某种情况下执行 → 放进 if/else
无论情况如何都执行   → 放在 if/else 外
```

### 为什么最终数量放在 `for` 外

如果放在循环里面，会输出每轮结束时的中间统计结果。

放在循环外，只会在全部论文处理完后输出最终总数。

---

## 十三、f-string 格式化输出

```python
print(f"{title}-{year}-{read_status}")
```

字符串前面的 `f` 表示格式化字符串。大括号中的表达式会被替换成实际值。

```python
title = "ReAct"
print(f"论文标题：{title}")
```

输出：

```text
论文标题：ReAct
```

如果写成普通字符串：

```python
print("title-year-read_status")
```

Python 只会原样输出文字，不会读取变量。

注意：f-string 中的 `{}` 用于插入表达式，与 Java/JavaScript 用来标记代码块的大括号不是同一个用途。

---

## 十四、一次简单重构

最初，判断“已读/未读”的代码直接写在循环中。后来把这段逻辑放入 `get_read_status()` 函数。

这属于重构：

```text
改变代码组织方式，但不改变程序对外行为
```

重构的目的包括：

- 让一段逻辑拥有清晰名称；
- 减少主流程中的细节；
- 以后可以重复调用；
- 更方便单独检查和修改。

重构后必须再次运行并对照预期输出，不能因为“只是整理代码”就不验证。

---

## 十五、当前程序的标准格式参考

当前程序已经能正确运行。按照常见 Python 空格和缩进风格，可以整理为：

```python
papers = [
    {"title": "ReAct", "year": 2022, "is_read": True},
    {"title": "AutoGen", "year": 2023, "is_read": False},
    {"title": "MetaGPT", "year": 2023, "is_read": False},
]


def get_read_status(is_read):
    if not is_read:
        return "未读"
    else:
        return "已读"


not_read_num = 0

for paper in papers:
    if not paper["is_read"]:
        not_read_num += 1

    read_status = get_read_status(paper["is_read"])
    title = paper["title"]
    year = paper["year"]
    print(f"{title}-{year}-{read_status}")

print(f"未读论文数量:{not_read_num}")
```

空格和空行多数不改变程序结果，但统一格式能提高可读性。后续会学习使用格式化工具自动处理，不需要现在手工追求完美。

---

## 十六、`git diff --staged` 的作用

执行：

```powershell
git diff --staged
```

比较的是：

```text
最新提交 ↔ 暂存区
```

它用于检查“下一次提交具体准备保存什么”。这是只读操作，不会改变文件、暂存区或提交历史。

### 为什么新文件在普通 `git diff` 中可能看不到

未跟踪文件还没有进入 Git 的比较体系。执行 `git add` 后，新文件进入暂存区，`git diff --staged` 才能显示完整新增内容。

### 差异输出含义

```text
new file mode 100644
```

表示这是一个新加入 Git 的普通文件。

```text
--- /dev/null
+++ b/day02/diagnostic.py
```

表示旧版本中不存在该文件，新版本新增了它。`/dev/null` 可以理解为原来没有内容。

```text
@@ -0,0 +1,22 @@
```

表示旧文件有 0 行，新文件新增第 1～22 行。

每行前面的 `+` 是 Git 的新增标记，不属于 Python 源码。

---

## 十七、Git 分页查看器 `less`

当 diff 内容超过一屏时，Git 会使用分页查看器展示结果。底部出现：

```text
(END)
```

表示已经到达输出末尾，不是命令卡死。

常用操作：

| 按键 | 作用 |
|---|---|
| 空格 | 向下翻一页 |
| `b` | 向上翻一页 |
| 上下方向键 | 逐行移动 |
| `q` | 退出分页器 |

`q` 是分页器中的按键操作，不是需要在 PowerShell 提示符后输入的命令。

如果临时不想使用分页器，可以执行：

```powershell
git --no-pager diff --staged
```

---

## 十八、Day 2 Git 结果

完成的提交：

```text
e0480b5 提交paper diafnostic文件
```

提交成功信息表明：

- 新增并提交了 `day02/diagnostic.py`；
- 文件包含 22 行；
- `main` 分支指向新的提交。

提交说明中的 `diafnostic` 拼写应为 `diagnostic`。这不影响代码和提交有效性，但以后提交前可以快速检查一次说明，让历史更清晰。

提交后状态：

```text
On branch main
nothing to commit, working tree clean
```

表示 Day 2 程序已经作为历史快照保存，工作区和暂存区都没有遗留修改。

---

## 十九、个人易错点与改进策略

### 1. 不是逻辑全忘了，而是语法提取困难

第一次尝试已经正确想到列表、字典、循环、判断和计数器。以后卡住时先把自然语言步骤写出来，再逐步翻译成 Python，不要立即让 AI 生成完整程序。

### 2. 容易混合多种语言语法

写 Python 前主动提醒自己：

```text
代码块用缩进，不用大括号
取反用 not
增加一用 += 1
字典使用 ["key"]
```

### 3. 缩进不是美观问题，而是程序结构

每写完 `for`、`if`、`else`，先观察 VS Code 的缩进引导线，确认代码属于哪个层级。

### 4. 能运行不等于正确

每个练习都先写出预期输出，再与实际输出逐行比较。

### 5. 变量会保留上次赋的值

如果某个分支没有重新赋值，程序可能继续使用之前的旧值。需要检查每条执行路径上变量是否都获得正确值。

### 6. 函数调用是否应该放在分支里，要看它是否每种情况都需要

如果每篇论文都要获取状态，就应放在 `if/else` 外，而不是只在某个分支调用。

### 7. Git 长输出不是卡死

看到 `(END)`，先想到分页器并按 `q`，不要反复按回车或重新执行命令。

### 8. 提交说明也需要检查

提交说明不会影响程序运行，但它是未来阅读历史的重要信息。提交前检查拼写和描述是否准确。

---

## 二十、Day 2 复习题

建议下一次学习前不看答案回答：

1. VS Code、PowerShell 和 Python 解释器分别负责什么？
2. 为什么 `python .` 与 `python .\day02\diagnostic.py` 的含义不同？
3. VS Code 文件旁边的白点和 `U` 分别表示什么？
4. 为什么多篇论文适合用列表，而一篇论文适合用字典？
5. 为什么字典键 `"title"` 通常需要引号？
6. Python 为什么不使用 `{}` 包围 `if` 和 `for` 代码块？
7. `not False` 的结果是什么？
8. `not_read_num += 1` 等价于什么？
9. `paper["title"]` 表达什么含义？
10. 定义函数和调用函数有什么区别？
11. 参数和返回值分别有什么作用？
12. 为什么 `read_status` 要在每轮循环中重新获得值？
13. 为什么输出每篇论文的 `print` 在 `for` 内，而最终数量的 `print` 在 `for` 外？
14. 语法错误、运行时错误和逻辑错误有什么区别？
15. `git diff --staged` 比较哪两个位置？
16. diff 中的 `/dev/null` 和每行前面的 `+` 分别表示什么？
17. Git 输出底部出现 `(END)` 时应怎样退出？

### 一句话复盘

今天在 VS Code 中用列表和字典建立论文数据，通过循环、判断、函数和 f-string 完成统计输出，并学会了从运行结果发现逻辑错误以及在提交前使用 `git diff --staged` 检查暂存内容。
