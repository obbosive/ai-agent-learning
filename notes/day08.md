# Day 8 学习笔记：Python 虚拟环境与依赖管理

## 一、今日完成情况

Day 8 解决的是一个真实项目必须面对的问题：同一台电脑上的不同 Python 项目，怎样各自使用合适的第三方库，并让别人能够重建相同的运行环境。

今天已经完成：

- 在项目根目录创建正式虚拟环境 `.venv`；
- 理解“激活虚拟环境”本质上是在修改当前终端的 `PATH`；
- 使用虚拟环境自己的 Python 和 pip 安装 `requests`；
- 使用 `requirements.txt` 记录依赖及精确版本；
- 创建临时环境 `.venv-rebuild`，验证依赖可以从零重建；
- 删除验证用的临时环境，只保留正式环境；
- 使用 `.gitignore` 排除虚拟环境和 Python 缓存；
- 让 VS Code 选择 `.venv\Scripts\python.exe`；
- 编写 `environment_check.py`，从程序内部检查解释器和库的真实位置；
- 使用 `pip check` 确认依赖关系完整且没有冲突。

当前项目的重要结构如下：

```text
ai-agent-learning/
├── .venv/                    # 本机正式虚拟环境，不提交到 Git
├── day08/
│   └── environment_check.py  # 环境检查程序
├── notes/
├── .gitignore
└── requirements.txt          # 需要提交的依赖清单
```

## 二、为什么需要虚拟环境

如果所有项目都把第三方库安装到全局 Python 中，容易出现版本冲突。例如：

```text
项目 A 需要某个库 1.x
项目 B 需要同一个库 2.x
```

全局环境通常只能保留一个实际安装版本，升级项目 B 的依赖可能破坏项目 A。虚拟环境的解决办法是为每个项目准备独立的解释器入口和第三方库目录：

```text
全局 Python
├── 项目 A/.venv/Lib/site-packages/
└── 项目 B/.venv/Lib/site-packages/
```

每个 `.venv` 都有自己的：

- `python.exe`；
- `pip`；
- `Lib\site-packages`；
- PowerShell 激活脚本。

虚拟环境不是虚拟机，也不是另一台电脑。它不会复制整个 Windows，只隔离某个 Python 项目的解释器入口和第三方包。

## 三、创建虚拟环境的命令与含义

在项目根目录执行：

```powershell
python -m venv .venv
```

逐段解释：

- `python`：启动当前能够找到的 Python 解释器；
- `-m`：让 Python 按模块运行后面的名字；
- `venv`：Python 标准库中负责创建虚拟环境的模块；
- `.venv`：新环境的目标目录名称，可以换名字，但这是常见约定。

这里的点只是目录名的一部分。在 Windows 里，以点开头的目录不具有 Linux 中完全相同的隐藏机制，但这种命名能清楚表示它是项目工具目录。

创建虚拟环境时，会以创建者为基础生成独立环境。因此，虚拟环境通常还隐含依赖某个 Python 大版本。当前项目使用的是 Python 3.12.10。

## 四、激活虚拟环境到底做了什么

PowerShell 中的激活命令是：

```powershell
.\.venv\Scripts\Activate.ps1
```

激活后，终端提示符通常变成：

```text
(.venv) PS C:\...\ai-agent-learning>
```

激活不是进入 `.venv` 文件夹，也不是启动一台虚拟电脑。它主要修改当前 PowerShell 进程的环境变量，把：

```text
项目\.venv\Scripts
```

临时放到 `PATH` 前面。于是输入：

```powershell
python
```

PowerShell 会优先找到：

```text
.venv\Scripts\python.exe
```

这个修改只影响当前终端及其子进程。关闭终端后，激活状态自然消失，不会永久替换电脑的全局 Python。

退出激活状态可以执行：

```powershell
deactivate
```

### 激活不是使用虚拟环境的必要条件

即使没有激活，也可以明确指定解释器：

```powershell
.\.venv\Scripts\python.exe .\day08\environment_check.py
```

或者明确使用它的 pip：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

此时命令已经写明使用哪个 `python.exe`，不需要再依赖 `PATH` 帮忙查找。可以这样理解：

```text
激活后输入 python       → 通过 PATH 查找，优先找到 .venv
写出解释器的完整路径    → 直接运行指定文件，不需要查找
```

## 五、PowerShell 执行策略

最初运行 `Activate.ps1` 时，PowerShell 因执行策略阻止脚本。当前用户范围已经设置为：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

关键含义：

