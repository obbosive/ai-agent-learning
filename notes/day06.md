# Day 6 学习笔记：删除、统计、数据安全、自动测试与版本发布

> 学习日期：2026-08-07  
> 学习目标：为论文管理器补齐删除和统计功能，安全处理损坏的 JSON，编写可重复运行的自动测试，并发布本地 `v0.1.0` 版本  
> 完成文件：`day06/main.py`、`day06/paper_manager.py`、`day06/storage.py`、`day06/papers.json`、`day06/test_statistics.py`、`README.md`

## 一、今天完成了什么

Day 6 的重点从“继续增加功能”转向“让项目更加完整和可靠”。

今天完成：

- 根据完整标题删除论文；
- 删除前要求用户二次确认；
- 删除成功后持久化到 JSON；
- 统计论文总数、已读数、未读数和阅读完成率；
- 把统计计算和终端显示拆成两个函数；
- 处理空列表，避免除零错误；
- 捕获 `json.JSONDecodeError`；
- JSON 损坏时停止进入修改菜单，避免覆盖原数据；
- 使用 `assert` 编写四组统计测试；
- 验证统计函数不会修改输入数据；
- 创建项目 README 草稿；
- 创建注释标签 `v0.1.0`。

最终程序菜单：

```text
1. 查看论文
2. 添加论文
3. 标记论文为已读
4. 搜索论文
5. 删除论文
6. 查看统计
7. 退出程序
```

---

## 二、删除操作的数据流

删除功能的安全顺序是：

```text
输入标题
→ 检查空输入
→ 查找完全匹配的论文
→ 请求用户确认
→ 从内存列表删除字典
→ 保存整个列表到 JSON
→ 提示成功
```

空输入、找不到论文和用户取消时，都不应该修改列表或保存 JSON。

删除比查询风险更高，所以使用忽略大小写的完全匹配：

```python
title.lower() == paper["title"].lower()
```

不使用部分匹配：

```python
title.lower() in paper["title"].lower()
```

否则输入 `GPT` 可能直接删除 `MetaGPT`，不够安全。

---

## 三、列表、字典和字符串不能混淆

删除功能中涉及三个不同层次的对象：

```text
papers     → 列表，保存所有论文字典
paper      → 当前遍历到的一篇论文字典
title      → 用户输入的标题字符串
```

今天曾写成：

```python
papers["title"]
```

但 `papers` 是列表，列表索引需要整数，因而产生：

```text
TypeError: list indices must be integers or slices, not str
```

正确访问当前论文标题：

```python
paper["title"]
```

今天还曾写成：

```python
papers.remove(title)
```

但 `papers` 中保存的是字典，不是标题字符串。正确删除当前论文字典：

```python
papers.remove(paper)
```

对象关系：

```text
用户输入 title
    ↓ 与字段比较
paper["title"]

找到匹配后
    ↓ 从外层列表删除
papers.remove(paper)
```

---

## 四、遍历列表时删除元素

通常不建议一边遍历列表，一边删除其中的元素。删除后，后续元素会向前移动，继续循环可能漏掉元素。

当前代码找到第一篇匹配论文后：

```python
papers.remove(paper)
save_papers(papers)
return
```

删除后立即结束函数，不再继续遍历，因此“只删除第一篇完整匹配论文”的场景是安全的。

如果需求变成删除所有重复标题，便需要重新设计遍历策略，不能简单沿用当前写法。

---

## 五、确认、取消与持久化

确认输入：

```python
confirm = input("请输入 y 确认：").strip().lower()
```

`.strip()` 去除首尾空白，`.lower()` 让 `Y` 和 `y` 等价。

```python
if confirm != "y":
    print("已取消删除。")
    return
```

只有明确输入 `y` 才执行删除。

```python
papers.remove(paper)  # 修改内存
save_papers(papers)   # 持久化到磁盘
```

实际验证：

- 空标题：JSON 不变；
- 不存在标题：JSON 不变；
- `Reflection + n`：取消成功，JSON 不变；
- `HAHAHA + y`：忽略大小写找到 `hahaha` 并删除；
- 退出重启后仍不存在，证明删除已经持久化。

