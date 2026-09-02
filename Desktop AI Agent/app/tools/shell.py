"""Asynchronous Shell and Command Execution with live streaming and PTY support."""

import os
import pty
import select
import signal
import subprocess
import threading
import time
import re
from pathlib import Path
from typing import Any, Callable, Dict, Optional


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape sequences from terminal output."""
    ansi_regex = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_regex.sub("", text)


class ShellRunner:
    """Manages command execution in background threads with live line-by-line streaming."""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.current_process: Optional[subprocess.Popen] = None
        self._is_running = False
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._is_running

    def stop_current_process(self) -> bool:
        """Terminate the active running process group gracefully then forcefully."""
        with self._lock:
            if not self.current_process or self.current_process.poll() is not None:
                self._is_running = False
                return False

            proc = self.current_process
            try:
                # Send SIGINT first, then SIGTERM to process group
                pgid = os.getpgid(proc.pid)
                os.killpg(pgid, signal.SIGINT)
                time.sleep(0.1)
                if proc.poll() is None:
                    os.killpg(pgid, signal.SIGTERM)
            except Exception:
                try:
                    proc.terminate()
                except Exception:
                    pass

            self._is_running = False
            return True

    def execute_command(
        self,
        command: str,
        cwd: Optional[Path] = None,
        on_stdout: Optional[Callable[[str], None]] = None,
        on_stderr: Optional[Callable[[str], None]] = None,
        timeout: int = 300,
        env: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Execute command asynchronously via PTY / subpipe and stream stdout line-by-line.
        Returns structured execution result:
        {
            "success": bool,
            "exit_code": int,
            "output": str,
            "error": Optional[str],
            "command": str
        }
        """
        working_dir = (cwd or self.workspace).resolve()
        working_dir.mkdir(parents=True, exist_ok=True)

        exec_env = os.environ.copy()
        exec_env["TERM"] = "xterm-256color"
        exec_env["PYTHONUNBUFFERED"] = "1"
        exec_env["PYTHONPATH"] = f".:{working_dir}:{exec_env.get('PYTHONPATH', '')}"
        if env:
            exec_env.update(env)

        master_fd, slave_fd = pty.openpty()
        output_chunks: list[str] = []

        try:
            with self._lock:
                self._is_running = True
                self.current_process = subprocess.Popen(
                    command,
                    shell=True,
                    stdin=slave_fd,
                    stdout=slave_fd,
                    stderr=slave_fd,
                    cwd=str(working_dir),
                    env=exec_env,
                    preexec_fn=os.setsid,  # Create process group for clean kill
                    close_fds=True,
                )
            os.close(slave_fd)  # Close slave in parent

            start_time = time.time()
            buffer = ""

            # Read from master_fd while process is alive or data remains
            while True:
                # Check for timeout
                if time.time() - start_time > timeout:
                    self.stop_current_process()
                    output_chunks.append("\n[Command timed out after 300 seconds]")
                    break

                # Non-blocking poll for data
                r, _, _ = select.select([master_fd], [], [], 0.05)
                if master_fd in r:
                    try:
                        data = os.read(master_fd, 4096)
                        if not data:
                            break
                        text = data.decode("utf-8", errors="replace")
                        clean_text = strip_ansi_codes(text)
                        buffer += clean_text
                        output_chunks.append(clean_text)

                        # Stream lines if callback provided
                        if "\n" in buffer:
                            lines = buffer.split("\n")
                            for line in lines[:-1]:
                                if on_stdout:
                                    on_stdout(line)
                            buffer = lines[-1]
                    except OSError:
                        # Process closed the PTY
                        break

                # Check if process finished and no more data
                poll_res = self.current_process.poll()
                if poll_res is not None:
                    # Drain any remaining bytes
                    while True:
                        r, _, _ = select.select([master_fd], [], [], 0.02)
                        if not r:
                            break
                        try:
                            data = os.read(master_fd, 4096)
                            if not data:
                                break
                            clean_text = strip_ansi_codes(data.decode("utf-8", errors="replace"))
                            buffer += clean_text
                            output_chunks.append(clean_text)
                        except OSError:
                            break
                    break

            if buffer and on_stdout:
                on_stdout(buffer)

            exit_code = self.current_process.poll() if self.current_process else 0
            if exit_code is None:
                exit_code = -1

            full_output = "".join(output_chunks).strip()
            success = (exit_code == 0)

            return {
                "success": success,
                "exit_code": exit_code,
                "output": full_output,
                "error": None if success else f"Command exited with code {exit_code}",
                "command": command,
            }

        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "output": "".join(output_chunks).strip(),
                "error": str(e),
                "command": command,
            }
        finally:
            try:
                os.close(master_fd)
            except Exception:
                pass
            with self._lock:
                self._is_running = False
                self.current_process = None


def run_command(
    command: str,
    runner: Optional[ShellRunner] = None,
    workspace: Optional[Path] = None,
    on_stdout: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """Execute a Linux command with live output streaming."""
    r = runner or ShellRunner(workspace or Path.cwd())
    return r.execute_command(command=command, on_stdout=on_stdout)
