#!/usr/bin/env python3
"""
LaTeX Template Module for cmdlog2tex

Contains LaTeX document templates and styling definitions.
"""

LATEX_DOCUMENT_TEMPLATE = """% Use ctexart document class for Chinese support
\\documentclass{{ctexart}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{terminalboxes}}

% 自动添加的颜色定义（由 log2tex 生成）
{color_defs}


% ============================================================================
% 使用说明：
%
% 无色模式（推荐，自动处理特殊字符）：
%   \\begin{{terminalplain}}{{Terminal}}{{dark}}
%     (base) max@qmobile:~/Documents$ ls
%   \\end{{terminalplain}}
%
% 有色模式（需要手动添加颜色命令）：
%   \\begin{{terminalcolored}}{{Terminal}}{{dark}}
%     (base) \\textcolor{{ansigreen}}{{max@qmobile}} ls \\\\
%   \\end{{terminalcolored}}
%
% 主题切换：
%   - 第二个参数使用 dark: 黑色背景，适合屏幕阅读
%   - 第二个参数使用 light: 白色背景，适合打印
%
% ============================================================================

\\begin{{document}}

\\begin{{{env_name}}}{{Terminal}}{{{theme}}}
{content}
\\end{{{env_name}}}

\\end{{document}}
"""