---

## 六、把计算与显示分开

统计功能没有全部写进一个函数，而是拆成：

```python
calculate_statistics(papers)
show_statistics(papers)
```

`calculate_statistics()`：

```text
接收论文列表
→ 计算统计数据
→ 返回字典
```

它不使用：

- `input()`；
- `print()`；
- `save_papers()`；
- 对输入数据的修改操作。

`show_statistics()`：

```text
调用计算函数
→ 接住返回字典
→ 格式化终端输出
```

这样拆分的好处是计算逻辑可以直接自动测试，不需要模拟用户输入或解析终端文字。

---

## 七、统计数据的计算顺序

统计函数的数据流：

```text
total_count = len(papers)
→ 遍历统计 read_count
→ not_read_count = total_count - read_count
→ 安全计算 read_rate
→ 返回统计字典
```

读取布尔值时可以直接判断：

```python
if paper["is_read"]:
    read_count += 1
```

不必写成：

```python
if paper["is_read"] == True:
```

后者可以运行，但前者更直接。

---

## 八、`len()`、运行时错误与拼写

今天曾把内置函数写成：

```python
lens(papers)
```

`lens` 是合法的标识符，所以语法检查可以通过；但程序真正执行时找不到这个名字，产生：

```text
NameError: name 'lens' is not defined
```

正确函数是：

```python
len(papers)
```

这说明：

```text
语法检查通过
不代表运行时使用的每个名字都存在
```

---

## 九、避免 `ZeroDivisionError`

阅读完成率：

```python
read_rate = read_count / total_count * 100
```

当列表为空时：

```text
read_count = 0
total_count = 0
```

执行 `0 / 0` 会产生：

```text
ZeroDivisionError
```

因此必须先判断：

```python
if total_count == 0:
    read_rate = 0
else:
    read_rate = read_count / total_count * 100
```

百分比格式：

```python
f"{read_rate:.1f}%"
```

`.1f` 表示把浮点数显示为一位小数。

---

## 十、统计函数的返回字典

函数返回：

```python
{
    "total_count": total_count,
    "read_count": read_count,
    "not_read_count": not_read_count,
    "read_rate": read_rate,
}
```

返回字典让多个有名称的结果能够一次返回。调用方通过键获取具体统计值。

当前数据验证结果：

```text
论文总数：4
已读数量：3
未读数量：1
阅读完成率：75.0%
```

---

## 十一、文件不存在与 JSON 损坏

文件不存在：

```python
except FileNotFoundError:
    print("没有找到论文数据文件，暂时使用空列表")
    return []
```

这可能是用户第一次运行程序，因此允许使用合法空列表进入菜单。

文件存在但格式损坏：

```python
except json.JSONDecodeError as error:
    print(f"论文数据格式损坏：{error}")
    return None
```

损坏表示原文件中可能仍有需要恢复的数据，不能伪装成正常空列表。

如果损坏时返回 `[]`，用户随后执行添加或删除，保存操作可能用新数据覆盖损坏文件，使原数据更难恢复。

---

## 十二、使用 `None` 作为明确的失败信号

当前 `load_papers()` 的返回约定：

```text
正常 JSON   → list
文件不存在  → []
JSON 损坏   → None
```

`main()` 在进入菜单前判断：

```python
loaded_papers = load_papers()

if loaded_papers is None:
    print("程序已停止，以避免覆盖已损坏的数据文件！")
    return
```

不能使用：

```python
if not loaded_papers:
```

因为 `[]` 和 `None` 的真值都是 `False`，但含义不同：

```text
[]   → 正常的空数据，可以操作
None → 加载失败，必须停止
```

---

## 十三、`== None` 与 `is None`

`==` 比较值是否相等，`is` 比较是否为同一个对象。

```python
[1, 2] == [1, 2]  # True，内容相同
```

`None` 是 Python 中唯一的特殊空值对象。规范判断方式是：

```python
value is None
value is not None
```

因此今天把：

```python
if loaded_papers == None:
```

调整为：

