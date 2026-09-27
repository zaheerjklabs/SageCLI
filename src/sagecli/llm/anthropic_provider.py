"""Anthropic Claude LLM Provider with tool calling support."""

from typing import List, Dict, Any, Optional, Tuple, Callable
import json
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
        on_chunk: Optional[Callable[[str], None]] = None,
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

        use_stream = on_chunk is not None
        if use_stream:
            payload["stream"] = True

        try:
            if use_stream:
                resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout_seconds, stream=True)
                if resp.status_code != 200:
                    error_msg = f"Anthropic API Error ({resp.status_code}): {resp.text}"
                    return LLMResponse(content=error_msg, finish_reason="error")

                text_parts = []
                tool_calls_dict: Dict[int, Dict[str, Any]] = {}
                finish_reason = "end_turn"
                prompt_tokens = 0
                completion_tokens = 0
                current_event = None

                for line in resp.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    line = line.strip()
                    if line.startswith("event: "):
                        current_event = line[7:].strip()
                        continue
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    try:
                        data = json.loads(data_str)
                    except Exception:
                        continue

                    event_type = data.get("type", current_event)
                    if event_type == "message_start":
                        msg = data.get("message", {})
                        usage = msg.get("usage", {})
                        prompt_tokens = usage.get("input_tokens", 0)
                    elif event_type == "content_block_start":
                        idx = data.get("index", 0)
                        cb = data.get("content_block", {})
                        if cb.get("type") == "tool_use":
                            tool_calls_dict[idx] = {
                                "id": cb.get("id", f"call_{idx}"),
                                "name": cb.get("name", ""),
                                "arguments": "",
                            }
                    elif event_type == "content_block_delta":
                        idx = data.get("index", 0)
                        delta = data.get("delta", {})
                        d_type = delta.get("type")
                        if d_type == "text_delta":
                            text = delta.get("text", "")
                            text_parts.append(text)
                            if on_chunk:
                                on_chunk(text)
                        elif d_type == "input_json_delta":
                            partial = delta.get("partial_json", "")
                            if idx in tool_calls_dict:
                                tool_calls_dict[idx]["arguments"] += partial
                    elif event_type == "message_delta":
                        delta = data.get("delta", {})
                        finish_reason = delta.get("stop_reason", finish_reason)
                        usage = data.get("usage", {})
                        completion_tokens = usage.get("output_tokens", 0)

                parsed_tool_calls = []
                for idx in sorted(tool_calls_dict.keys()):
                    t = tool_calls_dict[idx]
                    try:
                        args = json.loads(t["arguments"]) if t["arguments"] else {}
                    except Exception:
                        args = {"raw": t["arguments"]}
                    parsed_tool_calls.append(ToolCall(
                        id=t["id"],
                        name=t["name"],
                        arguments=args,
                    ))

                return LLMResponse(
                    content="".join(text_parts),
                    tool_calls=parsed_tool_calls,
                    model=self.model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    finish_reason=finish_reason,
                )
            else:
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
