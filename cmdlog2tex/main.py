#!/usr/bin/env python3
"""
cmdlog2tex - Main entry point

This is the unified entry point for all three commands (cmd2log, log2tex, cmd2tex).
It automatically detects which command was called and injects the appropriate mode.
"""

import sys
import os
from .cli import main as cli_main


def main():
    """Main entry point that injects the command mode based on sys.argv[0]."""
    # Detect which command was called
    program_name = os.path.basename(sys.argv[0])

    # Inject the mode as the first argument
    if "cmd2log" in program_name:
        sys.argv.insert(1, "cmd2log")
    elif "log2tex" in program_name:
        sys.argv.insert(1, "log2tex")
    elif "cmd2tex" in program_name:
        sys.argv.insert(1, "cmd2tex")
    # If called directly as 'cmdlog2tex', mode must be specified by user

    cli_main()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[cmdlog2tex] Interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"[cmdlog2tex] Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
