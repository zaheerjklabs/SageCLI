"""OpenAI and OpenAI-compatible LLM Provider (Groq, OpenRouter, vLLM)."""

import json
from typing import List, Dict, Any, Optional, Tuple
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

        try:
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
