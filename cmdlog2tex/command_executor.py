#!/usr/bin/env python3
"""
command_executor - Execute commands and capture logs

Handles command execution and log recording for multiple platforms.
Output: Platform-specific log file (.pwsh.log / .cmd.log / .ansilog)
"""

import os
import sys
import subprocess
import platform
import tempfile
import threading
import time
from typing import Tuple, Optional
from contextlib import contextmanager


@contextmanager
def temp_file_context(suffix: str = "", content: str = ""):
    """Context manager for temporary file creation and cleanup."""
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False, suffix=suffix
        ) as tmp:
            if content:
                tmp.write(content)
            temp_path = tmp.name
        yield temp_path
    finally:
        if temp_path:
            try:
                os.unlink(temp_path)
            except OSError:
                pass  # Silently ignore cleanup errors


def detect_available_shell() -> str:
    """
    Detect if PowerShell is available on Windows.

    Returns:
        'powershell' if available, 'cmd' otherwise
    """
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", "exit"],
            capture_output=True,
            timeout=2,
        )
        return "powershell"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "cmd"


def get_default_shell(requested_shell: Optional[str] = None) -> str:
    """
    Get the default shell based on platform and availability.

    Args:
        requested_shell: User-specified shell ('powershell' | 'cmd' | 'bash')

    Returns:
        Shell type to use
    """
    if requested_shell:
        return requested_shell

    system = platform.system()
    if system == "Windows":
        return detect_available_shell()
    else:
        return "bash"


def generate_log_filename(input_file: str, shell: Optional[str] = None) -> str:
    """
    Generate output log filename based on input file and shell type.

    Args:
        input_file: Input commands file path
        shell: Shell type (optional, for explicit naming)

    Returns:
        Generated log filename with platform-specific suffix
    """
    base_path = os.path.splitext(input_file)[0]

    # On Windows, both cmd and PowerShell use .txt suffix (unified)
    # On Unix-like systems, bash uses .ansilog
    system = platform.system()
    if system == "Windows":
        return f"{base_path}.txt"
    else:  # Linux/macOS
        return f"{base_path}.ansilog"


