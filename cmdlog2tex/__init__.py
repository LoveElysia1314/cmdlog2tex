"""cmdlog2tex - Command Log to LaTeX Converter

A toolkit for executing command streams and converting terminal logs to LaTeX.

Commands:
    cmd2tex - Execute command streams and convert to LaTeX
    log2tex - Convert terminal logs or HTML to LaTeX

Acknowledgments:
    HTML to LaTeX conversion inspired by https://github.com/daniel-j/html2latex
"""

__version__ = "0.8.0"
__author__ = "cmdlog2tex contributors"

import os


def add_common_args(parser):
    """添加共同的参数到parser"""
    # 模式选择
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--plain",
        action="store_const",
        const="plain",
        dest="mode",
        help="无色模式：去除所有ANSI颜色，生成简洁的LaTeX",
    )
    mode_group.add_argument(
        "--colored",
        action="store_const",
        const="colored",
        dest="mode",
        help="有色模式（默认）：保留ANSI颜色并转换为LaTeX \\textcolor 命令",
    )

    # 主题选择
    parser.add_argument(
        "--theme",
        choices=["dark", "light"],
        default=os.environ.get("LOG2TEX_THEME", "dark"),
        help="主题选择：dark（黑暗，默认）或 light（明亮）",
    )

    return parser


def get_default_mode():
    """获取默认模式"""
    return os.environ.get("LOG2TEX_MODE", "colored")


def set_mode_defaults(args):
    """设置模式默认值"""
    if args.mode is None:
        args.mode = get_default_mode()
    return args
