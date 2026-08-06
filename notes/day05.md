# Day 5 学习笔记：搜索、模块拆分、程序入口与 Git 分支

> 学习日期：2026-08-06  
> 学习目标：为论文管理器增加搜索功能，把单文件程序拆成多个模块，理解 Python 的导入和程序入口，并完成一次 Git 功能分支开发与合并  
> 完成文件：`day05/main.py`、`day05/paper_manager.py`、`day05/storage.py`、`day05/papers.json`

## 一、今天完成了什么

今天在 Day 4 交互式论文管理器的基础上完成了四项升级：

1. 增加不区分英文大小写的标题关键词搜索；
2. 按职责把单个 Python 文件拆成三个模块；
3. 使用 `main()` 和 `if __name__ == "__main__":` 区分直接运行与模块导入；
4. 使用 Git 功能分支完成“显示搜索结果数量”，再合并回 `main`。

最终结构：

```text
day05/
├── main.py           # 菜单、程序启动流程
├── paper_manager.py  # 查看、添加、标记和搜索
├── storage.py        # JSON 读取和保存
└── papers.json       # 持久化数据
```

依赖关系：

```text
main.py
├── 从 storage 导入 load_papers
└── 从 paper_manager 导入业务函数

paper_manager.py
└── 从 storage 导入 save_papers

storage.py
└── 只依赖 Python 标准库 json
```

---

## 二、标题关键词搜索

完全相等与包含关系不同：

```python
"Gen" == "AutoGen"  # False
"Gen" in "AutoGen"  # True
```

搜索功能需要查找标题中是否包含关键词，因此使用：

```python
keyword in paper["title"]
```

`in` 左边是要寻找的较小字符串，右边是被搜索的完整字符串，方向不能颠倒。

---

## 三、不区分英文大小写

Python字符串比较默认区分大小写：

```python
"gen" in "AutoGen"  # False
```

为了让 `gen`、`Gen` 和 `GEN` 都能找到 `AutoGen`，比较前统一转换成小写：

```python
keyword.lower() in paper["title"].lower()
```

`lower()` 返回新的小写字符串，不会直接修改原字符串或 JSON 中保存的标题。

---

## 四、空字符串的真值

用户直接回车时：

```python
keyword = input(...).strip()
```

结果是空字符串 `""`，不是 `None`。

```text
""    → 存在一个字符串对象，只是没有字符
None  → 没有具体值
```

Python进行条件判断时，会先取得对象的真值：

```python
bool("")      # False
bool("gen")   # True
```

因此：

```python
if not keyword:
    print("搜索词不能为空！")
    return
```

可以拆解为：

```text
keyword 是 ""
→ bool(keyword) 是 False
→ not False 是 True
→ 进入 if
→ return 结束本次搜索
```

在当前场景中，它近似等价于：

```python
if keyword == "":
```

但要注意，`if not value` 也会把 `0`、`[]`、`None` 等对象判断为假。如果数字 `0` 是合法输入，就不能不加分析地使用这种写法。

---

## 五、为什么空关键词会匹配所有标题

Python规定空字符串存在于任何字符串中：

```python
"" in "AutoGen"  # True
"" in "ReAct"    # True
```

如果不提前拦截空关键词，下面的条件会对所有论文成立：

```python
if keyword.lower() in paper["title"].lower():
```

因此空输入校验必须发生在遍历之前。

---

## 六、收集搜索结果并复用函数

搜索功能先创建一个空列表：

```python
matched_list = []
```

匹配时把论文字典加入结果列表：

```python
for paper in papers:
    if keyword.lower() in paper["title"].lower():
        matched_list.append(paper)
```

遍历结束后，根据结果列表是否为空决定输出：

```python
if matched_list:
    print(f"共找到{len(matched_list)}篇匹配论文")
    show_papers(matched_list)
else:
    print("没有找到匹配的论文！")
```

这里复用 `show_papers()`，避免再次编写已读状态转换和输出格式。

`len(matched_list)` 返回结果列表中的元素数量。

搜索属于查询操作，不修改论文，因此不能调用 `save_papers()`。实际测试确认搜索前后 JSON 哈希保持不变。

---

## 七、为什么要拆分模块

原文件同时负责：

```text
JSON 文件读写
论文业务功能
菜单交互和启动流程
```

随着功能增加，一个文件会越来越长。模块拆分的目标是让每个文件只承担相对集中的职责。

这种思想与 C#/Unity 项目按职责拆分类和脚本相通，但 Python允许函数直接定义在模块顶层，不要求所有函数都放进类中。

