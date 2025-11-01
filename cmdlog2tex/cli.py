#!/usr/bin/env python3
"""
cli - Command Line Interface

Handles all command-line argument parsing, validation, and workflow orchestration.
Supports three modes: cmd2log, log2tex, cmd2tex
"""

import sys
import os
import argparse
from . import command_executor, log2tex


def preprocess_argv():
    """
    Support short-option concatenation like -cd, -pl, -cpython, etc.

    Supported patterns:
      -cd          → -c -d
      -pl          → -p -l
      -cpython     → -c python
      -pbash       → -p bash
    """
    argv = sys.argv[1:]
    processed = []
    i = 0

    while i < len(argv):
        arg = argv[i]

        if arg.startswith("-") and not arg.startswith("--") and len(arg) > 2:
            flags = arg[1:]
            j = 0
            n = len(flags)

            while j < n:
                char = flags[j]
                if char in ("c", "p"):
                    processed.append("-" + char)
                    j += 1
                    # Collect non-flag chars as language
                    lang_chars = []
                    while j < n and flags[j] not in ("c", "p", "d", "l"):
                        lang_chars.append(flags[j])
                        j += 1
                    if lang_chars:
                        processed.append("".join(lang_chars))
                elif char in ("d", "l"):
                    processed.append("-" + char)
                    j += 1
                else:
                    lang_chars = flags[j:]
                    processed.append("".join(lang_chars))
                    break
        else:
            processed.append(arg)

        i += 1

    return processed