```python
if loaded_papers is None:
```

---

## 十四、自动测试的 Arrange、Act、Assert

一条测试通常分成：

```text
Arrange → 准备输入和预期结果
Act     → 调用被测试函数
Assert  → 比较实际结果与预期结果
```

示例：

```python
papers = []
expected = {
    "total_count": 0,
    "read_count": 0,
    "not_read_count": 0,
    "read_rate": 0,
}

result = calculate_statistics(papers)

assert result == expected
```

`assert` 条件为 `True` 时继续；条件为 `False` 时产生 `AssertionError`。

---

## 十五、四组独立统计测试

`test_statistics.py` 中测试：

1. 空列表：`0 / 0 / 0 / 0%`；
2. 一篇已读、一篇未读：`2 / 1 / 1 / 50%`；
3. 全部已读：`2 / 2 / 0 / 100%`；
4. 全部未读：`2 / 0 / 2 / 0%`。

测试不读取真实 `papers.json`，而是自己创建小型输入数据。这样测试：

- 不依赖用户当前数据；
- 可以重复运行；
- 不会污染真实文件；
- 失败原因更容易定位。

实际把错误预期总数设置为 `99` 后，测试成功产生 `AssertionError`，证明测试能够发现错误，而不是无条件打印通过。

---

## 十六、验证函数没有修改输入

统计函数除了返回正确结果，还应该保证输入列表不变。

如果写：

```python
backup = papers
```

这不是复制，只是让两个名字指向同一个列表：

```text
papers ──┐
         ├──> 同一个列表
backup ──┘
```

修改 `papers` 时，`backup` 也会看到变化，无法作为快照。

当前数据是“列表中放简单字典”，可以创建独立快照：

```python
original_papers = []

for paper in papers:
    original_papers.append(paper.copy())
```

然后在函数调用后检查：

```python
assert papers == original_papers
```

这里既创建了新列表，也复制了每个字典。对于更深层的嵌套结构，可以使用 `copy.deepcopy()`。

---

## 十七、测试辅助函数

为了避免每个测试重复调用和断言，抽取：

```python
def check_statistics(papers, expected):
    original_papers = []
    for paper in papers:
        original_papers.append(paper.copy())

    result = calculate_statistics(papers)

    assert result == expected
    assert papers == original_papers
```

每个测试只负责准备不同场景，再调用：

```python
check_statistics(papers, expected)
```

今天曾在后两组测试中漏传 `expected`，产生：

```text
TypeError: check_statistics() missing 1 required positional argument: 'expected'
```

同时，抽取辅助函数后，各测试中原来的 `calculate_statistics(papers)` 已经多余，应删除，避免同一函数重复执行。

---

## 十八、测试运行器与入口保护

当前没有引入 `pytest`，而是手动编写：

```python
def run_tests():
    test_empty_papers()
    print("通过：空列表")
    ...


if __name__ == "__main__":
    run_tests()
```

某个测试抛出异常后，后面的“通过”不会继续输出。因此运行器不会在失败时仍然宣称全部通过。

现阶段先掌握测试的本质，之后再学习 `pytest` 自动发现和运行测试。

---

## 十九、README 的实际作用

README 是仓库入口说明，不需要为了显得专业而堆积空话。最有用的内容是：

```text
项目是什么
当前能做什么
怎样运行
怎样运行测试
代码怎样组织
目前有哪些限制
```

Markdown标题中 `#` 后要有空格：

```markdown
# 项目标题
## 项目简介
```

当前 README 暂时保留为简短草稿，Day 7 推送 GitHub 前再按实际需要整理。

---

## 二十、Git标签与版本

Day 6 提交：

```text
1027456 添加删除数据和测试功能，还有readme文档
```

创建注释标签：

```powershell
git tag -a v0.1.0 -m "论文管理系统第一版"
```

版本含义：

```text
v       → version
0       → 仍在早期开发阶段
1       → 第一组可用功能
0       → 当前补丁版本
```

分支与标签：

```text
分支 → 随着新提交移动
标签 → 固定指向一个具体提交
```

当前：

