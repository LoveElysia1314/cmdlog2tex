#!/usr/bin/env python3
"""
cmd2tex - Command Stream to LaTeX Converter

Execute a stream of shell commands and automatically convert output to LaTeX.
Combines 'script' command execution with log2tex conversion.

HTML to LaTeX conversion (via log2tex) is inspired by:
https://github.com/daniel-j/html2latex
"""

import argparse
import os
import sys
import subprocess
import shutil
from . import add_common_args, set_mode_defaults


def check_dependencies():
    """Check if required commands are available."""
    missing = []
    if not shutil.which("script"):
        missing.append("script (util-linux)")
    if not shutil.which("log2tex"):
        missing.append("log2tex")
    return missing


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Execute command stream and convert to LaTeX.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Environment Variables:
  CMD2TEX_SHELL      - Default shell (default: bash --login -i)""",
    )

    parser.add_argument(
        "--input", "-i", required=True, help="Input commands file (required)"
    )
    parser.add_argument(
        "--output", "-o", required=True, help="Output LaTeX file (required)"
    )
    parser.add_argument(
        "--shell",
        default=os.environ.get("CMD2TEX_SHELL", "bash --login -i"),
        help="Shell to execute commands (default: bash --login -i or $CMD2TEX_SHELL)",
    )
    parser.add_argument(
        "--no-log", action="store_true", help="删除生成的.ansilog文件（默认保留）"
    )

    # 添加共同参数
    parser = add_common_args(parser)

    args = parser.parse_args()

    # 设置默认模式
    args = set_mode_defaults(args)

    return args


def main():
    """Main entry point."""
    args = parse_args()

    # Check prerequisites
    missing = check_dependencies()
    if missing:
        print("Error: Missing required dependencies:", file=sys.stderr)
        for dep in missing:
            print(f"  - {dep}", file=sys.stderr)
        print("\nInstall missing dependencies:", file=sys.stderr)
        print("  Ubuntu/Debian: sudo apt install util-linux", file=sys.stderr)
        print("  For log2tex: pip install --user .", file=sys.stderr)
        sys.exit(1)

    # Validate input file exists
    if not os.path.exists(args.input):
        print(f"[cmd2tex] Error: input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    commands_path = os.path.abspath(args.input)
    output_file = args.output

    # 修改log文件命名：使用输入文件basename + .ansilog
    input_base = os.path.splitext(args.input)[0]
    log_file = f"{input_base}.ansilog"

    input_display = args.input
    output_display = args.output

    print(f"[cmd2tex] Input: {input_display}", file=sys.stderr)
    print(f"[cmd2tex] Output LaTeX: {output_display}", file=sys.stderr)

    # Change to working directory if specified
    original_dir = os.getcwd()
    try:
        # Step 1: Execute commands via script
        cmd_str = f'{args.shell} < "{commands_path}"'
        print(f"[cmd2tex] Executing: script -c '{cmd_str}' {log_file}", file=sys.stderr)
        print("-" * 60, file=sys.stderr)

        # Execute via script command, output to log file, always show real-time output
        proc = subprocess.run(
            ["script", "-c", cmd_str, log_file], text=True, stdout=None, stderr=None
        )

        print("-" * 60, file=sys.stderr)

        if proc.returncode != 0:
            print(
                f"[cmd2tex] Warning: command exited with code {proc.returncode}",
                file=sys.stderr,
            )
            # Continue to conversion even if commands failed

        print("[cmd2tex] Command execution completed.", file=sys.stderr)

        # Step 2: Convert log to LaTeX via log2tex
        print(f"[cmd2tex] Converting log to LaTeX...", file=sys.stderr)

        log2tex_cmd = ["log2tex", "-i", log_file, "-o", output_file]

        # 根据参数添加选项
        if args.mode == "plain":
            log2tex_cmd.append("--plain")
        else:
            log2tex_cmd.append("--colored")
        log2tex_cmd.extend(["--theme", args.theme])

        # Set environment variables for log2tex
        env = os.environ.copy()

        proc = subprocess.run(log2tex_cmd, env=env)

        if proc.returncode != 0:
            print(
                f"[cmd2tex] Error: log2tex failed with code {proc.returncode}",
                file=sys.stderr,
            )
            sys.exit(proc.returncode)

        print(f"[cmd2tex] LaTeX file created: {output_file}", file=sys.stderr)

        # Clean up intermediate log file (unless --no-log is specified)
        if os.path.exists(log_file) and args.no_log:
            os.remove(log_file)
            print(
                f"[cmd2tex] Cleaned up intermediate log file: {log_file}",
                file=sys.stderr,
            )
        else:
            print(f"[cmd2tex] Kept log file: {log_file}", file=sys.stderr)

        print("[cmd2tex] Conversion completed successfully.", file=sys.stderr)

    finally:
        # Restore original directory
        os.chdir(original_dir)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[cmd2tex] Interrupted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"[cmd2tex] Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)