def create_parser():
    """Create argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="cmdlog2tex",
        description="Convert terminal commands and logs to LaTeX documents",
    )

    subparsers = parser.add_subparsers(dest="mode", help="Execution mode")

    # cmd2log subcommand
    cmd2log_parser = subparsers.add_parser(
        "cmd2log", help="Execute commands and capture logs"
    )
    cmd2log_parser.add_argument(
        "-i", "--input", required=True, help="Input file containing commands"
    )
    cmd2log_parser.add_argument(
        "-o",
        "--output",
        required=False,
        help="Output log file (auto-generated if omitted)",
    )
    cmd2log_parser.add_argument(
        "-s",
        "--shell",
        choices=["powershell", "cmd", "bash"],
        help="Shell to use (auto-detected if omitted)",
    )

    # log2tex subcommand
    log2tex_parser = subparsers.add_parser("log2tex", help="Convert logs to LaTeX")
    log2tex_parser.add_argument("-i", "--input", required=True, help="Input log file")
    log2tex_parser.add_argument(
        "-o",
        "--output",
        required=False,
        help="Output LaTeX file (auto-generated if omitted)",
    )

    format_group = log2tex_parser.add_mutually_exclusive_group()
    format_group.add_argument(
        "-c",
        "--colored",
        action="store_true",
        help="Use colored output (ANSI logs only)",
    )
    format_group.add_argument(
        "-p", "--plain", action="store_true", help="Use plain text output (default)"
    )

    theme_group = log2tex_parser.add_mutually_exclusive_group()
    theme_group.add_argument(
        "-d", "--dark", action="store_true", help="Use dark theme (default)"
    )
    theme_group.add_argument(
        "-l", "--light", action="store_true", help="Use light theme"
    )

    log2tex_parser.add_argument(
        "--language", default="text", help="Language for LaTeX (default: text)"
    )

    # cmd2tex subcommand
    cmd2tex_parser = subparsers.add_parser(
        "cmd2tex", help="Complete pipeline: execute commands and convert to LaTeX"
    )
    cmd2tex_parser.add_argument(
        "-i", "--input", required=True, help="Input file containing commands"
    )
    cmd2tex_parser.add_argument(
        "-o",
        "--output",
        required=False,
        help="Output LaTeX file (auto-generated if omitted)",
    )
    cmd2tex_parser.add_argument(
        "-s",
        "--shell",
        choices=["powershell", "cmd", "bash"],
        help="Shell to use (auto-detected if omitted)",
    )

    format_group2 = cmd2tex_parser.add_mutually_exclusive_group()
    format_group2.add_argument(
        "-c",
        "--colored",
        action="store_true",
        help="Use colored output (ANSI logs only)",
    )
    format_group2.add_argument(
        "-p", "--plain", action="store_true", help="Use plain text output (default)"
    )

    theme_group2 = cmd2tex_parser.add_mutually_exclusive_group()
    theme_group2.add_argument(
        "-d", "--dark", action="store_true", help="Use dark theme (default)"
    )
    theme_group2.add_argument(
        "-l", "--light", action="store_true", help="Use light theme"
    )

    cmd2tex_parser.add_argument(
        "--language", default="text", help="Language for LaTeX (default: text)"
    )

    return parser


def validate_cmd2log_args(args) -> None:
    """Validate cmd2log arguments."""
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input file not found: {args.input}")


def validate_log2tex_args(args) -> None:
    """Validate log2tex arguments."""
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input file not found: {args.input}")

    if args.input.endswith(".tex"):
        raise ValueError("Input file cannot be a LaTeX file (.tex)")


def auto_complete_args(args) -> None:
    """Auto-complete missing arguments."""
    # Determine format (smart default based on log file type)
    if not hasattr(args, "format"):
        # For subcommands that have format
        if hasattr(args, "colored") and args.colored:
            args.format = "color"
        elif hasattr(args, "plain") and args.plain:
            args.format = "plain"
        else:
            # Auto-detect based on log file type
            # For log2tex and cmd2tex modes, check if input file suggests ANSI colors
            if args.mode in ("log2tex", "cmd2tex"):
                input_file = args.input
                if input_file.endswith(".ansilog"):
                    # ANSI log: use colored by default
                    args.format = "color"
                else:
                    # Plain text log (.txt, etc.): use plain
                    args.format = "plain"
            else:
                # cmd2log mode: format doesn't apply
                args.format = "plain"

    # Determine theme (default to dark)
    # Use CLI flags only; no environment variables
    if hasattr(args, "light") and args.light:
        args.theme = "light"
    else:
        args.theme = "dark"

    # Auto-complete output filenames
    if args.mode == "cmd2log" and not args.output:
        args.output = command_executor.generate_log_filename(args.input, args.shell)

    elif args.mode == "log2tex" and not args.output:
        base = os.path.splitext(args.input)[0]
        args.output = f"{base}.tex"

    elif args.mode == "cmd2tex" and not args.output:
        base = os.path.splitext(args.input)[0]
        args.output = f"{base}.tex"


def execute_cmd2log(args) -> None:
    """Execute cmd2log mode."""
    print(f"[cmdlog2tex] cmd2log: {args.input} → {args.output}", file=sys.stderr)

    returncode, shell_used, log_file = command_executor.execute_commands(
        input_file=args.input, output_log=args.output, shell=args.shell
    )

    print(
        f"[cmdlog2tex] Log created: {os.path.basename(log_file)} (shell: {shell_used})",
        file=sys.stderr,
    )
    if returncode != 0:
        print(
            f"[cmdlog2tex] Warning: Command exited with code {returncode}",
            file=sys.stderr,
        )


def execute_log2tex(args) -> None:
    """Execute log2tex mode."""
    print(f"[cmdlog2tex] log2tex: {args.input} → {args.output}", file=sys.stderr)

    # Determine output directory
    output_dir = os.path.dirname(os.path.abspath(args.output)) or "."
    output_tex_name = os.path.basename(args.output)

    result = log2tex.process_log_to_latex(
        log_file=args.input,
        output_tex=output_tex_name,
        output_dir=output_dir,
        format=args.format,
        theme=args.theme,
        language=args.language,
    )

    print(f"[cmdlog2tex] Platform detected: {result['platform_type']}", file=sys.stderr)
    print(f"[cmdlog2tex] Generated: {result['tex_file']}", file=sys.stderr)
    print(f"[cmdlog2tex] Intermediate: {result['plain_txt']}", file=sys.stderr)
    if result["color_txt"]:
        print(f"[cmdlog2tex] Intermediate: {result['color_txt']}", file=sys.stderr)


def execute_cmd2tex(args) -> None:
    """Execute cmd2tex mode (complete pipeline)."""
    print(f"[cmdlog2tex] cmd2tex: {args.input} → {args.output}", file=sys.stderr)

    # Stage 1: Execute commands
    print("[cmdlog2tex] Stage 1: Executing commands...", file=sys.stderr)
    base_input = os.path.splitext(args.input)[0]
    temp_log = command_executor.generate_log_filename(args.input, args.shell)

    returncode, shell_used, log_file = command_executor.execute_commands(
        input_file=args.input, output_log=temp_log, shell=args.shell
    )

    if returncode != 0:
        print(
            f"[cmdlog2tex] Warning: Command exited with code {returncode}",
            file=sys.stderr,
        )

    # Stage 2: Convert to LaTeX
    print("[cmdlog2tex] Stage 2: Converting to LaTeX...", file=sys.stderr)

    output_dir = os.path.dirname(os.path.abspath(args.output)) or "."
    output_tex_name = os.path.basename(args.output)

    result = log2tex.process_log_to_latex(
        log_file=log_file,
        output_tex=output_tex_name,
        output_dir=output_dir,
        format=args.format,
        theme=args.theme,
        language=args.language,
    )

    print(f"[cmdlog2tex] Platform detected: {result['platform_type']}", file=sys.stderr)
    print(f"[cmdlog2tex] Generated: {result['tex_file']}", file=sys.stderr)
    print(f"[cmdlog2tex] Complete pipeline finished", file=sys.stderr)


def main():
    """Main CLI entry point."""
    # Preprocess arguments to support short-option concatenation
    argv = preprocess_argv()

    parser = create_parser()
    args = parser.parse_args(argv)

    # Validate mode selection
    if not args.mode:
        parser.print_help()
        sys.exit(1)

    try:
        # Validate input arguments
        if args.mode == "cmd2log":
            validate_cmd2log_args(args)
        elif args.mode == "log2tex":
            validate_log2tex_args(args)
        elif args.mode == "cmd2tex":
            validate_cmd2log_args(args)  # input is command file

        # Auto-complete missing arguments
        auto_complete_args(args)

        # Execute appropriate mode
        if args.mode == "cmd2log":
            execute_cmd2log(args)
        elif args.mode == "log2tex":
            execute_log2tex(args)
        elif args.mode == "cmd2tex":
            execute_cmd2tex(args)

        print("[cmdlog2tex] Success", file=sys.stderr)
        sys.exit(0)

    except FileNotFoundError as e:
        print(f"[cmdlog2tex] Error: {e}", file=sys.stderr)
        sys.exit(2)
    except ValueError as e:
        print(f"[cmdlog2tex] Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[cmdlog2tex] Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
