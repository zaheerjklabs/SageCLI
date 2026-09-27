"""Automated testing, evaluation, and test suite execution tool."""

import subprocess
import time
from typing import Optional

from sagecli.tools.base import BaseTool, ToolResult
from sagecli.security import sanitize_text


class RunTestsTool(BaseTool):
    name = "run_tests"
    description = "Run pytest test suite or specific test file to verify project functionality."
    parameters = {
        "type": "object",
        "properties": {
            "test_path": {"type": "string", "description": "Specific test path or file (default: 'tests')"},
            "test_pattern": {"type": "string", "description": "Expression pattern (-k filter, optional)"},
        },
        "required": [],
    }
    is_destructive = False
    requires_approval_in_safe_mode = False

    def execute(self, workspace: str, test_path: str = "tests", test_pattern: Optional[str] = None, **kwargs) -> ToolResult:
        cmd = ["pytest", "-v", test_path]
        if test_pattern:
            cmd.extend(["-k", test_pattern])

        start_time = time.time()
        try:
            process = subprocess.run(
                cmd,
                cwd=workspace,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=180,
            )
            duration = time.time() - start_time
            stdout = sanitize_text(process.stdout or "")
            stderr = sanitize_text(process.stderr or "")

            combined = stdout
            if stderr.strip():
                combined += f"\nSTDERR:\n{stderr}"

            passed = (process.returncode == 0)
            status_str = "PASSED" if passed else "FAILED"
            summary = f"Pytest Suite: {status_str} (Exit code: {process.returncode}, Duration: {duration:.2f}s)\n\n"

            return ToolResult(
                success=passed,
                output=summary + combined,
                error=stderr if not passed and stderr else (stdout if not passed else None),
                data={"returncode": process.returncode, "passed": passed, "duration": duration},
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error="Test run timed out after 180 seconds.",
            )
        except Exception as exc:
            return ToolResult(success=False, output="", error=f"Failed to run tests: {exc}")
