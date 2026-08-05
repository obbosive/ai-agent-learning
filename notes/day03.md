# Day 3 学习笔记：JSON 持久化、文件读写与异常处理

> 学习日期：2026-08-05  
> 学习目标：让论文数据在程序退出后仍能保留，并在数据文件不存在时安全启动  
> 完成文件：`day03/paper_manager.py`、`day03/papers.json`

## 一、今天完成了什么

今天完成了论文管理程序的第一套持久化流程：

```text
从 JSON 读取数据
→ 在 Python 内存中使用或修改数据
→ 将修改后的数据保存回 JSON
→ 程序退出
→ 再次运行时恢复上次的数据
```

同时学习了：

- 编辑器内存、程序内存和磁盘文件的区别；
- JSON 与 Python 列表、字典、布尔值之间的转换；
- `with open()`、`json.dump()` 和 `json.load()`；
- 序列化、反序列化与持久化；
- 把读写操作封装成函数；
- `try/except FileNotFoundError`；
- 如何验证正常流程和异常流程；
- 如何理解 `NameError`、`TypeError` 等报错。

---

## 二、数据究竟存在哪里

### 1. Python 源代码文件

`.py` 文件保存在硬盘上。每次运行时，Python 根据源代码创建变量和对象。

### 2. VS Code 尚未保存的内容

如果文件标签旁边还有白色圆点，修改只在 VS Code 的编辑内存中，还没写入硬盘。

```text
编辑代码 → 暂时在 VS Code 内存中
Ctrl + S → 写入硬盘上的 .py 文件
```

Python 命令读取的是硬盘文件，所以未保存时可能运行旧代码。

### 3. Python 运行时内存

Python 启动后会在内存中创建列表和字典：

```python
papers.append(new_paper)
```

这只修改当前进程中的对象。程序退出后，该对象会被释放。

### 4. JSON 数据文件

JSON 文件保存在磁盘上。只有明确调用保存功能后，内存修改才会持久化。

```text
paper["is_read"] = True → 修改内存
save_papers(papers)     → 写入磁盘
```

核心原则：内存变量不会自动与磁盘文件同步。

---

## 三、持久化、序列化和反序列化

### 持久化

程序结束后，数据仍保存在磁盘等长期存储中。

### 序列化

把内存中的 Python 数据转换成适合保存或传输的格式：

```text
Python 列表/字典 → JSON 文本
```

使用：

```python
json.dump(papers, file)
```

### 反序列化

读取 JSON 文本并重新创建 Python 数据：

```text
JSON 文本 → Python 列表/字典
```

使用：

```python
json.load(file)
```

---

## 四、JSON 与 Python 类型对应

| JSON | Python |
|---|---|
| 数组 `[]` | 列表 `list` |
| 对象 `{}` | 字典 `dict` |
| 字符串 | 字符串 `str` |
| 数字 | `int` 或 `float` |
| `true` | `True` |
| `false` | `False` |
| `null` | `None` |

Python 中：

```python
{"is_read": True}
```

保存到 JSON 后：

```json
{"is_read": true}
```

读取回来后又成为 Python 的 `True`。

JSON 中只有数据，没有 `papers =` 这样的变量赋值；字符串和键必须使用双引号。

---

## 五、导入 JSON 标准库

```python
import json
```

`json` 是 Python 标准库，不需要额外安装。导入后可使用：

```python
json.dump(...)
json.load(...)
```

---

## 六、使用 `with open()` 操作文件

写入：

```python
with open("day03/papers.json", "w", encoding="utf-8") as file:
    json.dump(papers, file, ensure_ascii=False, indent=4)
```

读取：

```python
with open("day03/papers.json", "r", encoding="utf-8") as file:
    papers = json.load(file)
```

### `"r"` 读取模式

只读取文件；文件不存在时会产生 `FileNotFoundError`。

### `"w"` 写入模式

文件不存在时创建；文件存在时清空旧内容再重写。因此写入前要确认数据完整。

### `encoding="utf-8"`

指定文本编码，避免中文读写出现乱码。

### 为什么使用 `with`

`with` 代码块结束后，Python 会自动关闭文件并释放资源。

### 缩进层级

```text
def
    with
        json.dump 或 json.load
```

今天曾因为 `json.dump()` 和 `return json.load()` 少缩进一级而被 VS Code 标错。

---

## 七、相对路径从哪里计算

