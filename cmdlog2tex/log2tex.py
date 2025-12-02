#!/usr/bin/env python3
"""
log2tex - Convert terminal logs to LaTeX documents

Unified module that handles all log processing steps:
  1. Log reading and platform detection
  2. Platform-specific filtering
  3. ANSI segment analysis and conversion
  4. Intermediate file generation (.plain.txt, .color.txt)
  5. LaTeX document generation

One-to-one mapping: log file → LaTeX document
"""

import re
import os
import sys
import shutil
import subprocess
import platform
from typing import Tuple, Optional, Dict, List


class LogAnalyzer:
    """Analyze logs and detect color capability."""

    @staticmethod
    def detect_color_from_suffix(log_file: str) -> Optional[str]:
        """
        Detect color capability from file suffix.

        Returns:
            'colored' if suffix indicates colored terminal
            'plain' if suffix indicates plain terminal
            None if no definitive suffix found
        """
        if log_file.endswith(".ansilog"):
            return "colored"
        # Windows unified format: .txt files are plain (no special filtering needed)
        elif log_file.endswith(".txt"):
            return "plain"
        return None

    @staticmethod
    def has_ansi_codes(content: str) -> bool:
        """Check if content contains ANSI escape sequences."""
        return bool(re.search(r"\x1b\[[0-9;]*[mGKHf]|\033\[[0-9;]*[mGKHf]", content))

    @staticmethod
    def has_powershell_markers(content: str) -> bool:
        """Check for PowerShell Start-Transcript markers."""
        if not re.search(r"^\s*\*{4,}\s*$", content, re.MULTILINE):
            return False
        if re.search(
            r"Script (started|stopped)|Started|Stopped script", content, re.IGNORECASE
        ):
            return True
        separator_count = len(re.findall(r"^\s*\*{4,}\s*$", content, re.MULTILINE))
        return separator_count >= 2

    @staticmethod
    def has_cmd_markers(content: str) -> bool:
        """Check for Cmd/Batch markers."""
        if re.search(r"[A-Z]:\\[^>\n]*>", content):
            return True
        if re.search(r"Command Prompt|cmd\.exe|batch|@echo", content, re.IGNORECASE):
            return True
        return False

    @staticmethod
    def detect_capabilities(log_file: str) -> dict:
        """
        Detect log capabilities: color support and platform markers.

        Returns:
            {
                'has_color': bool,
                'has_powershell': bool,
                'has_cmd': bool,
                'platform_type': 'colored' | 'powershell' | 'cmd'
            }
        """
        result = {
            "has_color": False,
            "has_powershell": False,
            "has_cmd": False,
            "platform_type": "plain",  # default
        }

        # Layer 1: Suffix-based detection
        suffix_type = LogAnalyzer.detect_color_from_suffix(log_file)
        if suffix_type:
            result["platform_type"] = suffix_type
            if suffix_type == "colored":
                result["has_color"] = True
            return result

        # Layer 2: Content-based detection
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(5000)  # Read first 5000 chars for speed

                # Check for ANSI codes (indicates colored terminal)
                if LogAnalyzer.has_ansi_codes(content):
                    result["has_color"] = True
                    result["platform_type"] = "colored"
                    return result

                # Check for PowerShell markers (no color, but can still filter with PowerShell logic)
                if LogAnalyzer.has_powershell_markers(content):
                    result["has_powershell"] = True
                    result["platform_type"] = "powershell"
                    return result

                # Check for Cmd markers
                if LogAnalyzer.has_cmd_markers(content):
                    result["has_cmd"] = True
                    result["platform_type"] = "cmd"
                    return result

            except Exception:
                pass

        # Default to plain terminal without specific markers
        result["platform_type"] = "plain"
        return result

    @staticmethod
    def filter_powershell_log(content: str) -> str:
        """Extract useful content from PowerShell Transcript."""
        lines = content.split("\n")

        # Find separator lines (****)
        separator_indices = []
        for i, line in enumerate(lines):
            if re.match(r"^\s*\*{4,}\s*$", line):
                separator_indices.append(i)

        if len(separator_indices) < 2:
            return content

        # Extract middle section
        start_idx = separator_indices[0] + 1
        end_idx = separator_indices[-2]
        middle_lines = lines[start_idx:end_idx]

        # Filter out metadata
        filtered_lines = []
        for line in middle_lines:
            if re.match(r"^\s*Script (started|stopped)", line):
                continue
            if re.match(r"^\s*Output file is", line):
                continue
            filtered_lines.append(line)

        return "\n".join(filtered_lines).strip()

    @staticmethod
    def filter_cmd_log(content: str) -> str:
        """Extract useful content from Cmd log."""
        lines = content.split("\n")

        filtered_lines = []
        in_content = False

        for line in lines:
            if re.match(r"^\s*\*{4,}\s*$", line):
                in_content = not in_content
                continue

            # Skip metadata lines
            if re.match(r"^\s*Command Execution Log\s*$", line, re.IGNORECASE):
                continue
            if re.match(r"^\s*Execution Complete\s*$", line, re.IGNORECASE):
                continue

            if in_content or (line.strip() and not re.match(r"^\s*\*{4,}\s*$", line)):
                filtered_lines.append(line)

        return "\n".join(filtered_lines).strip()

    @staticmethod
    def read_and_filter(log_file: str, capabilities: dict) -> dict:
        """
        Read log file and apply appropriate filtering based on capabilities.

        For ANSI logs (colored): generate both plain and colored versions
        For plain logs (.txt on Windows): no filtering needed, return as-is

        Args:
            log_file: Path to log file
            capabilities: Result from detect_capabilities()

        Returns:
            {
                'plain_content': str,
                'color_content': str or None,
            }
        """
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        result = {
            "plain_content": None,
            "color_content": None,
        }

        if capabilities["has_color"]:
            # Colored terminal (ANSI log): generate both plain and colored versions
            result["plain_content"] = LatexFormatter.strip_all_ansi(content)
            result["color_content"] = LatexFormatter.to_latex(content)
        else:
            # Plain terminal (.txt files from Windows or others)
            # No special filtering needed - use content as-is
            result["plain_content"] = content

        return result


