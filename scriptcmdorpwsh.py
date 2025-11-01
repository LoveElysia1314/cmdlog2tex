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
        """创建日志文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = f"{self.shell_type}_session_{timestamp}.log"
        self.log_file = open(self.log_filename, "w", encoding="utf-8")
        print(f"Recording started. Log file: {self.log_filename}")

    def log_output(self, output):
        """记录输出，但不过滤提示符和命令输入"""
        if not self.recording or not self.log_file or self.log_file.closed:
            return

        # 跳过空行
        if not output.strip():
            return

        # 检测并保存当前的命令提示符
        if self.current_prompt is None and ">" in output:
            # 尝试提取提示符（如 "d:\drzqr\Downloads>"）
            lines = output.split("\n")
            for line in lines:
                if ">" in line and line.endswith(">"):
                    self.current_prompt = line
                    break

        # 如果这是上一个命令的回显（包含提示符和命令），则跳过
        # 但保留提示符本身
        if (
            self.last_command
            and self.current_prompt
            and output.strip().startswith(self.current_prompt)
            and output.strip()[len(self.current_prompt) :].strip() == self.last_command
        ):
            # 这是命令回显，但我们只记录提示符，不记录重复的命令
            self.log_file.write(self.current_prompt + "\n")
            self.log_file.flush()
            print(self.current_prompt)
            self.last_command = None  # 重置，以便下一个命令可以正常处理
            return

        # 直接写入输出，不添加任何前缀
        self.log_file.write(output)
        self.log_file.flush()
        print(output, end="")

    def start_recording(self):
        """开始记录会话"""
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
            # 启动子进程
            self.process = subprocess.Popen(
                shell_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            # 启动输出读取线程
            output_thread = threading.Thread(target=self._read_output)
            output_thread.daemon = True
            output_thread.start()

            print(
                f"{self.shell_type.upper()} session started. Type 'exit' to end recording."
            )
            print("-" * 50)

            # 主循环：读取用户输入并发送到子进程
            while self.recording and self.process.poll() is None:
                try:
                    user_input = input()
                    if user_input.lower() == "exit":
                        break

                    # 保存当前命令用于过滤
                    self.last_command = user_input

                    # 记录用户输入的命令
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
        """读取子进程输出的线程函数"""
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
        """停止记录"""
        if not self.recording:
            return

        self.recording = False

        # 先停止进程
        if self.process and self.process.poll() is None:
            try:
                # 发送退出命令
                if self.shell_type == "cmd":
                    self.process.stdin.write("exit\n")
                elif self.shell_type == "powershell":
                    self.process.stdin.write("exit\n")
                self.process.stdin.flush()

                # 给进程一些时间正常退出
                time.sleep(1)

                # 如果还在运行，强制终止
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

        # 然后关闭日志文件
        if self.log_file and not self.log_file.closed:
            try:
                self.log_file.close()
                print(f"\nRecording stopped. Log file saved: {self.log_filename}")
            except Exception as e:
                print(f"Error closing log file: {e}")


def signal_handler(sig, frame):
    """处理Ctrl+C信号"""
    print("\nReceived interrupt signal. Stopping recording...")
    sys.exit(0)


def main():
    """主函数"""
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