```text
main、HEAD、v0.1.0 → 1027456
```

标签目前只存在于本地，Day 7 上传 GitHub 时再推送远程。

---

## 二十一、今天出现的问题与根因

### 1. `papers["title"]`

原因：把整个列表当成一篇论文字典使用。

### 2. `papers.remove(title)`

原因：列表元素是字典，却尝试删除字符串。

### 3. 删除后重启又出现

潜在原因：只修改内存，必须调用 `save_papers(papers)`。

### 4. `lens(papers)`

原因：内置函数 `len()` 拼写错误，属于运行时 `NameError`。

### 5. 空列表计算完成率

原因：没有在除法前处理 `total_count == 0`。

### 6. 损坏 JSON 返回空列表

风险：后续保存可能覆盖原数据。损坏时使用 `None` 明确表示加载失败。

### 7. 使用 `if not loaded_papers`

风险：无法区分正常空列表和加载失败，应使用 `is None`。

### 8. `backup = papers`

原因：只是创建别名，不是独立快照，无法检测副作用。

### 9. 辅助函数缺少 `expected`

原因：函数定义需要两个参数，调用时只传了一个。

### 10. 抽取辅助函数后仍重复计算

原因：职责移动后没有清理旧调用，造成无用的重复执行。

---

## 二十二、个人学习提醒

1. 写删除逻辑前先列出每个变量的类型。
2. 删除操作使用完整匹配和二次确认。
3. 修改内存后必须明确决定是否保存磁盘。
4. 遍历中删除后如果继续循环，要警惕元素位置变化。
5. 计算函数尽量只接收数据、返回结果，不处理输入输出。
6. 除法前考虑分母为零的边界情况。
7. 语法检查不能发现所有未定义名字。
8. 文件不存在和文件损坏不能采用相同处理策略。
9. `None` 使用 `is None` 判断。
10. 不要用真值判断混淆 `[]` 与 `None`。
11. 测试数据应独立于真实用户数据。
12. 测试不仅要验证返回值，也要关注副作用。
13. `backup = original` 通常只是别名，不是复制。
14. 抽取辅助函数后要删除原来的重复逻辑。
15. 测试必须做一次反向验证，确认错误时真的失败。
16. README以能理解、能运行、能验证为目标，不以字数为目标。
17. 标签固定版本，分支承载持续开发。

---

## 二十三、综合复习题

### 题目 1：安全删除库存商品

#### 背景

某库存程序的数据如下：

```python
products = [
    {"name": "Keyboard", "stock": 5},
    {"name": "Mouse", "stock": 12},
    {"name": "Monitor", "stock": 3},
]
```

需要实现 `delete_product(products)`。删除属于高风险操作，名称比较忽略大小写，但不允许部分匹配。

#### 任务

1. 输入商品名并去除首尾空白；
2. 空名称直接提示并结束；
3. 完整遍历查找商品；
4. 找到后显示真实商品名并要求输入 `y` 确认；
5. 用户取消时不能修改列表或调用保存；
6. 确认后删除正确的字典并调用 `save_products(products)`；
7. 找不到时只提示一次；
8. 解释为什么不能写 `products["name"]` 或 `products.remove(name)`。

#### 验收标准

- 输入 `mouse + n` 后数据不变；
- 输入 `MOUSE + y` 后只删除 Mouse；
- 输入 `Mou` 不会部分匹配并删除；
- 重启程序后删除结果仍然存在。

---

### 题目 2：设计可测试的订单统计函数

#### 背景

订单列表中的每个字典包含布尔字段 `"paid"`。需要统计订单总数、已付款数、未付款数和付款率。

#### 任务

1. 编写只计算并返回字典的 `calculate_order_statistics(orders)`；
2. 空列表付款率为 `0`，不能发生除零；
3. 编写独立显示函数，付款率显示一位小数；
4. 准备空列表、混合、全部付款、全部未付款四组测试；
5. 抽取测试辅助函数；
6. 辅助函数必须验证返回值和输入列表没有被修改；
7. 解释为什么 `backup = orders` 不能作为可靠快照。

