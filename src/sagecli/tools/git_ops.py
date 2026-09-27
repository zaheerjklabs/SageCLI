"""Git checkpointing, diff inspection, and rollback tools."""

import subprocess
from typing import Optional

from sagecli.tools.base import BaseTool, ToolResult


class GitCheckpointTool(BaseTool):
    name = "git_checkpoint"
    description = "Create a git commit checkpoint before major edits so changes can be audited or rolled back."
    parameters = {
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "Checkpoint commit description"},
        },
        "required": ["message"],
    }
    is_destructive = True
    requires_approval_in_safe_mode = True

    def execute(self, workspace: str, message: str, **kwargs) -> ToolResult:
        try:
            # Check if git is initialized
            status = subprocess.run(["git", "status"], cwd=workspace, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if status.returncode != 0:
                # Initialize git
                subprocess.run(["git", "init"], cwd=workspace, check=True)

            # Stage all files
            subprocess.run(["git", "add", "."], cwd=workspace, check=True)
            
            # Commit
            commit_msg = f"sage(checkpoint): {message}"
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=workspace, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Get latest commit hash
            rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=workspace, stdout=subprocess.PIPE, text=True)
            commit_hash = rev.stdout.strip()

            return ToolResult(
                success=True,
                output=f"✓ Checkpoint created: [{commit_hash}] {message}",
                data={"commit_hash": commit_hash},
            )
        except Exception as exc:
            return ToolResult(success=False, output="", error=f"Git checkpoint failed: {exc}")


class GitDiffTool(BaseTool):
    name = "git_diff"
    description = "Inspect unstaged and staged code modifications since the last checkpoint."
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }
    is_destructive = False
    requires_approval_in_safe_mode = False

    def execute(self, workspace: str, **kwargs) -> ToolResult:
        try:
            diff_res = subprocess.run(["git", "diff", "HEAD"], cwd=workspace, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if diff_res.returncode != 0 or not diff_res.stdout.strip():
                # Check untracked files
                status_res = subprocess.run(["git", "status", "-s"], cwd=workspace, stdout=subprocess.PIPE, text=True)
                if not status_res.stdout.strip():
                    return ToolResult(success=True, output="No pending changes (working tree clean).")
                return ToolResult(success=True, output=f"Pending status:\n{status_res.stdout}")
            return ToolResult(success=True, output=diff_res.stdout)
        except Exception as exc:
            return ToolResult(success=False, output="", error=f"Failed to get git diff: {exc}")


class GitRollbackTool(BaseTool):
    name = "git_rollback"
    description = "Revert uncommitted changes or rollback to a previous checkpoint commit."
    parameters = {
        "type": "object",
        "properties": {
            "commit_hash": {"type": "string", "description": "Specific commit hash to rollback to (default: HEAD discard uncommitted)"},
        },
        "required": [],
    }
    is_destructive = True
    requires_approval_in_safe_mode = True

    def execute(self, workspace: str, commit_hash: Optional[str] = None, **kwargs) -> ToolResult:
        try:
            if commit_hash:
                subprocess.run(["git", "reset", "--hard", commit_hash], cwd=workspace, check=True)
                return ToolResult(success=True, output=f"✓ Rolled back workspace to commit {commit_hash}.")
            else:
                subprocess.run(["git", "restore", "."], cwd=workspace, check=True)
                subprocess.run(["git", "clean", "-fd"], cwd=workspace, check=True)
                return ToolResult(success=True, output="✓ Discarded uncommitted changes.")
        except Exception as exc:
            return ToolResult(success=False, output="", error=f"Rollback failed: {exc}")
