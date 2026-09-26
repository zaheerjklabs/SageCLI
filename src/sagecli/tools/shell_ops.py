"""Shell command execution tool with timeout, sandboxing, and output capture."""

import subprocess
import time

from sagecli.tools.base import BaseTool, ToolResult
from sagecli.security import check_command_safety, sanitize_text


class ExecuteCommandTool(BaseTool):
    name = "execute_command"
    description = "Execute a shell command or python script in the workspace. Returns stdout, stderr, and exit code."
    parameters = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The shell command string to execute (e.g. 'python train.py', 'pip install ...')"},
            "timeout_seconds": {"type": "integer", "description": "Timeout in seconds (default: 120)"},
        },
        "required": ["command"],
    }
    is_destructive = True
    requires_approval_in_safe_mode = True

    def execute(self, workspace: str, command: str, timeout_seconds: int = 120, **kwargs) -> ToolResult:
        is_safe, warn_msg = check_command_safety(command)
        if not is_safe:
            return ToolResult(
                success=False,
                output="",
                error=f"Command rejected for safety: {warn_msg}",
            )

        start_time = time.time()
        try:
            process = subprocess.run(
                command,
                shell=True,
                cwd=workspace,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_seconds,
            )
            duration = time.time() - start_time
            stdout_sanitized = sanitize_text(process.stdout or "")
            stderr_sanitized = sanitize_text(process.stderr or "")

            out_parts = []
            if stdout_sanitized.strip():
                out_parts.append(f"STDOUT:\n{stdout_sanitized}")
            if stderr_sanitized.strip():
                out_parts.append(f"STDERR:\n{stderr_sanitized}")
            
            summary = f"Exit Code: {process.returncode} (Duration: {duration:.2f}s)"
            full_output = f"{summary}\n" + "\n".join(out_parts) if out_parts else summary

            return ToolResult(
                success=(process.returncode == 0),
                output=full_output,
                error=stderr_sanitized if process.returncode != 0 else None,
                data={"returncode": process.returncode, "duration": duration},
            )
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return ToolResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout_seconds} seconds.",
                data={"duration": duration},
            )
        except Exception as exc:
            return ToolResult(success=False, output="", error=f"Execution error: {exc}")
