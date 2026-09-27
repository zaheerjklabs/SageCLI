"""Google Gemini LLM Provider supporting tool calling and streaming."""

import json
from typing import List, Dict, Any, Optional, Tuple
import requests

from sagecli.llm.base import BaseLLMProvider, Message, LLMResponse, ToolCall


class GeminiProvider(BaseLLMProvider):
    """Google Gemini REST API implementation."""

    def __init__(
        self,
        api_key: str = "",
        model: str = "gemini-2.5-pro",
        api_base: str = "https://generativelanguage.googleapis.com",
        timeout_seconds: int = 120,
    ):
        super().__init__(
            api_key=api_key,
            model=model or "gemini-2.5-pro",
            api_base=api_base or "https://generativelanguage.googleapis.com",
            timeout_seconds=timeout_seconds,
        )

    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert standard OpenAI tool declarations into Gemini functionDeclarations format."""
        function_declarations = []
        for t in tools:
            fn = t.get("function", t)
            decl = {
                "name": fn.get("name"),
                "description": fn.get("description", ""),
                "parameters": fn.get("parameters", {"type": "object", "properties": {}}),
            }
            function_declarations.append(decl)
        return [{"functionDeclarations": function_declarations}]

    def _convert_messages(self, messages: List[Message]) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """Convert standard Message list to Gemini contents and system_instruction."""
        system_instruction = None
        contents = []

        for msg in messages:
            if msg.role == "system":
                system_instruction = {
                    "parts": [{"text": msg.content}]
                }
            elif msg.role == "user":
                contents.append({
                    "role": "user",
                    "parts": [{"text": msg.content}]
                })
            elif msg.role == "assistant":
                if msg.raw_parts:
                    contents.append({"role": "model", "parts": msg.raw_parts})
                else:
                    parts: List[Dict[str, Any]] = []
                    if msg.content:
                        parts.append({"text": msg.content})
                    for tc in msg.tool_calls:
                        parts.append({
                            "functionCall": {
                                "name": tc.name,
                                "args": tc.arguments,
                            }
                        })
                    if not parts:
                        parts.append({"text": ""})
                    contents.append({"role": "model", "parts": parts})
            elif msg.role == "tool":
                # Tool result in Gemini format
                try:
                    response_obj = json.loads(msg.content)
                except Exception:
                    response_obj = {"result": msg.content}
                
                contents.append({
                    "role": "user",
                    "parts": [{
                        "functionResponse": {
                            "name": msg.name or "tool",
                            "response": response_obj,
                        }
                    }]
                })

        return system_instruction, contents

    def generate(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        system_instruction, contents = self._convert_messages(messages)
        
        # Clean model identifier
        model_name = self.model
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"

        url = f"{self.api_base}/v1beta/{model_name}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            }
        }

        if system_instruction:
            payload["systemInstruction"] = system_instruction

        if tools:
            payload["tools"] = self._convert_tools(tools)

        import time
        import re

        def _get_retry_delay(resp_text: str, attempt_idx: int) -> float:
            try:
                err_data = json.loads(resp_text)
                for detail in err_data.get("error", {}).get("details", []):
                    if "retryDelay" in detail:
                        val = float(re.sub(r"[^\d.]", "", detail["retryDelay"]))
                        return min(val + 0.5, 30.0)
            except Exception:
                pass
            match = re.search(r"retry in (\d+(?:\.\d+)?)s", resp_text, re.IGNORECASE)
            if match:
                try:
                    return min(float(match.group(1)) + 0.5, 30.0)
                except Exception:
                    pass
            return 2.0 * (attempt_idx + 1)

        max_retries = 3
        for attempt in range(max_retries + 1):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout_seconds)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        return LLMResponse(content="", finish_reason="empty")

                    cand = candidates[0]
                    parts = cand.get("content", {}).get("parts", [])
                    
                    text_parts = []
                    tool_calls = []

                    for i, part in enumerate(parts):
                        if "text" in part:
                            text_parts.append(part["text"])
                        if "functionCall" in part:
                            fc = part["functionCall"]
                            tool_calls.append(ToolCall(
                                id=f"call_gemini_{i}",
                                name=fc.get("name", ""),
                                arguments=fc.get("args", {}),
                            ))

                    usage = data.get("usageMetadata", {})
                    return LLMResponse(
                        content="".join(text_parts),
                        tool_calls=tool_calls,
                        model=self.model,
                        prompt_tokens=usage.get("promptTokenCount", 0),
                        completion_tokens=usage.get("candidatesTokenCount", 0),
                        total_tokens=usage.get("totalTokenCount", 0),
                        finish_reason=cand.get("finishReason", "stop"),
                        raw_response=data,
                        raw_parts=parts,
                    )
                
                # If 503 (high demand) or 429 (rate limit), retry with dynamic backoff
                if resp.status_code in (503, 429) and attempt < max_retries:
                    delay = _get_retry_delay(resp.text, attempt)
                    time.sleep(delay)
                    continue

                error_msg = f"Gemini API Error ({resp.status_code}): {resp.text}"
                if resp.status_code == 429:
                    error_msg += "\n\n💡 [bold]Quota Tip:[/] This model reached its per-minute/daily quota. You can wait a moment or switch models with [bold]/model gemini-3.5-flash[/] or [bold]/model gemini-3.1-flash-lite[/]."
                return LLMResponse(content=error_msg, finish_reason="error")

            except Exception as e:
                if attempt < max_retries:
                    time.sleep(2.0)
                    continue
                return LLMResponse(content=f"Gemini connection error: {e}", finish_reason="error")

    def validate_connection(self) -> Tuple[bool, str]:
        """Validate API key with a test call."""
        if not self.api_key:
            return False, "Gemini API key is empty."
        
        test_messages = [Message(role="user", content="Ping")]
        response = self.generate(test_messages)
        if response.finish_reason == "error":
            return False, response.content
        return True, "Successfully connected to Google Gemini."
