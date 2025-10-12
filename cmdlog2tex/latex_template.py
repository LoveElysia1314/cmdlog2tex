#!/usr/bin/env python3
"""
LaTeX Template Module for cmdlog2tex

Contains LaTeX document templates and styling definitions.
"""

LATEX_DOCUMENT_TEMPLATE = """% Use ctexart document class for Chinese support
\\documentclass{{ctexart}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{xcolor}}
\\usepackage[most]{{tcolorbox}}
\\usepackage{{listings}}

% ============================================================================
% 统一终端环境定义 - 支持有色/无色模式切换
% ============================================================================

% ===== 颜色定义 =====
\\definecolor{{terminalbg}}{{RGB}}{{40,44,52}}
\\definecolor{{terminalfg}}{{RGB}}{{171,178,191}}
\\definecolor{{promptgreen}}{{RGB}}{{39,201,63}}
\\definecolor{{pathblue}}{{RGB}}{{80,150,255}}

% ANSI 颜色定义（用于有色模式）
\\definecolor{{ansiblack}}{{RGB}}{{0,0,0}}
\\definecolor{{ansired}}{{RGB}}{{205,49,49}}
\\definecolor{{ansigreen}}{{RGB}}{{0,255,0}}
\\definecolor{{ansiyellow}}{{RGB}}{{255,255,0}}
\\definecolor{{ansiblue}}{{RGB}}{{0,0,255}}
\\definecolor{{ansimagenta}}{{RGB}}{{255,0,255}}
\\definecolor{{ansicyan}}{{RGB}}{{0,255,255}}
\\definecolor{{ansiwhite}}{{RGB}}{{255,255,255}}
\\definecolor{{ansigray}}{{RGB}}{{128,128,128}}
\\definecolor{{lime}}{{RGB}}{{0,255,0}}

{color_defs}

% ===== Listings 样式（用于无色模式）=====
\\lstdefinestyle{{terminalplain}}{{
  basicstyle=\\ttfamily\\small,
  breaklines=true,
  breakatwhitespace=false,
  breakautoindent=false,
  breakindent=0pt,
  numbers=none,
  showspaces=false,
  showstringspaces=false,
  showtabs=false,
  tabsize=4,
  frame=none,
  columns=fullflexible,
  keepspaces=true,
  upquote=true,
  literate={{~}}{{{{\\textasciitilde}}}}1
           {{\\^}}{{{{\\textasciicircum}}}}1
           {{\\$}}{{{{\\textdollar}}}}1
           {{\\#}}{{{{\\#}}}}1
           {{\\\\}}{{{{\\textbackslash}}}}1
}}

% ===== tcbset 样式预设 =====
\\tcbset{{
  base dark/.style={{
    colback=terminalbg,
    colframe=gray,
    coltext=terminalfg,
    coltitle=white,
    colbacktitle=black,
  }},
  base light/.style={{
    colback=white,
    colframe=gray,
    coltext=black,
    coltitle=black,
    colbacktitle=gray!20,
  }},
  base common/.style={{
    enhanced jigsaw,
    breakable,
    boxrule=0.5pt,
    arc=3pt,
    left=8pt,
    right=8pt,
    top=8pt,
    bottom=8pt,
    fonttitle=\\ttfamily\\small\\bfseries,
    before skip=10pt,
    after skip=10pt,
    width=\\textwidth,
  }}
}}

% ===== 有色终端环境 =====
% 用法：\\begin{{terminalcolored}}{{标题}}{{dark/light}}
\\newtcolorbox{{terminalcolored}}[2]{{
  base common,
  base #2,
  fontupper=\\ttfamily\\small,
  title=#1,
  title after break=#1,
}}

% ===== 无色终端环境（基于 listings）=====
% 用法：\\begin{{terminalplain}}{{标题}}{{dark/light}}
\\newtcblisting{{terminalplain}}[2]{{
  base common,
  base #2,
  listing engine=listings,
  listing only,
  listing options={{style=terminalplain,basicstyle=\\ttfamily\\small}},
  title=#1,
  title after break=#1,
}}

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
