# cmdlog2tex

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)  
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

A lightweight toolkit for converting terminal logs (with ANSI colors) into professional LaTeX documents, ideal for experimental reports, technical documentation, and tutorial generation.

---

## Introduction

`cmdlog2tex` provides two complementary command-line tools:

- **`cmd2tex`**: Executes a command stream, displays output in real time, and automatically generates a LaTeX document styled like a terminal.
- **`log2tex`**: Converts existing terminal logs (with ANSI colors) into fully formatted LaTeX documents.

Designed following Unix philosophy: single responsibility, composable, efficient, and easy to use.

---

## Key Features

- 🎨 Preserves ANSI colors and terminal formatting  
- ⚡ `cmd2tex` displays command execution in real time  
- 📝 Outputs professional LaTeX documents enhanced with `tcolorbox`  
- 🔧 Supports custom shells and working directories  
- 🐧 Native Linux support (Ubuntu/Debian recommended)  
- 🪟 Windows supports `log2tex` (`cmd2tex` requires WSL)  
- 🌙 Dual themes: dark (screen) / light (print)  
- 🎯 Dual modes: plain text / colored (default)  
- 📁 Intelligent log file management (`.ansilog` format, retained by default)

---

## Installation

### System Dependencies (Linux)

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y util-linux python3-pip
sudo apt install -y texlive-xetex texlive-latex-extra texlive-fonts-recommended
```

> Windows users only need Python 3.6+ and a TeX distribution (e.g., MiKTeX) to use `log2tex`.

### Install This Tool

Recommended via `pipx` (isolated environment):

```bash
pipx install git+https://github.com/LoveElysia1314/cmdlog2tex.git
```

Or install for the current user:

```bash
pip install --user git+https://github.com/LoveElysia1314/cmdlog2tex.git
```

Verify installation:

```bash
cmd2tex --help
log2tex --help
```

> If commands are not found, ensure `~/.local/bin` is in your `PATH`.

---

## Quick Start

### Execute Commands and Generate LaTeX (Recommended)

```bash
# Create a command file
cat > demo.txt << 'EOF'
echo "Hello from cmdlog2tex!"
date
echo -e "\033[31mRed\033[0m and \033[32mGreen\033[0m text"
EOF

# Execute and convert
cmd2tex -i demo.txt -o demo.tex

# Compile to PDF (requires LaTeX dependencies)
xelatex demo.tex
```

### Convert an Existing Log

```bash
log2tex -i session.log -o output.tex
xelatex output.tex
```

---

## Usage

### `cmd2tex`

```bash
cmd2tex -i <command_file> -o <output.tex> [--shell <shell>] [--plain|--colored] [--theme light|dark] [--no-log]
```

- Generates an intermediate `<command_file>.ansilog` (retained by default; use `--no-log` to delete)  
- Supports the same styling options as `log2tex`

### `log2tex`

```bash
log2tex -i <log_or_html> -o <output.tex> [--plain|--colored] [--theme light|dark]
```

- Defaults to **colored + dark theme** (suitable for most scenarios)  
- Use `--plain` for colorless mode  
- Use `--theme light` for print-friendly theme

---

## Environment Variables (Optional)

| Variable | Purpose | Default |
|----------|---------|---------|
| `CMD2TEX_SHELL` | Default shell | `bash --login -i` |
| `LOG2TEX_MODE` | Default mode | `colored` |
| `LOG2TEX_THEME` | Default theme | `dark` |

Example:

```bash
export LOG2TEX_MODE=colored
export LOG2TEX_THEME=light
```

## License

This project is licensed under the [MIT License](LICENSE).

---

## Links

- **Source Code**: https://github.com/LoveElysia1314/cmdlog2tex  
- **Issue Tracker**: https://github.com/LoveElysia1314/cmdlog2tex/issues  

---

**Happy converting! 🎉**