class WindowsInteractiveRecorder:
    """
    Unified interactive session recorder for Windows (cmd and PowerShell).

    Uses subprocess.Popen to launch an interactive shell session and records
    both commands and outputs in real-time, automatically detecting and
    preserving the actual prompt from the shell.
    """

    def __init__(self, shell_type: str, commands_list: list, log_file: str):
        self.shell_type = shell_type.lower()  # 'cmd' or 'powershell'
        self.commands_list = commands_list
        self.log_file_path = log_file
        self.log_file = None
        self.process = None
        self.recording = False
        self.current_prompt = None
        self.last_command = None
        self.final_returncode = 0
        self.command_index = 0

    def open_log_file(self):
        """Open log file for writing."""
        self.log_file = open(self.log_file_path, "w", encoding="utf-8")

    def close_log_file(self):
        """Close log file."""
        if self.log_file and not self.log_file.closed:
            self.log_file.close()

    def log_output(self, output: str):
        """
        Log output to file and stdout.

        Automatically detects and preserves the shell prompt, avoids
        recording duplicate command echoes.

        Args:
            output: Output string from the shell
        """
        if not self.recording or not self.log_file or self.log_file.closed:
            return

        # Skip empty lines
        if not output.strip():
            return

        # Detect and save current prompt (e.g., "C:\Users\Username>" or "PS C:\>")
        if self.current_prompt is None and ">" in output:
            lines = output.split("\n")
            for line in lines:
                if ">" in line and line.rstrip().endswith(">"):
                    # Found a prompt-like line
                    self.current_prompt = line.rstrip()
                    break

        # Avoid recording command echo (when output shows command that was just sent)
        if (
            self.last_command
            and self.current_prompt
            and output.strip().startswith(self.current_prompt)
        ):
            # Check if this is just echoing the command
            after_prompt = output.strip()[len(self.current_prompt) :].strip()
            if after_prompt == self.last_command:
                # Just record the prompt, skip the duplicate command
                self.log_file.write(self.current_prompt + "\n")
                self.log_file.flush()
                print(self.current_prompt)
                self.last_command = None
                return

        # Write output to both log file and stdout
        self.log_file.write(output)
        self.log_file.flush()
        print(output, end="")

    def read_output_thread(self):
        """
        Thread function to read subprocess output in real-time.
        Runs in background to capture output while main thread handles input.
        """
        while self.recording and self.process and self.process.poll() is None:
            try:
                output = self.process.stdout.readline()
                if output:
                    self.log_output(output)
            except Exception as e:
                if self.recording:
                    print(f"[Error reading output]: {e}", file=sys.stderr)
                break

    def execute(self) -> int:
        """
        Execute commands in an interactive shell session and record the output.

        Returns:
            Return code from the last command
        """
        self.open_log_file()
        self.recording = True

        # Determine shell executable
        if self.shell_type == "cmd":
            shell_cmd = "cmd.exe"
        elif self.shell_type == "powershell":
            shell_cmd = "powershell.exe"
        else:
            print(f"[Error] Unsupported shell type: {self.shell_type}", file=sys.stderr)
            self.close_log_file()
            return 1

        try:
            # Start interactive shell process with pipes
            # NOTE: Do not specify encoding here - let Python auto-detect system default encoding
            # This prevents Chinese character corruption on Windows (GBK/CP936 default encoding)
            self.process = subprocess.Popen(
                shell_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            # Start output reading thread
            output_thread = threading.Thread(target=self.read_output_thread)
            output_thread.daemon = True
            output_thread.start()

            # Give shell time to start and show initial prompt
            time.sleep(0.5)

            # NOTE: Do not send encoding setup commands (chcp 65001 or UTF-8 encoding)
            # Keep shell in default system encoding to match subprocess pipe encoding
            # This prevents Chinese character corruption on Windows systems

            # Execute each command
            for self.command_index, cmd in enumerate(self.commands_list):
                cmd = cmd.rstrip("\r\n")
                if not cmd.strip():
                    continue

                if not self.recording or self.process.poll() is not None:
                    break

                # Save command for duplicate detection
                self.last_command = cmd

                # Log the command to file
                self.log_file.write(cmd + "\n")
                self.log_file.flush()

                # Send command to shell
                try:
                    self.process.stdin.write(cmd + "\n")
                    self.process.stdin.flush()
                except (BrokenPipeError, OSError):
                    break

                # Give some time for command to execute
                time.sleep(0.1)

            # Wait a bit for final output
            time.sleep(0.5)

            # Send exit command
            try:
                self.process.stdin.write("exit\n")
                self.process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass

            # Wait for process to finish
            self.recording = False
            try:
                self.process.wait(timeout=3)
                self.final_returncode = self.process.returncode or 0
            except subprocess.TimeoutExpired:
                self.process.terminate()
                try:
                    self.process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
                self.final_returncode = 1

            return self.final_returncode

        except Exception as e:
            print(f"[Error] Failed to execute shell: {e}", file=sys.stderr)
            self.final_returncode = 1
            return 1
        finally:
            self.recording = False
            if self.process and self.process.poll() is None:
                try:
                    self.process.terminate()
                    self.process.wait(timeout=1)
                except:
                    try:
                        self.process.kill()
                    except:
                        pass
            self.close_log_file()


def execute_with_windows_shell(
    shell_type: str, commands_list: list, log_file: str
) -> int:
    """
    Execute commands using unified Windows shell recorder (cmd or PowerShell).

    This function uses interactive subprocess.Popen to create a real shell session,
    automatically detects the shell prompt, and records both commands and outputs
    exactly as they appear in a terminal.

    Args:
        shell_type: 'cmd' or 'powershell'
        commands_list: List of command strings to execute
        log_file: Path where log will be saved

    Returns:
        Return code from shell execution
    """
    recorder = WindowsInteractiveRecorder(shell_type, commands_list, log_file)
    return recorder.execute()


def execute_with_bash(commands_file: str, log_file: str) -> int:
    """
    Execute commands using Bash with script command.

    Uses 'script' command with bash interactive shell to record the session
    while executing commands from a file via stdin redirection.

    Args:
        commands_file: Path to file with commands
        log_file: Path where log will be saved

    Returns:
        Return code from bash execution
    """
    # Execute using script with bash interactive mode
    # This runs: script -c 'bash --login -i < "commands_file"' log_file
    # The bash --login -i flags provide interactive shell with login initialization
    # This preserves the colored prompt and proper shell environment
    cmd_str = f'bash --login -i < "{commands_file}"'

    result = subprocess.run(
        ["script", "-c", cmd_str, log_file],
        text=True,
        stdout=None,
        stderr=None,  # Don't redirect output - let it display directly in terminal
        # IMPORTANT: Use os.environ.copy() to preserve original TERM value for colored prompts.
        # Setting TERM to "xterm" breaks color support. Use original TERM for proper color display.
        env=os.environ.copy(),
    )

    return result.returncode


def execute_commands(
    input_file: str, output_log: Optional[str] = None, shell: Optional[str] = None
) -> Tuple[int, str, str]:
    """
    Execute command stream from file and capture logs.

    Main entry point for command execution.

    Args:
        input_file: Path to file containing commands (one per line)
        output_log: Output log file path (auto-generated if None)
        shell: Shell type ('powershell' | 'cmd' | 'bash' | None for auto)

    Returns:
        (return_code, shell_used, log_file_path)

    Raises:
        FileNotFoundError: If input_file doesn't exist
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Auto-generate output filename if not specified
    if output_log is None:
        output_log = generate_log_filename(input_file, shell)

    # Make paths absolute
    input_file = os.path.abspath(input_file)
    output_log = os.path.abspath(output_log)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_log) or "."
    os.makedirs(output_dir, exist_ok=True)

    # Read commands from file
    with open(input_file, "r", encoding="utf-8", errors="surrogateescape") as f:
        lines = f.readlines()

    # Filter out empty lines
    commands_list = [ln for ln in lines if ln.strip()]

    # Handle empty command file
    if not commands_list:
        open(output_log, "w", encoding="utf-8").close()
        return 0, get_default_shell(shell), output_log

    # Determine platform
    system = platform.system()
    shell_to_use = shell or get_default_shell()

    # Execute based on platform and shell
    if system == "Windows":
        # Use unified Windows shell recorder for both cmd and PowerShell
        returncode = execute_with_windows_shell(shell_to_use, commands_list, output_log)
    else:  # Linux/macOS
        # Create temp file with commands (no shebang - script -c already runs bash)
        bash_content = "".join(commands_list)
        with temp_file_context(suffix=".sh", content=bash_content) as tmp:
            returncode = execute_with_bash(tmp, output_log)

    return returncode, shell_to_use, output_log