- `CurrentUser`：只修改当前 Windows 用户的配置，不是整台电脑所有用户；
- `RemoteSigned`：本地创建的脚本可以运行，从互联网下载且带有网络来源标记的脚本通常需要签名或解除阻止。

这是一种常见的个人开发环境配置。它解决了每次激活虚拟环境都临时放行的麻烦，但不表示以后可以不检查来历就运行陌生脚本。

## 六、为什么推荐 `python -m pip`

安装依赖时使用：

```powershell
python -m pip install requests
```

而不是只写：

```powershell
pip install requests
```

原因是电脑可能同时存在多个 Python 和多个 pip。单独输入 `pip` 时，终端需要从 `PATH` 中寻找一个 `pip.exe`，它不一定属于想要使用的解释器。

`python -m pip` 的数据流更明确：

```text
先确定 python
    ↓
让这个 python 运行它对应的 pip
    ↓
依赖安装到这个 python 所属的环境
```

其中：

- `install`：执行安装操作；
- `requests`：要安装的包名；
- `-r requirements.txt`：从指定文件逐行读取安装要求。

## 七、直接依赖与间接依赖

项目代码直接导入的是：

```python
import requests
```

因此 `requests` 是项目的直接依赖。但 `requests` 内部还依赖其他包，所以最终环境中包含：

```text
requests==2.34.2
├── certifi==2026.7.22
├── charset-normalizer==3.4.9
├── idna==3.18
└── urllib3==2.7.0
```

后面四个是当前项目的间接依赖，也叫传递依赖。安装 `requests` 时，pip 会读取它声明的依赖关系并自动安装这些包。

## 八、`pip freeze`、`requirements.txt` 与重建环境

查看当前环境中已安装的包及精确版本：

```powershell
python -m pip freeze
```

生成依赖文件：

```powershell
python -m pip freeze > requirements.txt
```

前半部分由 Python 和 pip 产生文本；`>` 是 PowerShell 的输出重定向符号，它会把文本写入右侧文件，并覆盖该文件原来的内容。因此执行前应确认当前虚拟环境和目标文件都正确。

当前 `requirements.txt` 是：

```text
certifi==2026.7.22
charset-normalizer==3.4.9
idna==3.18
requests==2.34.2
urllib3==2.7.0
```

双等号表示固定精确版本。例如：

```text
requests==2.34.2
```

表示安装 2.34.2，而不是自动选择未来的其他版本。这有助于减少“在我的电脑上正常，在你的电脑上出错”的情况。

重建时使用：

```powershell
python -m pip install -r requirements.txt
```

完整逻辑是：

```text
requirements.txt 提供包名与版本
                 ↓
pip 从软件源下载对应安装包
                 ↓
安装到当前 python 所属的 site-packages
```

### 为什么不上传 `.venv`

`.venv` 体积大，包含大量可重新下载的文件，而且其中某些路径和可执行文件与创建它的电脑、操作系统及 Python 安装位置有关。把它提交到 Git 不可靠，也会让仓库臃肿。

正确做法是：

```text
提交代码 + requirements.txt
忽略 .venv
在每台电脑上重新创建 .venv 并安装依赖
```

## 九、从零重建环境的标准流程

拿到一个使用 `requirements.txt` 的 Python 项目后，典型流程是：

```powershell
git clone <仓库地址>
cd <项目目录>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python <程序入口文件>
```

每一步分别负责：

1. `git clone`：下载代码和 Git 历史；
2. `cd`：让当前目录切换到项目根目录；
3. `python -m venv .venv`：在本机创建新环境；
4. `Activate.ps1`：让当前终端默认使用新环境；
5. `pip install -r`：按照依赖文件下载并安装第三方库；
6. 最后一条命令才真正运行项目。

今天使用 `.venv-rebuild` 做过一次完整验证。即使没有激活临时环境，下面的命令仍然成功：

```powershell
.\.venv-rebuild\Scripts\python.exe -m pip install -r requirements.txt
```

原因是它明确指定了临时环境里的解释器。`requirements.txt` 没写目录也能被找到，则是因为执行命令时当前目录正是项目根目录；相对路径从当前目录开始解析。

## 十、`requirements.txt` 能做什么，不能做什么

`requirements.txt` 主要记录 Python 第三方包，不能完整描述整台电脑。它通常没有自动记录：

- 应该安装哪个 Python 大版本；
- Windows、Linux 等操作系统差异；
- Git、数据库或其他系统软件；
- 环境变量；
- API Key、账号密码等秘密信息；
- 项目的启动命令和数据准备方法。

