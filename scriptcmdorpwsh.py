import os
import sys
import time
import threading
import subprocess
import signal
from datetime import datetime


class CleanCommandRecorder:
    def __init__(self, shell_type="cmd"):
        self.shell_type = shell_type.lower()
        self.process = None
        self.recording = False
        self.log_file = None
        self.start_time = None
        self.log_filename = None
        self.last_command = None
        self.current_prompt = None
        self.initial_output_skipped = False
        self.pending_command = None

    def create_log_file(self):
        """Create log file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = f"{self.shell_type}_session_{timestamp}.log"
        self.log_file = open(self.log_filename, "w", encoding="utf-8")
        print(f"Recording started. Log file: {self.log_filename}")

    def log_output(self, output):
        """Log output, but do not filter prompts and command inputs"""
        if not self.recording or not self.log_file or self.log_file.closed:
            return

        # Skip empty lines
        if not output.strip():
            return

        # Detect and save the current command prompt
        if self.current_prompt is None and ">" in output:
            # Try to extract the prompt (e.g., "d:\drzqr\Downloads>")
            lines = output.split("\n")
            for line in lines:
                if ">" in line and line.endswith(">"):
                    self.current_prompt = line
                    break

        # If this is the echo of the previous command (containing prompt and command), skip it
        # But keep the prompt itself
        if (
            self.last_command
            and self.current_prompt
            and output.strip().startswith(self.current_prompt)
            and output.strip()[len(self.current_prompt) :].strip() == self.last_command
        ):
            # This is command echo, but we only record the prompt, not the repeated command
            self.log_file.write(self.current_prompt + "\n")
            self.log_file.flush()
            print(self.current_prompt)
            self.last_command = (
                None  # Reset so the next command can be processed normally
            )
            return

        # Write output directly, without adding any prefix
        self.log_file.write(output)
        self.log_file.flush()
        print(output, end="")

    def start_recording(self):
        """Start recording session"""
        self.create_log_file()
        self.recording = True
        self.start_time = datetime.now()

        if self.shell_type == "cmd":
            shell_cmd = "cmd.exe"
        elif self.shell_type == "powershell":
            shell_cmd = "powershell.exe"
        else:
            print(f"Unsupported shell type: {self.shell_type}")
            return False

        try:
            # Start subprocess
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
            output_thread = threading.Thread(target=self._read_output)
            output_thread.daemon = True
            output_thread.start()

            print(
                f"{self.shell_type.upper()} session started. Type 'exit' to end recording."
            )
            print("-" * 50)

            # Main loop: read user input and send to subprocess
            while self.recording and self.process.poll() is None:
                try:
                    user_input = input()
                    if user_input.lower() == "exit":
                        break

                    # Save current command for filtering
                    self.last_command = user_input

                    # Record user input command
                    if self.log_file and not self.log_file.closed:
                        self.log_file.write(user_input + "\n")
                        self.log_file.flush()

                    self.process.stdin.write(user_input + "\n")
                    self.process.stdin.flush()

                except EOFError:
                    break
                except KeyboardInterrupt:
                    print("\nReceived Ctrl+C, stopping recording...")
                    break
                except Exception as e:
                    print(f"Input error: {e}")
                    break

        except Exception as e:
            print(f"Error starting {self.shell_type}: {e}")
        finally:
            self.stop_recording()

    def _read_output(self):
        """Thread function to read subprocess output"""
        while self.recording and self.process and self.process.poll() is None:
            try:
                output = self.process.stdout.readline()
                if output:
                    self.log_output(output)
            except Exception as e:
                if self.recording:
                    print(f"Output reading error: {e}")
                break

    def stop_recording(self):
        """Stop recording"""
        if not self.recording:
            return

        self.recording = False

        # Stop the process first
        if self.process and self.process.poll() is None:
            try:
                # Send exit command
                if self.shell_type == "cmd":
                    self.process.stdin.write("exit\n")
                elif self.shell_type == "powershell":
                    self.process.stdin.write("exit\n")
                self.process.stdin.flush()

                # Give the process some time to exit normally
                time.sleep(1)

                # If still running, force terminate
                if self.process.poll() is None:
                    self.process.terminate()
                    self.process.wait(timeout=3)
            except (subprocess.TimeoutExpired, OSError):
                try:
                    self.process.kill()
                except:
                    pass
            except Exception as e:
                print(f"Error stopping process: {e}")

        # Then close the log file
        if self.log_file and not self.log_file.closed:
            try:
                self.log_file.close()
                print(f"\nRecording stopped. Log file saved: {self.log_filename}")
            except Exception as e:
                print(f"Error closing log file: {e}")


def signal_handler(sig, frame):
    """Handle Ctrl+C signal"""
    print("\nReceived interrupt signal. Stopping recording...")
    sys.exit(0)


def main():
    """Main function"""
    signal.signal(signal.SIGINT, signal_handler)

    print("Clean Command Line Recorder")
    print("1. CMD")
    print("2. PowerShell")

    choice = input("Select shell type (1 or 2): ").strip()

    if choice == "1":
        shell_type = "cmd"
    elif choice == "2":
        shell_type = "powershell"
    else:
        print("Invalid choice. Defaulting to CMD.")
        shell_type = "cmd"

    recorder = CleanCommandRecorder(shell_type)

    try:
        recorder.start_recording()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        recorder.stop_recording()


if __name__ == "__main__":
    main()