模块拆分属于重构：

```text
代码组织方式改变
程序对外行为不应该改变
```

因此拆分后必须重新测试正常路径和异常路径。

---

## 八、Python模块和导入

一个普通 `.py` 文件就可以作为 Python 模块。

```python
from storage import load_papers, save_papers
```

大致含义是：

```text
找到 storage.py
→ 创建 storage 模块对象
→ 执行 storage.py 的顶层代码
→ 从模块命名空间中取得两个函数
→ 在当前模块中绑定这两个名字
```

每个模块有自己的全局命名空间。`show_menu()` 定义在 `paper_manager.py` 中时，不会自动出现在 `main.py` 中；必须移动到 `main.py` 或显式导入。

今天曾因此出现：

```text
NameError: name 'show_menu' is not defined
```

---

## 九、导入模块时“从上到下执行”是什么意思

导入模块时，Python会执行模块的顶层语句，但不等于自动调用其中所有函数。

例如：

```python
print("A")


def hello():
    print("B")


print("C")
```

导入该模块时会输出：

```text
A
C
```

执行 `def hello():` 时只是创建函数并绑定名字，不会进入函数体，所以 `B` 不会输出。只有调用：

```python
hello()
```

函数体才会执行。

如果模块顶层直接存在 `print()`、赋值、函数调用或 `while` 循环，导入时它们会立即执行。

---

## 十、`main()` 不是特殊语法

```python
def main():
    ...
```

`main` 只是社区常用的函数名。Python不会自动寻找或调用它。改成下面这样也可以：

```python
def start_program():
    ...
```

真正启动函数的是显式调用：

```python
main()
```

把启动流程集中进 `main()` 的好处：

- 菜单流程集中，入口清楚；
- `loaded_papers` 成为局部变量；
- 导入模块时可以只获得函数，不启动交互；
- 后续测试或其他代码可以主动调用入口函数。

---

## 十一、`__name__` 和入口保护

Python执行模块时会自动提供：

```python
__name__
```

同一个文件有两种使用方式：

```text
直接运行 main.py → __name__ 的值是 "__main__"
通过 import main  → __name__ 的值是 "main"
```

因此入口保护写成：

```python
if __name__ == "__main__":
    main()
```

含义是：

```text
如果当前文件由用户直接启动
→ 调用 main() 并显示菜单

如果当前文件只是被其他模块导入
→ 不调用 main()，只提供其中定义的函数
```

真正特殊的是 `__name__` 和字符串 `"__main__"`，不是函数名 `main`。

实际验证：

- `python day05/main.py`：菜单正常启动；
- `import main`：模块成功导入，菜单没有启动；
- `import paper_manager`：业务函数可以取得，也没有启动菜单。

---

## 十二、重构时遗漏返回值

把读取函数移动到 `storage.py` 时，异常分支曾漏掉：

```python
return []
```

如果 Python函数执行到末尾没有遇到 `return`，会自动返回 `None`。

这会造成返回类型不稳定：

```text
文件存在   → 返回 list
文件不存在 → 返回 None
```

后续调用：

```python
papers.append(...)
```

可能产生：

```text
AttributeError: 'NoneType' object has no attribute 'append'
```

修复后实际临时隐藏 `papers.json` 进行测试，`load_papers()` 正确返回 `list []`，随后又恢复了数据文件。

这说明重构后不能只测试最常见的正常路径，还要重新执行异常路径。

---

## 十三、Git分支、HEAD与提交指针

当前阶段可以把分支理解成指向某个提交的可移动标签。

创建功能分支前：

```text
8ecae0e
   ↑
 main、HEAD
```

执行：

```powershell
git switch -c feature/search-count
```

创建并切换后：

```text
8ecae0e
   ↑
 main、feature/search-count、HEAD
```

新建分支不会复制一套项目文件。两个分支最初只是指向同一个提交。

在功能分支创建新提交后：

```text
8ecae0e ── 8e03ae6
   ↑           ↑
 main     feature/search-count、HEAD
```

`main` 保持不动，功能分支向前移动。

---

## 十四、切换分支为什么会改变代码

执行：

```powershell
git switch main
```

`HEAD` 改为指向 `main`。Git会根据 `main` 指向的提交快照更新工作区，因此“显示搜索结果数量”的代码会暂时消失。

代码没有丢失，它仍保存在功能分支的提交中。

切换分支前通常要求工作区干净，是为了防止未提交修改与目标分支内容冲突。

---

## 十五、Fast-forward合并

切回 `main` 后执行：

```powershell
git merge feature/search-count
```