因此，一个成熟开源项目通常还需要 README、项目配置文件、示例环境变量文件等说明。`requirements.txt` 是可复现环境的重要部分，但不是全部。

## 十一、`pip freeze`、`pip check` 和 `pip install -r`

三个命令回答不同问题：

| 命令 | 作用 |
|---|---|
| `python -m pip freeze` | 列出当前环境里已经安装的包和精确版本 |
| `python -m pip check` | 检查已安装包是否缺少依赖或版本不兼容 |
| `python -m pip install -r requirements.txt` | 按文件内容安装或补齐依赖 |

本项目执行 `pip check` 的结果为：

```text
No broken requirements found.
```

这表示 pip 当前没有发现依赖缺失或版本冲突。它只能检查包所声明的依赖关系，不能代替项目自己的功能测试。

## 十二、VS Code 中的解释器选择

VS Code 不是 Python 解释器。Python 扩展仍需知道当前项目应该使用哪个 `python.exe`。

选择方式：

```text
Ctrl + Shift + P
→ Python: 选择解释器
→ .venv\Scripts\python.exe
```

选择后，VS Code 的运行按钮、代码补全、导入检查、调试器和新建 Python 终端会尽量统一使用该环境。

需要区分：

- 选择解释器：告诉 VS Code 的 Python 扩展使用哪个环境；
- 激活环境：调整某一个终端的 `PATH`；
- 明确写出解释器路径：某一条命令直接指定环境。

新建终端时出现 `(.venv)`，并且运行检查程序显示解释器来自 `.venv`，说明 VS Code 与项目环境已经统一。

## 十三、从程序内部验证真实环境

`day08/environment_check.py` 使用：

```python
import sys

import requests


def show_environment():
    print(f"解释器位于{sys.executable}")
    print(f"是否处于虚拟环境：{sys.prefix != sys.base_prefix}")
    print(f"requests版本：{requests.__version__}")
    print(f"requests位置：{requests.__file__}")


if __name__ == "__main__":
    show_environment()
```

关键属性：

- `sys.executable`：正在执行当前程序的 Python 可执行文件；
- `sys.prefix`：当前解释器环境的目录；
- `sys.base_prefix`：创建虚拟环境所依据的基础 Python 目录；
- `requests.__version__`：实际导入的 requests 版本；
- `requests.__file__`：实际导入文件在硬盘上的位置。

在虚拟环境中运行得到：

```text
解释器位于...\.venv\Scripts\python.exe
是否处于虚拟环境：True
requests版本：2.34.2
requests位置：...\.venv\Lib\site-packages\requests\__init__.py
```

全局 Python 没有安装 `requests`，所以用全局解释器运行时会在：

```python
import requests
```

处产生 `ModuleNotFoundError`。这是依赖隔离生效的证据，不是项目虚拟环境损坏。

Python 从上到下执行文件。第二行导入失败后，程序立即停止，因此后面的函数定义、入口保护和函数调用都还没有执行。

## 十四、`.gitignore` 与当前 Git 状态

当前 `.gitignore` 包含：

```gitignore
__pycache__/
*.py[cod]
.venv/
```

分别忽略：

- Python 自动生成的缓存目录；
- `.pyc`、`.pyo`、`.pyd` 等编译或平台相关文件；
- 本机虚拟环境。

需要提交的是：

- `.gitignore`；
- `requirements.txt`；
- `day08/environment_check.py`；
- Day 8 学习笔记。

不需要提交的是 `.venv`。`.gitignore` 只决定 Git 是否跟踪文件，不会禁止 Python 和 VS Code 使用这些文件。

## 十五、个人复盘与注意事项

1. 今天最初容易把“激活”理解成进入一个特殊空间。更准确的模型是：它只改变当前终端查找命令的优先顺序。
2. 以后看到命令时，先找出三个信息：由哪个解释器执行、操作哪个环境、相对路径从哪里开始。这样就不会只是在机械复制命令。
3. `.venv`、`.venv-rebuild` 的拼写要注意。它们只是我们取的目录名，拼错后不会自动对应到另一个目录。
4. 终端提示符有 `(.venv)` 是有用线索，但最可靠的证据仍是 `sys.executable`。提示符属于界面显示，真实解释器路径属于程序运行事实。
5. 安装包时优先使用 `python -m pip`。这样可以把 Python 和 pip 明确绑定，减少多环境下装错位置的问题。
6. 当前目录会影响 `requirements.txt`、脚本文件等相对路径的解析。执行命令前应观察 PowerShell 提示符中的目录。
7. 虚拟环境可以删除和重建，所以不要在 `.venv` 中保存自己编写的业务代码或重要数据。
8. 运行 GitHub 项目时，不能看到 `requirements.txt` 就立刻盲目安装。还应先阅读 README，确认 Python 版本、启动方式、系统依赖和环境变量要求。

