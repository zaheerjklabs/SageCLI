"""OpenAI and OpenAI-compatible LLM Provider (Groq, OpenRouter, vLLM)."""

import json
from typing import List, Dict, Any, Optional, Tuple, Callable
import requests

from sagecli.llm.base import BaseLLMProvider, Message, LLMResponse, ToolCall


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API and compatible endpoints."""

    def __init__(
        self,
        api_key: str = "",
        model: str = "gpt-4o",
        api_base: str = "https://api.openai.com/v1",
        timeout_seconds: int = 120,
        extra_headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(
            api_key=api_key,
            model=model or "gpt-4o",
            api_base=api_base.rstrip("/"),
            timeout_seconds=timeout_seconds,
        )
        self.extra_headers = extra_headers or {}

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert messages to OpenAI chat completions format."""
        formatted = []
        for m in messages:
            item = m.to_dict()
            # Clean up empty tool_calls or None fields
            if "tool_calls" in item and not item["tool_calls"]:
                del item["tool_calls"]
            formatted.append(item)
        return formatted

    def generate(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> LLMResponse:
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            **self.extra_headers,
        }

        formatted_messages = self._convert_messages(messages)
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        use_stream = on_chunk is not None
        if use_stream:
            payload["stream"] = True
            payload["stream_options"] = {"include_usage": True}

        try:
            if use_stream:
                resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout_seconds, stream=True)
                if resp.status_code != 200:
                    error_msg = f"OpenAI API Error ({resp.status_code}): {resp.text}"
                    return LLMResponse(content=error_msg, finish_reason="error")

                text_parts = []
                streaming_tool_calls: Dict[int, Dict[str, Any]] = {}
                finish_reason = "stop"
                usage_data: Dict[str, Any] = {}
                model_name = self.model

                for line in resp.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    line = line.strip()
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                    except Exception:
                        continue

                    if "model" in data:
                        model_name = data["model"]
                    if "usage" in data and data["usage"]:
                        usage_data = data["usage"]

                    choices = data.get("choices", [])
                    if not choices:
                        continue
                    choice = choices[0]
                    delta = choice.get("delta", {})
                    if choice.get("finish_reason"):
                        finish_reason = choice["finish_reason"]

                    # Content text chunk
                    content_chunk = delta.get("content")
                    if content_chunk:
                        text_parts.append(content_chunk)
                        if on_chunk:
                            on_chunk(content_chunk)

                    # Tool call chunk
                    tc_chunks = delta.get("tool_calls", [])
                    for tc_chunk in tc_chunks:
                        idx = tc_chunk.get("index", 0)
                        if idx not in streaming_tool_calls:
                            streaming_tool_calls[idx] = {
                                "id": tc_chunk.get("id", f"call_{idx}"),
                                "name": tc_chunk.get("function", {}).get("name", ""),
                                "arguments": "",
                            }
                        else:
                            if tc_chunk.get("id"):
                                streaming_tool_calls[idx]["id"] = tc_chunk["id"]
                            if tc_chunk.get("function", {}).get("name"):
                                streaming_tool_calls[idx]["name"] += tc_chunk["function"]["name"]
                        
                        arg_delta = tc_chunk.get("function", {}).get("arguments", "")
                        if arg_delta:
                            streaming_tool_calls[idx]["arguments"] += arg_delta

                parsed_tool_calls = []
                for idx in sorted(streaming_tool_calls.keys()):
                    tc_data = streaming_tool_calls[idx]
                    args_str = tc_data["arguments"]
                    try:
                        args = json.loads(args_str) if args_str else {}
                    except Exception:
                        args = {"raw": args_str}
                    parsed_tool_calls.append(ToolCall(
                        id=tc_data["id"] or f"call_{idx}",
                        name=tc_data["name"],
                        arguments=args,
                    ))

                return LLMResponse(
                    content="".join(text_parts),
                    tool_calls=parsed_tool_calls,
                    model=model_name,
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0),
                    finish_reason=finish_reason,
                )

            else:
                resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout_seconds)
                if resp.status_code != 200:
                    error_msg = f"OpenAI API Error ({resp.status_code}): {resp.text}"
                    return LLMResponse(content=error_msg, finish_reason="error")

                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    return LLMResponse(content="", finish_reason="empty")

                choice = choices[0]
                msg = choice.get("message", {})
                content = msg.get("content") or ""

                raw_tool_calls = msg.get("tool_calls", [])
                parsed_tool_calls = []

                for tc in raw_tool_calls:
                    fn = tc.get("function", {})
                    args_str = fn.get("arguments", "{}")
                    try:
                        args = json.loads(args_str) if isinstance(args_str, str) else args_str
                    except Exception:
                        args = {"raw": args_str}

                    parsed_tool_calls.append(ToolCall(
                        id=tc.get("id", f"call_{len(parsed_tool_calls)}"),
                        name=fn.get("name", ""),
                        arguments=args,
                    ))

                usage = data.get("usage", {})
                return LLMResponse(
                    content=content,
                    tool_calls=parsed_tool_calls,
                    model=data.get("model", self.model),
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                    finish_reason=choice.get("finish_reason", "stop"),
                    raw_response=data,
                )
        except Exception as e:
            return LLMResponse(content=f"OpenAI connection error: {e}", finish_reason="error")

    def validate_connection(self) -> Tuple[bool, str]:
        """Validate connection with minimal request."""
        if not self.api_key and "localhost" not in self.api_base:
            return False, "API key is required."
        
        test_messages = [Message(role="user", content="Ping")]
        response = self.generate(test_messages)
        if response.finish_reason == "error":
            return False, response.content
        return True, "Successfully connected to OpenAI-compatible provider."
