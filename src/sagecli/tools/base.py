"""Base tool definitions, schemas, and execution results."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class ToolResult:
    """Standardized tool execution output."""
    success: bool
    output: str
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    def to_string(self) -> str:
        if self.success:
            return self.output
        return f"Error: {self.error or self.output}"


class BaseTool(ABC):
    """Abstract base class for all SageCLI agent tools."""

    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}
    is_destructive: bool = False
    requires_approval_in_safe_mode: bool = False

    def to_schema(self) -> Dict[str, Any]:
        """Convert tool definition to standard OpenAI/Gemini tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }

    @abstractmethod
    def execute(self, workspace: str, **kwargs) -> ToolResult:
        """Execute the tool with supplied arguments within the workspace."""
        pass
