# cmdlog2tex

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Version 0.9.0](https://img.shields.io/badge/version-0.9.0-green.svg)](https://github.com/LoveElysia1314/cmdlog2tex)

**语言：** [English](README.md) | 简体中文

---

将终端命令/日志（支持 ANSI 颜色）转换为优雅的 LaTeX 文档。提供三个 CLI 工具：

- cmd2log — 执行命令列表并生成日志
- log2tex — 将日志转换为 LaTeX
- cmd2tex — 完整流程（推荐）

适合实验报告、技术文档与培训材料。

---

## 示例

可以在此查看示例输出 PDF： [example/demo.pdf](example/demo.pdf)

下面展示示例 PDF 的第一页预览：

![示例 — 第1页](example/demo_pag.png)

---

## 安装

```bash
pip install cmdlog2tex
```

---

## 快速开始

推荐：一条命令完成整个流程

```bash
# 执行命令并生成 LaTeX 文档
cmd2tex --input commands.txt --output output.tex
```

需要显式指定 Shell 时：

```bash
# Windows (cmd)
cmd2tex --input commands.txt --output output.tex --shell cmd

# Windows (PowerShell)
cmd2tex --input commands.txt --output output.tex --shell powershell

# Linux / macOS (bash)
cmd2tex --input commands.sh --output output.tex --shell bash
```

---

## CLI 速查

### cmd2tex — 完整流程

```text
cmd2tex -i FILE -o FILE [options]

必需：
  -i, --input FILE          命令列表文件
  -o, --output FILE         输出 LaTeX 文件（默认：<input>.tex）

可选：
  -s, --shell SHELL         powershell | cmd | bash
  -p, --plain               纯文本（默认）
  -c, --colored             彩色文本（仅对 ANSI 日志有效）
  -d, --dark                深色主题（默认）
  -l, --light               浅色主题
  --language LANG           LaTeX 语言标记（默认：text）
```

### cmd2log — 仅记录

```text
cmd2log -i FILE [-o FILE] [--shell SHELL]
```

- Windows：生成 <base>.txt
- Linux/macOS：生成 <base>.ansilog

### log2tex — 仅转换

```text
log2tex -i FILE [-o FILE] [-p | -c] [-d | -l] [--language LANG]
```

- .tex 默认生成在输入文件所在目录。
- “彩色”模式仅对含 ANSI 的日志（例如 .ansilog）有效。

### 小技巧：短选项拼接

为方便输入，支持将短选项拼接：

- `-cd`  → `-c -d`
- `-pl`  → `-p -l`
- `-cpython` → `-c --language python`
- `-pbash`   → `-p --language bash`

---

## 输出与平台差异

根据平台及是否含 ANSI 颜色，输出文件略有不同。

Windows（cmd / PowerShell）：

```
commands.txt
  ↓ cmd2tex
  ├─ commands.txt           （日志，纯文本）
  └─ output.tex             （最终 LaTeX）
```

- 纯文本日志不会生成 `.plain.txt` / `.color.txt` 中间文件。

Linux / macOS（bash，通常含 ANSI 颜色）：

```
commands.sh
  ↓ cmd2tex
  ├─ commands.ansilog       （原始 ANSI 会话）
  ├─ commands.plain.txt     （去 ANSI 的纯文本）
  ├─ commands.color.txt     （ANSI → LaTeX 彩色片段）
  └─ output.tex             （最终 LaTeX）
```

`output.tex` 使用 `\\terminput` 引入上述文本文件之一。

---

## LaTeX 集成

最小示例（推荐使用 XeLaTeX 编译）：

```latex
\documentclass{article}
\usepackage{ctex} % 可选：中文支持
\usepackage{terminalcode}

\begin{document}

\terminput[text]{Terminal}{commands.plain.txt}

\end{document}
```

- 若出现 `Undefined control sequence \terminput`，请将 `terminalcode.sty` 复制到 `.tex` 同目录（工具也会自动复制一份到 `output.tex` 所在目录）。
- 主题切换：`\terminalcodetheme{dark}`（默认）或 `\terminalcodetheme{light}`。

---

## terminalcode 宏包安装

生成的 LaTeX 文档依赖于 **terminalcode** 宏包。该宏包已上传至 CTAN 和 GitHub，支持在线安装。

### 方案 1：系统级安装（推荐）

通过 LaTeX 发行版的包管理工具安装：

#### TeX Live（Windows / Linux / macOS）
```bash
tlmgr update --self
tlmgr install terminalcode
```

#### MiKTeX（Windows）
```bash
# 使用 MiKTeX 控制台 GUI
miktex-console

# 或命令行
mpm --install-package terminalcode
```

#### macOS（MacTeX）
```bash
# MacTeX 基于 TeX Live
tlmgr update --self
tlmgr install terminalcode
```

### 方案 2：本地副本（自动）

如果系统无法安装宏包，**cmdlog2tex 会自动在输出目录复制一份本地 terminalcode.sty**。你的 .tex 文件仍然可以正常编译。

### 宏包资源

- **CTAN**：https://ctan.org/pkg/terminalcode
- **GitHub**：https://github.com/LoveElysia1314/terminalcode-sty

---

## 支持的 LaTeX 发行版

| 发行版 | 系统级安装 | 本地备用 | 说明 |
|---|---|---|---|
| **TeX Live** | ✅ 支持 | ✅ 可用 | 推荐，官方标准 |
| **MacTeX** | ✅ 支持 | ✅ 可用 | 推荐 macOS 用户 |
| **MiKTeX** | ✅ 支持 | ✅ 可用 | Windows 流行选择 |
| **Overleaf** | ✅ 预装 | ✅ 可用 | 在线编辑器，无需操作 |
| **其他** | ⚠️ 可能支持 | ✅ 可用 | 本地备用保证兼容性 |

### cmdlog2tex 的处理方式

1. 首先检测系统是否已安装 terminalcode 宏包
2. 若已安装，使用系统宝包（推荐）
3. 若未安装，自动复制本地副本到输出目录
4. 无论哪种情况，你的 LaTeX 文档都能成功编译

---

## 故障排除

- LaTeX 宏缺失：复制 `terminalcode.sty` 并使用 XeLaTeX 编译。
- 中文乱码：确保文件为 UTF-8，推荐使用 XeLaTeX。
- Windows PowerShell 拒绝执行脚本：为当前用户设置执行策略。

---

## 已知限制

- 复杂 ANSI 序列可能无法完全映射；256/真彩色支持有限。
- 很长且无空格的行在 LaTeX 中可能超宽；建议适度换行。
- `\verb` 内的加粗/斜体存在天生限制（通过转义标记规避）。
- 当前版本默认不对会话元数据（PowerShell/Cmd）做自动过滤。

---

## 许可证与贡献

MIT License。欢迎提交 Issue / PR：https://github.com/LoveElysia1314/cmdlog2tex

---

版本：0.9.0  
更新：2025-11-01