## 十六、独立综合复习题

### 题目 1：两个项目的依赖冲突

背景：一台电脑上有 `project_a` 和 `project_b`。二者都使用 Python 3.12，但 A 需要 `example-lib==1.8.0`，B 需要 `example-lib==2.4.0`。全局安装会造成冲突。

任务：为两个项目分别设计虚拟环境和依赖文件，并写出首次创建、安装以及以后重新进入项目时使用的 PowerShell 命令。

验收标准：

- 两个项目使用不同的 `.venv` 目录；
- 安装命令明确绑定正确的 Python 与 pip；
- 两个 `requirements.txt` 固定各自所需版本；
- 解释清楚关闭终端后什么会消失、什么仍保存在硬盘上。

### 题目 2：诊断“明明安装了却无法导入”

背景：开发者执行 `pip install requests` 后看到安装成功，但运行程序仍然报 `ModuleNotFoundError: No module named 'requests'`。电脑上同时有全局 Python 和项目 `.venv`。

任务：给出一套只读诊断方案，确定“安装时使用的 pip”和“运行时使用的 Python”是否属于同一个环境，并说明可能的修复方法。

验收标准：

- 至少检查运行解释器的真实路径；
- 至少检查 requests 的安装位置或当前环境的包列表；
- 能解释为什么只看到“安装成功”并不足以证明程序可以导入；
- 修复方案不会把所有依赖随意安装到全局 Python。

### 题目 3：交付一个可重建的命令行项目

背景：你要把一个使用 `requests` 的天气查询程序交给同学。仓库不能包含自己的虚拟环境，也不能包含 API Key。

任务：设计仓库中应该提交和忽略的文件，并写出同学从 clone 到运行程序的完整流程。

验收标准：

- `.venv` 和真实密钥不会进入 Git；
- 仓库包含依赖清单和必要的运行说明；
- 重建步骤明确区分创建环境、激活环境、安装依赖和运行程序；
- 能说明为什么只有 `requirements.txt` 仍不足以保存 API Key 和 Python 版本要求。

### 题目 4：分析一组环境检查结果

背景：某项目终端提示符显示 `(.venv)`，但程序输出如下：

```text
sys.executable = C:\Python312\python.exe
sys.prefix = C:\Python312
sys.base_prefix = C:\Python312
requests.__file__ = C:\Python312\Lib\site-packages\requests\__init__.py
```

任务：判断程序是否真正使用虚拟环境，解释每一项证据，并给出一种可靠的运行方式。

验收标准：

- 不能只根据提示符 `(.venv)` 下结论；
- 正确判断 `sys.prefix == sys.base_prefix` 的含义；
- 指出 requests 实际来自哪里；
- 给出的命令能够明确指定项目虚拟环境解释器。

## 十七、复习题参考思路

### 题目 1 参考思路

分别进入两个项目，各自运行 `python -m venv .venv`，并使用各自的 `.\.venv\Scripts\python.exe -m pip` 安装对应版本。关闭终端后，激活带来的 `PATH` 修改消失，但两个 `.venv` 目录及已安装依赖仍保存在硬盘上，除非主动删除。

### 题目 2 参考思路

用 `python -c "import sys; print(sys.executable)"` 检查运行解释器；用 `python -m pip show requests` 或 `python -m pip list` 检查同一解释器对应环境中的安装情况。最常见原因是单独执行的 `pip` 属于一个 Python，而运行代码使用了另一个 Python。选择正确解释器后，再通过该解释器执行 `-m pip install requests`。

### 题目 3 参考思路

提交源代码、`requirements.txt`、`.gitignore`、README 和不含真实密钥的 `.env.example`；忽略 `.venv/`、缓存和真实 `.env`。同学 clone 后先确认 Python 版本，再创建并激活 `.venv`、执行 `python -m pip install -r requirements.txt`、配置自己的密钥，最后运行入口文件。

### 题目 4 参考思路

程序没有使用虚拟环境。`sys.executable` 指向全局 Python，两个 prefix 相等，requests 也来自全局 `Lib\site-packages`。提示符可能是旧显示或环境后来被覆盖。可靠方式是直接运行 `.\.venv\Scripts\python.exe <入口文件>`，再重新检查路径。
