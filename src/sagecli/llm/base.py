"""Base classes, message models, and interfaces for LLM providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import json


@dataclass
class ToolCall:
    """Represents a structured tool/function call requested by the model."""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class Message:
    """Represents a chat message in the conversation thread."""
    role: str                       # 'system' | 'user' | 'assistant' | 'tool'
    content: str
    name: Optional[str] = None      # Tool name if role == 'tool'
    tool_call_id: Optional[str] = None
    tool_calls: List[ToolCall] = field(default_factory=list)
    raw_parts: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"role": self.role, "content": self.content}
        if self.name:
            d["name"] = self.name
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        if self.tool_calls:
            d["tool_calls"] = [
                {"id": tc.id, "type": "function", "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)}}
                for tc in self.tool_calls
            ]
        return d


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = "stop"
    raw_response: Optional[Dict[str, Any]] = None
    raw_parts: Optional[List[Dict[str, Any]]] = None


class BaseLLMProvider(ABC):
    """Abstract Base Class for LLM Providers (Gemini, OpenAI, Anthropic, Groq, Ollama, etc.)."""

    def __init__(
        self,
        api_key: str = "",
        model: str = "",
        api_base: str = "",
        timeout_seconds: int = 120,
    ):
        self.api_key = api_key
        self.model = model
        self.api_base = api_base
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    def generate(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """Generate a response synchronously from the model."""
        pass

    @abstractmethod
    def validate_connection(self) -> Tuple[bool, str]:
        """Send a lightweight ping to validate API credentials and connectivity."""
        pass
