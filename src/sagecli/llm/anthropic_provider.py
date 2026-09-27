"""Anthropic Claude LLM Provider with tool calling support."""

from typing import List, Dict, Any, Optional, Tuple
import requests

from sagecli.llm.base import BaseLLMProvider, Message, LLMResponse, ToolCall


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Messages API implementation."""

    def __init__(
        self,
        api_key: str = "",
        model: str = "claude-3-7-sonnet-20250219",
        api_base: str = "https://api.anthropic.com/v1",
        timeout_seconds: int = 120,
    ):
        super().__init__(
            api_key=api_key,
            model=model or "claude-3-7-sonnet-20250219",
            api_base=api_base.rstrip("/"),
            timeout_seconds=timeout_seconds,
        )

    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert OpenAI tool schema to Anthropic format."""
        anthropic_tools = []
        for t in tools:
            fn = t.get("function", t)
            anthropic_tools.append({
                "name": fn.get("name"),
                "description": fn.get("description", ""),
                "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
            })
        return anthropic_tools

    def _convert_messages(self, messages: List[Message]) -> Tuple[Optional[str], List[Dict[str, Any]]]:
        """Convert Message list to Anthropic system string and messages list."""
        system_content = None
        formatted_messages = []

        for msg in messages:
            if msg.role == "system":
                system_content = msg.content
            elif msg.role == "user":
                formatted_messages.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                content_blocks: List[Dict[str, Any]] = []
                if msg.content:
                    content_blocks.append({"type": "text", "text": msg.content})
                for tc in msg.tool_calls:
                    content_blocks.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.arguments,
                    })
                formatted_messages.append({
                    "role": "assistant",
                    "content": content_blocks if content_blocks else msg.content,
                })
            elif msg.role == "tool":
                formatted_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id or "tool_call",
                        "content": msg.content,
                    }]
                })

        return system_content, formatted_messages

    def generate(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        url = f"{self.api_base}/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        system_prompt, formatted_messages = self._convert_messages(messages)
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": 4096,
            "temperature": temperature,
        }

        if system_prompt:
            payload["system"] = system_prompt

        if tools:
            payload["tools"] = self._convert_tools(tools)

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout_seconds)
            if resp.status_code != 200:
                error_msg = f"Anthropic API Error ({resp.status_code}): {resp.text}"
                return LLMResponse(content=error_msg, finish_reason="error")

            data = resp.json()
            content_blocks = data.get("content", [])
            
            text_blocks = []
            tool_calls = []

            for block in content_blocks:
                b_type = block.get("type")
                if b_type == "text":
                    text_blocks.append(block.get("text", ""))
                elif b_type == "tool_use":
                    tool_calls.append(ToolCall(
                        id=block.get("id", f"call_{len(tool_calls)}"),
                        name=block.get("name", ""),
                        arguments=block.get("input", {}),
                    ))

            usage = data.get("usage", {})
            return LLMResponse(
                content="".join(text_blocks),
                tool_calls=tool_calls,
                model=data.get("model", self.model),
                prompt_tokens=usage.get("input_tokens", 0),
                completion_tokens=usage.get("output_tokens", 0),
                total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                finish_reason=data.get("stop_reason", "end_turn"),
                raw_response=data,
            )
        except Exception as e:
            return LLMResponse(content=f"Anthropic connection error: {e}", finish_reason="error")

    def validate_connection(self) -> Tuple[bool, str]:
        """Validate Anthropic credentials."""
        if not self.api_key:
            return False, "Anthropic API key is empty."
        
        test_messages = [Message(role="user", content="Ping")]
        response = self.generate(test_messages)
        if response.finish_reason == "error":
            return False, response.content
        return True, "Successfully connected to Anthropic Claude."