因为 `main` 没有产生新的分叉提交，只需把 `main` 指针向前移动，所以 Git完成 Fast-forward：

```text
合并前：

8ecae0e ── 8e03ae6
   ↑           ↑
 main        feature

合并后：

8ecae0e ── 8e03ae6
               ↑
       main、feature、HEAD
```

Fast-forward通常不会额外创建合并提交，因为现有历史本身已经是一条直线。

实际合并后：

```text
main                 8e03ae6
feature/search-count 8e03ae6
```

搜索数量重新出现在 `main` 中，工作区保持干净。

---

## 十六、删除已合并的功能分支

合并完成后，功能分支标签通常可以删除：

```powershell
git branch -d feature/search-count
```

小写 `-d` 会检查该分支是否已经合并；未合并时通常拒绝删除，因此比强制删除更安全。

删除分支只删除分支标签，不会删除已经进入 `main` 的提交和代码，因为 `main` 仍然指向 `8e03ae6`。

不应在没有确认的情况下使用大写 `-D` 强制删除未合并分支。

---

## 十七、今天出现的问题与根因

### 1. 空搜索显示全部论文

原因：错误判断 `keyword == None`。空输入实际是 `""`，而空字符串又存在于所有字符串中。

### 2. 菜单文字与分支不一致

原因：增加搜索选项后更新了控制流，却没有同步更新用户看到的菜单文字。

### 3. 模块移动后缺少 `return []`

原因：重构搬运代码时遗漏了异常分支的返回值，导致文件缺失时可能返回 `None`。

### 4. 拆分后存在无用导入

原因：JSON读写移入 `storage.py` 后，原模块仍保留 `import json` 或不再使用的 `load_papers`。

### 5. `show_menu` 未定义

原因：函数仍位于 `paper_manager.py`，但 `main.py` 没有导入；模块之间的名字不会自动共享。

### 6. 误以为 `main` 是Python规定的入口

原因：把 C# 中的入口经验直接套用到 Python。Python从第一行执行，`main()` 只是主动组织启动流程的普通函数。

---

## 十八、个人学习提醒

1. 输入为空时先确认得到的是 `""`、`None` 还是其他类型。
2. `if not value` 使用的是真值规则，不只是空字符串专用语法。
3. 部分搜索使用 `keyword in full_text`，注意方向。
4. 查询功能不应保存或修改数据。
5. 已有函数可以复用时，不要重复编写输出逻辑。
6. 每个模块只导入自己实际使用的名字。
7. 模块中的名字不会自动出现在其他模块中，必须移动或导入。
8. 导入会执行顶层代码，但 `def` 只创建函数，不执行函数体。
9. `main` 是普通函数；入口保护依赖的是 `__name__`。
10. 重构后要重新测试正常路径和异常路径。
11. 创建分支不会复制文件夹，只会创建新的提交指针。
12. 切换分支前尽量保持工作区干净。
13. 功能分支提交后，`main` 不会自动获得该提交。
14. Fast-forward本质上是主分支指针向前移动。
15. 删除已合并分支只删除标签，不删除已合并代码。

---

## 十九、综合复习题

### 题目 1：实现独立的商品关键词搜索

#### 背景

某库存程序使用以下数据：

```python
products = [
    {"name": "Mechanical Keyboard", "price": 399},
    {"name": "Wireless Mouse", "price": 159},
    {"name": "USB Keyboard", "price": 129},
]
```

#### 任务

编写 `search_products(products)`：

1. 输入关键词并删除首尾空白；
2. 空关键词要提示并结束本次搜索；
3. 搜索不区分英文大小写；
4. 支持部分匹配；
5. 显示匹配数量以及每个商品的名称和价格；
6. 没有匹配结果时只提示一次；
7. 搜索不得修改原列表。

#### 验收标准

- 输入 `KEYBOARD` 能找到两件商品；
- 输入空白不会显示全部商品；
- 输入 `screen` 提示没有结果；
- 函数执行前后 `products` 内容相同。

---

### 题目 2：为命令行项目设计模块结构

#### 背景

一个待办程序目前把下面内容全部写在 `app.py` 中：

- JSON加载和保存；
- 添加、查看、完成任务；
- 用户菜单和无限循环；
- 程序启动代码。

#### 任务

1. 把程序设计成 `storage.py`、`task_manager.py` 和 `main.py` 三个模块；
2. 写出每个模块应该包含的函数；
3. 画出模块之间的导入方向；
4. 说明为什么 `storage.py` 不应反过来导入菜单模块；
5. 写出启动程序的命令。

