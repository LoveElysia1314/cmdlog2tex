# cmdlog2tex

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)  
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

将终端日志（含 ANSI 颜色）转换为专业 LaTeX 文档的轻量级工具集，适用于实验报告、技术文档与教程生成。

---

## 简介

`cmdlog2tex` 提供两个互补的命令行工具：

- **`cmd2tex`**：执行命令流，实时显示输出，并自动生成带终端样式的 LaTeX 文档  
- **`log2tex`**：将已有终端日志（含 ANSI 色彩）转换为格式完整的 LaTeX 文档

设计遵循 Unix 哲学：单一职责、可组合、高效易用。

---

## 主要特性

- 🎨 保留 ANSI 颜色与终端格式  
- ⚡ `cmd2tex` 实时显示命令执行过程  
- 📝 输出基于 `tcolorbox` 美化的专业 LaTeX 文档  
- 🔧 支持自定义 shell 与工作目录  
- 🐧 原生支持 Linux（推荐 Ubuntu/Debian）  
- 🪟 Windows 支持 `log2tex`（`cmd2tex` 需 WSL）  
- 🌙 双主题：深色（屏幕） / 浅色（打印）  
- 🎯 双模式：纯文本 / 彩色（默认）  
- � 智能 log 文件管理（`.ansilog` 格式，默认保留）

---

## 安装

### 系统依赖（Linux）

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y util-linux python3-pip
sudo apt install -y texlive-xetex texlive-latex-extra texlive-fonts-recommended
```

> Windows 用户只需安装 Python 3.6+ 与 TeX 发行版（如 MiKTeX），即可使用 `log2tex`。

### 安装本工具

推荐使用 `pipx`（隔离环境）：

```bash
pipx install git+https://github.com/LoveElysia1314/cmdlog2tex.git
```

或用户级安装：

```bash
pip install --user git+https://github.com/LoveElysia1314/cmdlog2tex.git
```

验证安装：

```bash
cmd2tex --help
log2tex --help
```

> 若命令未找到，请确认 `~/.local/bin` 已加入 `PATH`。

---

## 快速开始

### 执行命令并生成 LaTeX（推荐）

```bash
# 创建命令文件
cat > demo.txt << 'EOF'
echo "Hello from cmdlog2tex!"
date
echo -e "\033[31mRed\033[0m and \033[32mGreen\033[0m text"
EOF

# 执行并转换
cmd2tex -i demo.txt -o demo.tex

# 编译 PDF (需安装latex相关依赖)
xelatex demo.tex
```

### 转换已有日志

```bash
log2tex -i session.log -o output.tex
xelatex output.tex
```

---

## 使用说明

### `cmd2tex`

```bash
cmd2tex -i <命令文件> -o <输出.tex> [--shell <shell>] [--plain|--colored] [--theme light|dark] [--no-log]
```

- 生成 `<命令文件>.ansilog` 中间文件（默认保留，可用 `--no-log` 删除）
- 支持与 `log2tex` 相同的样式控制参数

### `log2tex`

```bash
log2tex -i <日志或HTML> -o <输出.tex> [--plain|--colored] [--theme light|dark]
```

- 默认为 **彩色 + 深色主题**（适合大多数场景）  
- 使用 `--plain` 切换为无色模式  
- 使用 `--theme light` 切换为打印友好主题

---

## 环境变量（可选）

| 变量 | 作用 | 默认值 |
|------|------|--------|
| `CMD2TEX_SHELL` | 默认 shell | `bash --login -i` |
| `LOG2TEX_MODE` | 默认模式 | `colored` |
| `LOG2TEX_THEME` | 默认主题 | `dark` |

示例：

```bash
export LOG2TEX_MODE=colored
export LOG2TEX_THEME=light
```

## 许可证

本项目采用 [MIT License](LICENSE)。

---

## 链接

- **源码**: https://github.com/LoveElysia1314/cmdlog2tex  
- **问题反馈**: https://github.com/LoveElysia1314/cmdlog2tex/issues  

---

**Happy converting! 🎉**