class LatexFormatter:
    """Format ANSI text to LaTeX code."""

    # Compiled regex patterns for performance
    SGR_PATTERN = re.compile(r"\x1b\[([0-9;]*)m")

    ANSI_CODES = {
        "30": "30",
        "31": "31",
        "32": "32",
        "33": "33",
        "34": "34",
        "35": "35",
        "36": "36",
        "37": "37",
        "90": "90",
        "91": "91",
        "92": "92",
        "93": "93",
        "94": "94",
        "95": "95",
        "96": "96",
        "97": "97",
    }

    @staticmethod
    def strip_all_ansi(text: str) -> str:
        """Remove all ANSI escape sequences."""
        # Remove OSC sequences
        text = re.sub(r"\x1b\][^\a\x1b]*(?:\a|\x1b\\)", "", text)
        text = re.sub(r"\x1b\]7;[^\a\x1b]*[\a\x1b\\]?", "", text)

        # Remove private mode sequences
        text = re.sub(r"\x1b\[\?[0-9;]*[a-zA-Z]", "", text)

        # Remove cursor repositioning
        text = re.sub(
            r"[\r\n](?:\x1b\[[0-9]*[ABCDEFGHJK])+(?:\x1b\[[0-2]?K)?[^\r\n]*(?=\r|\n|$)",
            "",
            text,
        )

        # Remove cursor movement and positioning
        text = re.sub(r"\x1b\[[0-9]*[ABCDEFGHJK]", "", text)
        text = re.sub(r"\x1b\[[0-9;]*[Hf]", "", text)
        text = re.sub(r"\x1b\[[0-2]?K", "", text)

        # Remove SGR sequences (colors)
        text = re.sub(r"\x1b\[[0-9;]*m", "", text)

        # Remove other CSI sequences
        text = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)

        # Clean up line endings
        text = re.sub(r"\r+", "", text)
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove excessive blank lines
        text = re.sub(r"\n\n\n+", "\n\n", text)

        return text

    @staticmethod
    def parse_sgr(params: List[str]) -> Dict:
        """Parse SGR (color) parameters. Ignore text formatting attributes like bold."""
        styles = {"color": None}

        if not params or params == ["0"] or params == [""]:
            return styles

        for param in params:
            if param == "0":
                return {"color": None}
            # Only extract color codes (30-37, 90-97), ignore formatting attributes (1, bold, etc.)
            elif param in LatexFormatter.ANSI_CODES:
                styles["color"] = param

        return styles

    @staticmethod
    def extract_segments(text: str) -> List[Tuple[str, Optional[str]]]:
        """
        Extract text segments with their ANSI color.

        Returns:
            List of (text, color_code)
        """
        segments = []
        current_pos = 0
        current_color = None

        for match in LatexFormatter.SGR_PATTERN.finditer(text):
            if match.start() > current_pos:
                segment_text = text[current_pos : match.start()]
                if segment_text:
                    segments.append((segment_text, current_color))

            params = match.group(1).split(";") if match.group(1) else ["0"]
            styles = LatexFormatter.parse_sgr(params)

            current_color = styles["color"]
            current_pos = match.end()

        if current_pos < len(text):
            segment_text = text[current_pos:]
            if segment_text:
                segments.append((segment_text, current_color))

        return segments

    @staticmethod
    def choose_verb_delimiter(text: str) -> str:
        """Choose a delimiter not present in text for \\verb."""
        delimiters = ["|", "/", "!", "@", "#", "$", "%", "^", "&", "*"]
        for delim in delimiters:
            if delim not in text:
                return delim
        return "|"

    @staticmethod
    def format_segment(text: str, color: Optional[str]) -> str:
        """Format a segment using \\ac and \\verb."""
        if not text:
            return ""

        stripped = text.lstrip()
        leading_spaces = len(text) - len(stripped)
        stripped = stripped.rstrip()
        trailing_spaces = len(text) - leading_spaces - len(stripped)

        if not stripped:
            return " " * len(text)

        if color:
            delim = LatexFormatter.choose_verb_delimiter(stripped)
            escaped_text = stripped.replace(
                delim, f"\\text{chr(ord('b')+1)}ar{{{delim}}}"
            )
            color_param = color if color else ""
            result = f"«\\ac{{{color_param}}}\\verb{delim}{escaped_text}{delim}»"
        else:
            result = stripped

        return " " * leading_spaces + result + " " * trailing_spaces

    @staticmethod
    def to_latex(text: str) -> str:
        """Convert ANSI-formatted text to LaTeX."""
        # Preserve SGR codes, remove other ANSI codes
        text = re.sub(r"\x1b\][^\a\x1b]*(?:\a|\x1b\\)", "", text)
        text = re.sub(r"\x1b\]7;[^\a\x1b]*[\a\x1b\\]?", "", text)
        text = re.sub(r"\x1b\[\?[0-9;]*[a-zA-Z]", "", text)
        text = re.sub(
            r"[\r\n](?:\x1b\[[0-9]*[ABCDEFGHJK])+(?:\x1b\[[0-2]?K)?[^\r\n]*(?=\r|\n|$)",
            "",
            text,
        )
        text = re.sub(r"\x1b\[[0-9]*[ABCDEFGHJK]", "", text)
        text = re.sub(r"\x1b\[[0-9;]*[Hf]", "", text)
        text = re.sub(r"\x1b\[[0-2]?K", "", text)
        text = re.sub(r"\r+", "\r", text)

        lines = []
        for line in text.split("\n"):
            if not line:
                lines.append("")
                continue

            segments = LatexFormatter.extract_segments(line)
            formatted_parts = [
                LatexFormatter.format_segment(seg_text, color)
                for seg_text, color in segments
            ]
            lines.append("".join(formatted_parts))

        return "\n".join(lines)