#### 验收标准

- 数据、业务和入口职责分开；
- 不出现循环导入；
- `main.py` 可以组装所有功能；
- 其他文件导入业务函数时不会启动菜单。

---

### 题目 3：预测直接运行与导入的输出

#### 背景

文件 `tool.py`：

```python
print("加载 tool")


def main():
    print("执行 main")


if __name__ == "__main__":
    main()
```

文件 `app.py`：

```python
print("导入前")
import tool
print("导入后")
tool.main()
```

#### 任务

1. 分别预测执行 `python tool.py` 和 `python app.py` 的完整输出顺序；
2. 说明两种情况下 `tool.py` 内部的 `__name__` 分别是什么；
3. 解释为什么导入时会输出“加载 tool”，但不会由入口保护自动输出“执行 main”；
4. 如果删除入口保护，只在文件末尾写 `main()`，预测 `python app.py` 的输出变化。

#### 验收标准

- 区分顶层代码执行与函数体调用；
- 明白 `main` 只是普通函数；
- 能解释入口保护如何避免导入副作用。

---

### 题目 4：设计一次安全的功能分支开发

#### 背景

一个Git仓库当前只有 `main` 分支，最新提交为 `A`。开发者要增加“导出报表”功能，希望在功能完成前不影响 `main`。功能分支产生提交 `B`，期间 `main` 没有新提交。

#### 任务

1. 写出创建并切换到 `feature/export-report` 的命令；
2. 写出修改完成后的检查、暂存和提交命令；
3. 画出提交后 `main`、功能分支和 `HEAD` 的位置；
4. 写出切回 `main` 并合并的命令；
5. 判断此次合并是否可以 Fast-forward，并解释原因；
6. 写出安全删除已合并功能分支的命令；
7. 解释删除分支后提交 `B` 为什么仍然存在。

#### 验收标准

- 功能开发发生在独立分支；
- 合并方向是把功能分支合入 `main`；
- 能区分删除分支标签与删除提交；
- 不使用强制删除掩盖未合并工作。

---

## 二十、参考思路

### 题目 1 参考思路

```python
def search_products(products):
    keyword = input("请输入商品关键词：").strip()
    if not keyword:
        print("关键词不能为空。")
        return

    matched_products = []
    for product in products:
        if keyword.lower() in product["name"].lower():
            matched_products.append(product)

    if not matched_products:
        print("没有匹配商品。")
        return

    print(f"共找到 {len(matched_products)} 件商品：")
    for product in matched_products:
        print(f"{product['name']} | {product['price']}元")
```

该函数只建立新的结果列表并读取原字典，没有修改字段或保存数据。

### 题目 2 参考思路

```text
main.py
├── 导入 storage.load_tasks
└── 导入 task_manager 中的业务函数

task_manager.py
└── 导入 storage.save_tasks

storage.py
└── 导入标准库 json
```

`storage.py` 只负责数据，不应依赖用户菜单，否则底层模块会反向依赖上层界面，容易形成循环导入。可以从项目根目录执行 `python .\todo\main.py`，具体路径取决于项目结构。

### 题目 3 参考思路

执行 `python tool.py`：

```text
加载 tool
执行 main
```

此时 `tool.py` 的 `__name__` 是 `"__main__"`。

执行 `python app.py`：

```text
导入前
加载 tool
导入后
执行 main
```

导入时 `tool.py` 的 `__name__` 是 `"tool"`，入口条件不成立；最后的 `tool.main()` 是显式调用。如果删除入口保护并直接写 `main()`，导入阶段会先执行一次，`app.py` 最后又显式调用一次，因此“执行 main”会出现两次。

### 题目 4 参考思路

```powershell
git switch -c feature/export-report
git diff
git add <本次功能文件>
git diff --staged
git commit -m "feat: add report export"
git switch main
git merge feature/export-report
git branch -d feature/export-report
```

提交后历史：

```text
A ── B
↑    ↑
main feature、HEAD
```

因为 `main` 从 `A` 开始没有产生其他提交，`B` 是 `A` 的直接后代，可以 Fast-forward。合并后 `main` 指向 `B`。删除功能分支只是删除另一个指向 `B` 的标签，`main` 仍然引用 `B`，所以提交和代码继续存在。

---

### 一句话复盘

今天为程序增加了大小写无关的关键词搜索，把数据、业务和入口拆成独立模块，理解了 Python 导入时执行顶层代码以及 `__name__` 入口保护的作用，并使用 Git 功能分支完成开发、提交、切换和 Fast-forward 合并。
