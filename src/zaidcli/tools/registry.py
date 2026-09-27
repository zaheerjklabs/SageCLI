"""Tool registry and execution dispatcher with permission management."""

from typing import Dict, List, Any, Optional, Callable, Tuple
from sagecli.tools.base import BaseTool, ToolResult
from sagecli.tools.file_ops import ReadFileTool, WriteFileTool, PatchFileTool, ListDirectoryTool
from sagecli.tools.shell_ops import ExecuteCommandTool
from sagecli.tools.dataset_ops import InspectDatasetTool
from sagecli.tools.test_eval_ops import RunTestsTool
from sagecli.tools.git_ops import GitCheckpointTool, GitDiffTool, GitRollbackTool


class ToolRegistry:
    """Registry managing available agent tools and safe dispatching."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        tools = [
            ReadFileTool(),
            WriteFileTool(),
            PatchFileTool(),
            ListDirectoryTool(),
            ExecuteCommandTool(),
            InspectDatasetTool(),
            RunTestsTool(),
            GitCheckpointTool(),
            GitDiffTool(),
            GitRollbackTool(),
        ]
        for t in tools:
            self.register(t)

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Return list of tool schemas for LLM function calling."""
        return [tool.to_schema() for tool in self._tools.values()]

    def can_execute(
        self,
        tool_name: str,
        mode: str = "Safe",
        permission_callback: Optional[Callable[[str, Dict[str, Any]], bool]] = None,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """Verify if tool execution is permitted in the current mode."""
        tool = self.get_tool(tool_name)
        if not tool:
            return False, f"Unknown tool: '{tool_name}'"

        args = arguments or {}

        # 1. Plan Mode: No destructive actions or shell commands
        if mode.lower() == "plan":
            if tool.is_destructive:
                return False, f"Execution skipped: Tool '{tool_name}' modifies state, but SageCLI is in Plan Mode."

        # 2. Safe Mode: Ask approval if tool requires approval
        if mode.lower() == "safe" and tool.requires_approval_in_safe_mode:
            if permission_callback:
                allowed = permission_callback(tool_name, args)
                if not allowed:
                    return False, f"User denied permission to execute '{tool_name}'."

        return True, ""

    def dispatch(
        self,
        tool_name: str,
        workspace: str,
        arguments: Dict[str, Any],
        mode: str = "Safe",
        permission_callback: Optional[Callable[[str, Dict[str, Any]], bool]] = None,
    ) -> ToolResult:
        """Validate permissions and execute tool."""
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(success=False, output="", error=f"Tool '{tool_name}' not found.")

        can_run, reason = self.can_execute(
            tool_name=tool_name,
            mode=mode,
            permission_callback=permission_callback,
            arguments=arguments,
        )
        if not can_run:
            return ToolResult(success=False, output="", error=reason)

        try:
            return tool.execute(workspace=workspace, **arguments)
        except Exception as exc:
            return ToolResult(success=False, output="", error=f"Unhandled exception in tool '{tool_name}': {exc}")


# Global default registry
default_registry = ToolRegistry()
