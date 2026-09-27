"""SageCLI tool suite for ML/DL autonomous engineering."""

from sagecli.tools.base import BaseTool, ToolResult
from sagecli.tools.file_ops import ReadFileTool, WriteFileTool, PatchFileTool, ListDirectoryTool
from sagecli.tools.shell_ops import ExecuteCommandTool
from sagecli.tools.dataset_ops import InspectDatasetTool
from sagecli.tools.test_eval_ops import RunTestsTool
from sagecli.tools.git_ops import GitCheckpointTool, GitDiffTool, GitRollbackTool
from sagecli.tools.registry import ToolRegistry, default_registry

__all__ = [
    "BaseTool",
    "ToolResult",
    "ReadFileTool",
    "WriteFileTool",
    "PatchFileTool",
    "ListDirectoryTool",
    "ExecuteCommandTool",
    "InspectDatasetTool",
    "RunTestsTool",
    "GitCheckpointTool",
    "GitDiffTool",
    "GitRollbackTool",
    "ToolRegistry",
    "default_registry",
]