#### 验收标准

- 四组结果正确；
- 测试不读取真实数据文件；
- 故意修改预期值时出现 `AssertionError`；
- 统计函数没有输入输出和保存副作用。

---

### 题目 3：安全加载应用配置

#### 背景

一个程序从 `config.json` 加载配置。首次运行时文件可能不存在；但文件也可能存在却因手动编辑而损坏。进入菜单后，用户可以保存配置。

#### 任务

1. 设计 `load_config()` 的异常处理；
2. 文件不存在时返回一个合法空字典 `{}`；
3. JSON 损坏时返回 `None` 并输出解析错误；
4. 主程序只在返回 `None` 时停止；
5. 解释为什么不能对两种情况都返回 `{}`；
6. 解释为什么主程序不能写 `if not config`；
7. 分别设计正常、缺失和损坏三条测试路径。

#### 验收标准

- 首次运行可以进入程序；
- 损坏文件不会被空配置覆盖；
- 空字典和加载失败得到不同处理；
- 使用 `is None` 判断失败信号。

---

### 题目 4：发布一个本地命令行工具版本

#### 背景

一个命令行工具已经完成核心功能、基础测试和 README。当前修改尚未提交，开发者希望创建本地早期版本 `v0.2.0`。

#### 任务

1. 写出提交前检查工作区和暂存区的命令；
2. 只暂存本次版本需要的源文件、测试和 README；
3. 创建提交后确认工作区干净；
4. 创建带说明的注释标签 `v0.2.0`；
5. 写出查看标签及其目标提交的命令；
6. 解释标签与分支的区别；
7. 说明本地创建标签后，远程 GitHub 是否会自动获得标签。

#### 验收标准

- 标签指向预期提交；
- 自动生成文件不进入版本；
- 标签不会随着后续提交自动移动；
- 明确远程推送将在后续单独执行。

---

## 二十四、参考思路

### 题目 1 参考思路

```python
def delete_product(products):
    name = input("请输入商品名：").strip()
    if not name:
        print("商品名不能为空。")
        return

    for product in products:
        if name.lower() == product["name"].lower():
            confirm = input(
                f"确认删除 {product['name']} 吗？输入 y 确认："
            ).strip().lower()

            if confirm != "y":
                print("已取消删除。")
                return

            products.remove(product)
            save_products(products)
            print("删除成功。")
            return

    print("没有找到该商品。")
```

`products` 是列表，字段属于当前字典 `product`；列表中保存的是字典，因此应删除 `product`，而不是输入字符串 `name`。

### 题目 2 参考思路

计算函数先获得总数和已付款数，未付款数使用相减得到；总数为零时付款率设为零。测试辅助函数先逐个复制订单字典，调用计算函数后分别断言返回结果和原列表。

```python
def check_statistics(orders, expected):
    original_orders = []
    for order in orders:
        original_orders.append(order.copy())

    result = calculate_order_statistics(orders)

    assert result == expected
    assert orders == original_orders
```

`backup = orders` 只会让两个名字指向同一列表，无法检测原列表被修改。

### 题目 3 参考思路

```python
def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as error:
        print(f"配置文件损坏：{error}")
        return None
```

主流程：

```python
config = load_config()
if config is None:
    print("程序停止，以避免覆盖损坏配置。")
    return
```

`{}` 是合法空配置且真值为假；因此不能使用 `if not config` 判断加载失败。

### 题目 4 参考思路

```powershell
git status
git diff
git add <源文件> <测试文件> README.md
git diff --staged
git commit -m "release: prepare v0.2.0"
git status
git tag -a v0.2.0 -m "second early release"
git tag -n
git show v0.2.0 --no-patch
```

分支通常随着新提交移动，标签固定指向创建时的提交。标签创建在本地不会自动出现在 GitHub，需要后续显式推送。

---

### 一句话复盘

今天补齐了删除和统计功能，用 `None` 区分损坏数据与合法空数据，通过独立快照和 `assert` 验证统计结果与副作用，并用 README、提交和 `v0.1.0` 标签形成了第一个可识别版本。