今天使用的是：

```python
"day03/papers.json"
```

当前从项目根目录运行：

```powershell
python .\day03\paper_manager.py
```

因此相对路径从 `C:\Users\23854\Desktop\实习\ai-agent-learning` 开始计算。

运行前要观察 PowerShell 提示符，确认当前目录正确。

---

## 八、`json.dump()` 的参数

```python
json.dump(papers, file, ensure_ascii=False, indent=4)
```

- `papers`：要写入的 Python 数据；
- `file`：目标文件对象；
- `ensure_ascii=False`：中文保持原样；
- `indent=4`：使用 4 空格排版，便于阅读。

写文件成功时，终端可以没有任何输出。成功结果体现在文件创建或内容改变。

---

## 九、`json.load()` 的结果

```python
loaded_papers = json.load(file)
```

它读取 JSON 并创建 Python 对象。今天用 `type()` 验证最外层数据是列表。

---

## 十、封装保存和读取函数

```python
def save_papers(papers):
    with open("day03/papers.json", "w", encoding="utf-8") as file:
        json.dump(papers, file, ensure_ascii=False, indent=4)
```

```python
def load_papers():
    with open("day03/papers.json", "r", encoding="utf-8") as file:
        return json.load(file)
```

封装后，主流程可以表达为：

```python
papers = load_papers()
# 修改 papers
save_papers(papers)
```

文件模式、编码等细节被放进函数内部。

---

## 十一、函数与返回值

曾经只写：

```python
load_papers()
print(loaded_papers)
```

函数虽然返回了数据，但结果没有保存，随后产生 `NameError`。

正确写法：

```python
loaded_papers = load_papers()
```

| 写法 | 含义 |
|---|---|
| `load_papers` | 函数本身 |
| `load_papers()` | 调用函数 |
| `loaded_papers` | 保存结果的列表变量 |
| `loaded_papers()` | 错误地尝试调用列表 |

曾写成 `for paper in loaded_papers():`，导致：

```text
TypeError: list object is not callable
```

因为括号表示调用，而列表不是函数。正确写法是：

```python
for paper in loaded_papers:
```

---

## 十二、读取、修改、保存是三件事

```python
loaded_papers = load_papers()

for paper in loaded_papers:
    if paper["title"] == "MetaGPT":
        paper["is_read"] = True

save_papers(loaded_papers)
```

执行关系：

```text
load_papers()               → 磁盘数据复制到内存
paper["is_read"] = True    → 修改内存对象
save_papers(loaded_papers) → 内存数据写回磁盘
```

省略保存时，终端仍可能打印新值，但不能证明磁盘已经更新。

保存通常放在循环外，全部修改完成后统一写一次，避免重复磁盘操作。

---

## 十三、Python 交互模式

只执行：

```powershell
python
```

会进入 REPL，提示符变为 `>>>`。

退出可输入：

```python
exit()
```

也可以用 `quit()`；Windows 下还可按 `Ctrl + Z` 后回车。

`Ctrl + C` 只中断当前输入并显示 `KeyboardInterrupt`，不会退出 REPL。

---

## 十四、异常与错误类型

- 语法错误：Python 无法理解代码结构；
- 运行时异常：代码结构正确，但执行中发生问题；
- 逻辑错误：程序运行完成，但结果不符合需求。

读取不存在的文件会产生运行时异常：

```text
FileNotFoundError
```

---

## 十五、`try/except FileNotFoundError`

```python
def load_papers():
    try:
        with open("day03/papers.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print("没有找到论文数据文件，暂时使用空列表")
        return []
```

执行流程：

```text
进入 try
→ 文件存在：读取并返回列表
→ 文件不存在：跳到 except FileNotFoundError
→ 输出提示并返回空列表
```

文件缺失时仍返回列表，只是内容为空，使函数返回类型保持稳定。

`except` 必须与 `try` 对齐。

---

## 十六、为什么不用裸 `except:`

裸 `except:` 会捕获范围过大的错误，包括：

- 文件不存在；
- JSON 格式损坏；
- 变量拼写错误；
- 其他不应该被忽略的问题。

它可能把真正的 Bug 伪装成“没有数据”，甚至导致空列表被写回文件。

原则是：只捕获当前能够明确处理的异常。

今天只处理：

```python
except FileNotFoundError:
```

