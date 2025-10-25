#!/usr/bin/env python3
"""
log2tex - Log to LaTeX Converter

Convert terminal logs (with ANSI colors) to LaTeX documents.
"""

import re
import argparse
import os
import sys
import shutil
import logging
from .latex_template import LATEX_DOCUMENT_TEMPLATE
from . import add_common_args, set_mode_defaults


class LogToTexConverter:
    """Convert terminal logs or HTML to LaTeX with terminal styling."""

    def __init__(self, mode="plain", theme="dark"):
        """
        初始化转换器

        Args:
            mode: 'plain' (无色，默认) 或 'colored' (有色)
            theme: 'dark' (默认) 或 'light'
        """
        self.mode = mode
        self.theme = theme
        self.used_colors = set()

    def strip_all_ansi_codes(self, text):
        """
        完全移除所有ANSI转义序列（包括SGR颜色序列）

        用于无色模式，生成纯文本输出。
        """
        # 1. 移除OSC序列
        text = re.sub(r"\x1b\][^\a\x1b]*(?:\a|\x1b\\)", "", text)
        text = re.sub(r"\x1b\]7;[^\a\x1b]*[\a\x1b\\]?", "", text)

        # 2. 移除私有模式序列
        text = re.sub(r"\x1b\[\?[0-9;]*[a-zA-Z]", "", text)

        # 3. 移除光标重定位模式
        text = re.sub(
            r"[\r\n](?:\x1b\[[0-9]*[ABCDEFGHJK])+(?:\x1b\[[0-2]?K)?[^\r\n]*(?=\r|\n|$)",
            "",
            text,
        )

        # 4. 移除光标移动序列
        text = re.sub(r"\x1b\[[0-9]*[ABCDEFGHJK]", "", text)

        # 5. 移除光标定位
        text = re.sub(r"\x1b\[[0-9;]*[Hf]", "", text)

        # 6. 移除行擦除序列
        text = re.sub(r"\x1b\[[0-2]?K", "", text)

        # 7. ⭐ 移除SGR颜色序列
        text = re.sub(r"\x1b\[[0-9;]*m", "", text)

        # 8. 移除所有其他CSI序列
        text = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)

        # 9. 清理多余的回车符
        text = re.sub(r"\r+", "", text)

        # 10. 规范化换行符
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 11. 清理多余的连续空行（保留单个空行）
        text = re.sub(r"\n\n\n+", "\n\n", text)

        return text

    def parse_sgr(self, params):
        """解析SGR (Select Graphic Rendition) 参数"""
        # ANSI颜色映射
        colors = {
            "30": "black",
            "31": "red",
            "32": "lime",
            "33": "yellow",
            "34": "blue",
            "35": "magenta",
            "36": "cyan",
            "37": "white",
            "90": "gray",
            "91": "#FF6B6B",
            "92": "#4ECB71",
            "93": "#FFD93D",
            "94": "#6BCF7F",
            "95": "#C792EA",
            "96": "#89DDFF",
            "97": "white",
            "40": "black",
            "41": "red",
            "42": "green",
            "43": "yellow",
            "44": "blue",
            "45": "magenta",
            "46": "cyan",
            "47": "white",
        }

        styles = {
            "color": None,
            "bgcolor": None,
            "bold": False,
            "italic": False,
            "underline": False,
        }

        if not params or params == ["0"] or params == [""]:
            return styles

        i = 0
        while i < len(params):
            param = params[i]

            if param == "0":  # Reset
                return {
                    "color": None,
                    "bgcolor": None,
                    "bold": False,
                    "italic": False,
                    "underline": False,
                }
            elif param == "1":
                styles["bold"] = True
            elif param == "3":
                styles["italic"] = True
            elif param == "4":
                styles["underline"] = True
            elif param in ["22", "23", "24"]:
                if param == "22":
                    styles["bold"] = False
                elif param == "23":
                    styles["italic"] = False
                elif param == "24":
                    styles["underline"] = False
            elif param in colors:
                if param.startswith("3") and len(param) == 2:
                    styles["color"] = colors[param]
                elif param.startswith("9") and len(param) == 2:
                    styles["color"] = colors[param]
                elif param.startswith("4") and len(param) == 2:
                    styles["bgcolor"] = colors[param]

            i += 1

        return styles

    def log_to_colored_latex(self, log_content):
        """Convert ANSI log to colored LaTeX content."""
        # 清理不需要的ANSI序列（保留SGR用于颜色转换）
        cleaned = self.strip_ansi_except_sgr(log_content)

        # Debug模式: 保存清理后的log
        if os.environ.get("LOG2TEX_DEBUG"):
            debug_file = "debug_cleaned.log"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(cleaned)
            print(
                f"[log2tex] Debug: saved cleaned log to {debug_file}", file=sys.stderr
            )

        # 转换ANSI SGR序列到LaTeX
        parts = []
        current_pos = 0
        current_styles = {
            "color": None,
            "bgcolor": None,
            "bold": False,
            "italic": False,
            "underline": False,
        }

        # 查找所有SGR序列 (ESC[...m)
        pattern = re.compile(r"\x1b\[([0-9;]*)m")

        for match in pattern.finditer(cleaned):
            # 添加之前的文本
            if match.start() > current_pos:
                text = cleaned[current_pos : match.start()]
                if text:
                    text = self.escape_latex_special_chars(text)
                    text = self.apply_latex_styles(text, current_styles)
                    parts.append(text)

            # 更新样式
            params = match.group(1).split(";") if match.group(1) else ["0"]
            new_styles = self.parse_sgr(params)

            # 如果样式改变,关闭之前的命令
            if new_styles != current_styles:
                if any(current_styles.values()):
                    parts.append("}")
                current_styles = new_styles

            current_pos = match.end()

        # 添加剩余文本
        if current_pos < len(cleaned):
            text = cleaned[current_pos:]
            if text:
                text = self.escape_latex_special_chars(text)
                text = self.apply_latex_styles(text, current_styles)
                parts.append(text)

        # 关闭最后的命令
        if any(current_styles.values()):
            parts.append("}")

        latex_content = "".join(parts)

        # 转换换行符为LaTeX换行
        lines = latex_content.split("\n")
        processed = []
        for line in lines:
            clean = line.rstrip()
            if clean:
                processed.append(clean + " \\\\")
            else:
                processed.append("")

        # 移除前后的空行
        while processed and not processed[0]:
            processed.pop(0)
        while processed and not processed[-1]:
            processed.pop()

        return "\n".join(processed)

    def strip_ansi_except_sgr(self, text):
        """
        清理不需要的ANSI转义序列（但保留SGR颜色序列）

        用于有色模式，保留 \\x1b[...m 序列用于后续颜色转换。
        """
        # 移除OSC序列 (终端标题等)
        text = re.sub(r"\x1b\][^\a\x1b]*(?:\a|\x1b\\)", "", text)
        text = re.sub(r"\x1b\]7;[^\a\x1b]*[\a\x1b\\]?", "", text)

        # 移除私有模式序列
        text = re.sub(r"\x1b\[\?[0-9;]*[a-zA-Z]", "", text)

        # 移除光标重定位模式
        text = re.sub(
            r"[\r\n](?:\x1b\[[0-9]*[ABCDEFGHJK])+(?:\x1b\[[0-2]?K)?[^\r\n]*(?=\r|\n|$)",
            "",
            text,
        )

        # 移除光标移动序列
        text = re.sub(r"\x1b\[[0-9]*[ABCDEFGHJK]", "", text)

        # 移除光标定位
        text = re.sub(r"\x1b\[[0-9;]*[Hf]", "", text)

        # 移除行擦除序列
        text = re.sub(r"\x1b\[[0-2]?K", "", text)

        # 清理多余的回车符
        text = re.sub(r"\r+", "\r", text)

        # 注意: 不移除 SGR 序列 (\x1b[...m)，保留用于颜色转换

        return text

    def apply_latex_styles(self, text, styles):
        """应用LaTeX样式到文本"""
        if not text or not any(styles.values()):
            return text

        commands = []
        if styles["bold"]:
            commands.append("\\textbf{")
        if styles["italic"]:
            commands.append("\\textit{")
        if styles["color"]:
            color_name = self.css_color_to_latex(styles["color"])
            if color_name:
                commands.append(f"\\textcolor{{{color_name}}}{{")
        if styles["bgcolor"]:
            color_name = self.css_color_to_latex(styles["bgcolor"])
            if color_name:
                commands.append(f"\\colorbox{{{color_name}}}{{")

        if commands:
            return "".join(commands) + text
        return text

    def escape_latex_special_chars(self, text):
        """转义LaTeX特殊字符"""
        text = text.replace("\\", "\\textbackslash{}")
        text = text.replace("{", "\\{")
        text = text.replace("}", "\\}")
        text = text.replace("$", "\\$")
        text = text.replace("#", "\\#")
        text = text.replace("%", "\\%")
        text = text.replace("~", "\\textasciitilde{}")
        text = text.replace("_", "\\_")
        text = text.replace("^", "\\textasciicircum{}")
        text = text.replace("&", "\\&")

        # 处理多个空格
        def replace_multiple_spaces(match):
            spaces = match.group(0)
            if len(spaces) > 1:
                return spaces[0] + " \\ " * (len(spaces) - 1)
            return spaces

        text = re.sub(r" +", replace_multiple_spaces, text)

        return text

    def log_to_plain_latex(self, log_content):
        """
        直接将日志转换为无色LaTeX内容

        不经过HTML阶段，直接生成纯文本内容。
        适用于 terminalplain 环境（基于listings）。

        Args:
            log_content: 原始日志内容

        Returns:
            str: 清理后的纯文本内容（无需特殊转义）
        """
        # 完全去除ANSI码
        clean_content = self.strip_all_ansi_codes(log_content)

        return clean_content

    def css_color_to_latex(self, css_color):
        """Convert CSS color to LaTeX color name."""
        if not css_color:
            return None

        css_color = css_color.replace(" ", "")

        # Named colors
        color_map = {
            "black": "black",
            "white": "white",
            "red": "red",
            "green": "green",
            "blue": "blue",
            "yellow": "yellow",
            "cyan": "cyan",
            "magenta": "magenta",
            "gray": "gray",
            "darkgray": "darkgray",
            "lightgray": "lightgray",
            "brown": "brown",
            "lime": "lime",
            "olive": "olive",
            "orange": "orange",
            "pink": "pink",
            "purple": "purple",
            "teal": "teal",
            "violet": "violet",
        }

        if css_color.lower() in color_map:
            return color_map[css_color.lower()]

        # Hex colors
        if css_color.startswith("#"):
            if len(css_color) == 7:  # #RRGGBB
                r = int(css_color[1:3], 16) / 255.0
                g = int(css_color[3:5], 16) / 255.0
                b = int(css_color[5:7], 16) / 255.0
                name = f"color{css_color[1:].lower()}"
                self.used_colors.add((name, r, g, b))
                return name
            elif len(css_color) == 4:  # #RGB
                r = int(css_color[1] * 2, 16) / 255.0
                g = int(css_color[2] * 2, 16) / 255.0
                b = int(css_color[3] * 2, 16) / 255.0
                name = f"color{(css_color[1:]*2).lower()}"
                self.used_colors.add((name, r, g, b))
                return name

        # rgb() format
        match = re.match(r"rgb\((\d+),(\d+),(\d+)\)", css_color)
        if match:
            r = int(match.group(1)) / 255.0
            g = int(match.group(2)) / 255.0
            b = int(match.group(3)) / 255.0
            name = f"colorrgb{match.group(1)}{match.group(2)}{match.group(3)}"
            self.used_colors.add((name, r, g, b))
            return name

        return None

    def get_color_definitions(self):
        """Generate LaTeX color definitions."""
        if not self.used_colors:
            return ""

        lines = ["% Auto-generated color definitions"]
        for name, r, g, b in self.used_colors:
            lines.append(f"\\definecolor{{{name}}}{{rgb}}{{{r:.3f},{g:.3f},{b:.3f}}}")
        return "\n".join(lines) + "\n"

    def generate_latex_document(self, content):
        """
        生成完整LaTeX文档（统一模板）

        使用统一的模板，根据 self.mode 和 self.theme 选择环境和主题。
        模板中同时定义了 terminalcolored 和 terminalplain 环境，
        用户可以后期修改环境参数来切换。

        Args:
            content: LaTeX内容（有色模式已包含颜色命令，无色模式为纯文本）

        Returns:
            str: 完整的LaTeX文档
        """
        # 获取颜色定义（有色模式需要）
        color_defs = self.get_color_definitions()

        # 根据模式选择环境名称
        env_name = "terminalplain" if self.mode == "plain" else "terminalcolored"

        # 使用统一模板
        return LATEX_DOCUMENT_TEMPLATE.format(
            color_defs=color_defs, env_name=env_name, theme=self.theme, content=content
        )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert terminal logs to LaTeX.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Environment Variables:
  LOG2TEX_MODE            - 默认模式: plain/colored (默认: colored)
  LOG2TEX_THEME           - 默认主题: dark/light (默认: dark)""",
    )

    parser.add_argument("--input", "-i", required=True, help="输入文件（日志，必需）")
    parser.add_argument("--output", "-o", required=True, help="输出LaTeX文件（必需）")

    # 添加共同参数
    parser = add_common_args(parser)

    args = parser.parse_args()

    # 设置默认模式
    args = set_mode_defaults(args)

    return args


def main():
    """Main entry point."""
    args = parse_args()

    converter = LogToTexConverter(mode=args.mode, theme=args.theme)

    # Validate input file exists
    if not os.path.exists(args.input):
        print(f"[log2tex] 错误: 输入文件不存在: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Read input
    print(f"[log2tex] 读取: {args.input}", file=sys.stderr)
    with open(args.input, "r", encoding="utf-8", errors="ignore") as f:
        input_content = f.read()

    # 根据模式处理
    if args.mode == "plain":
        # ===== 无色模式 =====
        print(f"[log2tex] 无色模式 + {args.theme} 主题", file=sys.stderr)
        latex_content = converter.log_to_plain_latex(input_content)
    else:
        # ===== 有色模式 =====
        print(f"[log2tex] 有色模式 + {args.theme} 主题", file=sys.stderr)
        latex_content = converter.log_to_colored_latex(input_content)

    # 生成完整文档并输出
    latex_doc = converter.generate_latex_document(latex_content)
    output_dir = os.path.dirname(args.output) or "."
    os.makedirs(output_dir, exist_ok=True)
    
    # 写入 LaTeX 文档
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(latex_doc)
    print(f"[log2tex] 输出已写入: {args.output}", file=sys.stderr)

    # 复制 terminalboxes.sty 到输出目录
    sty_src = os.path.join(os.path.dirname(__file__), "terminalboxes.sty")
    sty_dst = os.path.join(output_dir, "terminalboxes.sty")
    if os.path.exists(sty_src):
        shutil.copy(sty_src, sty_dst)
        print(f"[log2tex] 宏包已复制: {sty_dst}", file=sys.stderr)
    else:
        print(f"[log2tex] 警告: 未找到宏包文件: {sty_src}", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[log2tex] Interrupted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"[log2tex] Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)