class DocumentBuilder:
    """Build LaTeX document and generate output files."""

    @staticmethod
    def generate_tex(
        colored_txt: str, plain_txt: str, theme: str, language: str
    ) -> str:
        """Generate LaTeX document code."""
        from .latex_template import LATEX_DOCUMENT_TEMPLATE

        # Use colored or plain version (use only basename for relative path)
        input_file = (
            os.path.basename(colored_txt)
            if colored_txt
            else os.path.basename(plain_txt)
        )
        env_begin = f"\\terminput[{language}]{{Terminal}}{{{input_file}}}"

        return LATEX_DOCUMENT_TEMPLATE.format(
            theme=theme, env_begin=env_begin, env_end="", content=""
        )

    @staticmethod
    def write_sidecar_files(
        log_file: str,
        base_path: str,
        plain_content: str,
        color_content: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Write intermediate text files.

        For ANSI colored logs: generate .plain.txt and .color.txt
        For plain logs: don't generate intermediate files, use the original log directly

        Args:
            log_file: Original log file path
            base_path: Base path for output files
            plain_content: Plain text content
            color_content: Colored text content (optional)

        Returns:
            {'plain_txt': filename or original_log, 'color_txt': filename or None}
        """
        # Check if this is an ANSI colored log
        is_colored = color_content is not None

        if is_colored:
            # For ANSI logs: generate intermediate .plain.txt and .color.txt files
            base = os.path.splitext(base_path)[0]
            plain_path = f"{base}.plain.txt"
            color_path = f"{base}.color.txt"

            with open(plain_path, "w", encoding="utf-8") as f:
                f.write(plain_content)

            with open(color_path, "w", encoding="utf-8") as f:
                f.write(color_content)

            return {
                "plain_txt": os.path.basename(plain_path),
                "color_txt": os.path.basename(color_path),
            }
        else:
            # For plain logs (.txt files from Windows, etc.):
            # Don't create intermediate files, use the original log file directly
            return {"plain_txt": os.path.basename(log_file), "color_txt": None}

    @staticmethod
    def copy_macro_package(output_dir: str) -> Optional[str]:
        """
        Smart decision: system package preferred, local fallback.

        Priority:
        1. System-wide terminalcode package found → use it, no copy
        2. System package not found → copy local terminalcode.sty + print tips

        Args:
            output_dir: Output directory

        Returns:
            Basename of copied .sty file, or None if using system package
        """

        # Check for system package
        if DocumentBuilder.has_system_terminalcode():
            print(
                "[cmdlog2tex] Using system terminalcode package",
                file=sys.stderr,
            )
            return None

        # System package not found, copy local fallback
        sty_src = os.path.join(os.path.dirname(__file__), "terminalcode.sty")
        sty_dst = os.path.join(output_dir, "terminalcode.sty")

        if os.path.exists(sty_src):
            try:
                shutil.copy(sty_src, sty_dst)
                print(
                    "[cmdlog2tex] Local terminalcode.sty copied to output directory",
                    file=sys.stderr,
                )
                print(
                    "[cmdlog2tex] Note: System-wide installation is recommended:",
                    file=sys.stderr,
                )
                print(
                    "[cmdlog2tex]   tlmgr update --self && tlmgr install terminalcode",
                    file=sys.stderr,
                )
            except (IOError, OSError) as e:
                print(
                    f"[cmdlog2tex] Warning: Failed to copy terminalcode.sty: {e}",
                    file=sys.stderr,
                )
            return os.path.basename(sty_dst)

        print(
            "[cmdlog2tex] Warning: terminalcode.sty not found anywhere",
            file=sys.stderr,
        )
        return None

    @staticmethod
    def has_system_terminalcode() -> bool:
        """
        Check if terminalcode package is installed system-wide.

        Tries multiple detection methods for cross-platform compatibility.

        Returns:
            True if system package found, False otherwise
        """

        # Method 1: Use kpsewhich (TeX Live / MacTeX)
        try:
            result = subprocess.run(
                ["kpsewhich", "terminalcode.sty"],
                capture_output=True,
                timeout=2,
                text=True,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass

        # Method 2: Search standard TEXMF directories
        try:
            candidates = DocumentBuilder._get_texmf_candidates()
            for directory in candidates:
                sty_path = os.path.join(directory, "terminalcode.sty")
                if os.path.isfile(sty_path):
                    return True
        except Exception:
            pass

        return False

    @staticmethod
    def _get_texmf_candidates() -> list:
        """
        Get candidate TEXMF directories for different LaTeX distributions.

        Returns:
            List of candidate directory paths to search for terminalcode.sty
        """
        candidates = []
        home = os.path.expanduser("~")
        system = platform.system()

        if system == "Windows":
            bases = [
                "C:\\texlive",
                "C:\\Program Files\\MiKTeX",
                os.path.join(os.environ.get("APPDATA", ""), "MiKTeX"),
                os.path.join(home, "texmf"),
            ]
            for base in bases:
                if os.path.exists(base):
                    candidates.extend(
                        [
                            os.path.join(
                                base, "texmf-dist", "tex", "latex", "terminalcode"
                            ),
                            os.path.join(base, "texmf-dist", "tex", "latex"),
                            os.path.join(base, "tex", "latex"),
                        ]
                    )
        else:  # Linux / macOS
            bases = [
                "/usr/local/texlive",
                "/usr/share/texlive",
                "/opt/texlive",
                os.path.join(home, "texmf"),
                os.path.join(home, ".texmf"),
            ]
            for base in bases:
                if os.path.exists(base):
                    candidates.extend(
                        [
                            os.path.join(
                                base, "texmf-dist", "tex", "latex", "terminalcode"
                            ),
                            os.path.join(base, "texmf-dist", "tex", "latex"),
                            os.path.join(base, "tex", "latex"),
                        ]
                    )

        return candidates


def process_log_to_latex(
    log_file: str,
    output_tex: str,
    output_dir: Optional[str] = None,
    format: str = "color",
    theme: str = "dark",
    language: str = "text",
) -> dict:
    """
    Main entry point: Convert log file to LaTeX document.

    Args:
        log_file: Path to input log file
        output_tex: Output LaTeX filename (without path)
        output_dir: Output directory (default: same as log_file)
        format: 'color' | 'plain' (default: 'color')
                For colored terminals: selects which txt file to use in LaTeX
                For plain terminals: parameter is ignored, always outputs plain
        theme: 'dark' | 'light'
        language: 'bash' | 'python' | 'text'

    Returns:
        {
            'platform_type': str,
            'tex_file': str,
            'plain_txt': str,
            'color_txt': str | None,
        }

    Raises:
        FileNotFoundError: If log_file doesn't exist
        ValueError: If format or theme invalid
    """
    if not os.path.exists(log_file):
        raise FileNotFoundError(f"Log file not found: {log_file}")

    # Determine output directory
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(log_file))
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # Detect capabilities
    capabilities = LogAnalyzer.detect_capabilities(log_file)

    # Read and filter log
    filtered_result = LogAnalyzer.read_and_filter(log_file, capabilities)
    plain_content = filtered_result["plain_content"]
    color_content = filtered_result["color_content"]

    # Write intermediate files (only for ANSI logs)
    sidecar = DocumentBuilder.write_sidecar_files(
        log_file, log_file, plain_content, color_content
    )

    # Determine which version to use in LaTeX
    # For colored terminals: respect format parameter (default 'color')
    # For plain terminals: always use plain, ignore format parameter
    if capabilities["has_color"]:
        use_colored = (format == "color") and color_content is not None
        latex_input = sidecar["color_txt"] if use_colored else sidecar["plain_txt"]
    else:
        # Plain terminal: always use plain, ignore format parameter
        latex_input = sidecar["plain_txt"]

    # Generate LaTeX document
    latex_code = DocumentBuilder.generate_tex(
        latex_input if (latex_input == sidecar["color_txt"]) else None,
        sidecar["plain_txt"],
        theme,
        language,
    )

    # Write LaTeX file
    output_tex_path = os.path.join(output_dir, output_tex)
    with open(output_tex_path, "w", encoding="utf-8") as f:
        f.write(latex_code)

    # Copy macro package
    DocumentBuilder.copy_macro_package(output_dir)

    return {
        "platform_type": capabilities["platform_type"],
        "tex_file": os.path.basename(output_tex_path),
        "plain_txt": sidecar["plain_txt"],
        "color_txt": sidecar["color_txt"],
    }