JSON 内容损坏时可能产生 `json.JSONDecodeError`，目前先让它正常暴露。

---

## 十七、异常分支必须实际测试

只在文件存在时运行，不能证明 `except` 正确。

今天的安全测试：

1. 文件存在时运行，读到三篇论文；
2. 暂时把 `papers.json` 改名为 `papers_backup.json`；
3. 再次运行，输出提示、`[]` 和列表类型；
4. 把文件名恢复为 `papers.json`；
5. 再次运行，重新读到三篇论文。

验证结果：

```text
文件存在 → 正常列表
文件缺失 → 空列表
文件恢复 → 正常列表
```

测试重要文件时优先使用临时改名，不直接删除。

---

## 十八、今天出现的错误与根因

### 1. 写了代码却没有生成 JSON

原因：文件未按 `Ctrl + S`，Python 执行的是硬盘上的旧版本。

### 2. `NameError`

原因：调用函数后没有把返回值赋给变量。

### 3. `list object is not callable`

原因：把列表写成 `loaded_papers()`，错误地加了调用括号。

### 4. `aper` 与 `paper`

循环变量拼写不一致。变量名必须完全相同。

### 5. 输出改变但 JSON 没变

原因：只修改内存，忘记调用 `save_papers()`。

### 6. 裸 `except:`

原因：异常范围过宽。应精确写成 `except FileNotFoundError:`。

### 7. 实验代码未清理

异常测试前若仍自动保存，空列表可能被写成新文件并干扰结果。

---

## 十九、当前程序参考结构

```python
import json


def save_papers(papers):
    with open("day03/papers.json", "w", encoding="utf-8") as file:
        json.dump(papers, file, ensure_ascii=False, indent=4)


def load_papers():
    try:
        with open("day03/papers.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print("没有找到论文数据文件，暂时使用空列表")
        return []


loaded_papers = load_papers()

print(loaded_papers)
print(type(loaded_papers))
```

这里使用标准空格格式作为复习参考。当前功能已正确，后面会学习自动格式化工具。

---

## 二十、个人学习提醒

1. 运行前确认文件已保存，标签旁边没有白点。
2. 文件写入成功不一定有终端输出，要检查目标文件。
3. 调用有返回值的函数时，要决定是否用变量接住结果。
4. 括号代表调用，列表变量后不要随便加 `()`。
5. 变量拼写必须一致，VS Code 黄色提示也应检查。
6. 修改内存后需要显式保存，文件不会自动同步。
7. 读报错先看最后一行异常类型，再向上找文件和行号。
8. 只捕获明确异常，不使用裸 `except:`。
9. 正常路径和异常路径都要执行测试。
10. 测试重要文件时使用临时改名等可恢复操作。
11. 实验结束后及时清理一次性代码。
12. 不要只用“粗心”概括错误，要判断是未保存、缩进、拼写、调用方式还是数据流问题。

---

## 二十一、Day 3 复习题

1. VS Code 未保存内容、Python 内存对象和 JSON 文件分别在哪里？
2. 为什么运行时 `append()` 的数据在退出后可能消失？
3. 什么叫持久化、序列化和反序列化？
4. JSON 的 `true`、`false`、`null` 读取到 Python 后是什么？
5. `"r"` 与 `"w"` 模式有什么区别？
6. 为什么 `"w"` 模式需要谨慎？
7. `with open()` 有什么作用？
8. `encoding="utf-8"` 有什么作用？
9. `ensure_ascii=False` 和 `indent=4` 分别影响什么？
10. `json.dump()` 与 `json.load()` 的方向分别是什么？
11. `load_papers` 与 `load_papers()` 有什么区别？
12. 为什么 `loaded_papers()` 会报列表不可调用？
13. 修改内存中的字段后，为什么还要调用保存函数？
14. `try` 和 `except` 分别负责什么？
15. 文件不存在时为什么返回 `[]`？
16. 为什么不建议使用裸 `except:`？
17. 如何安全测试 `FileNotFoundError` 分支？
18. 只输入 `python` 为什么出现 `>>>`，怎样退出？
19. 程序没有终端输出，是否一定代表失败？
20. 如何证明一次内存修改真正被持久化？

### 一句话复盘

今天把论文数据从 Python 内存保存到 JSON，再从 JSON 恢复成列表，并用精确的 `FileNotFoundError` 处理让程序在数据文件缺失时仍能安全返回空列表。
