"""Session token usage and cost tracker for SageCLI."""

from dataclasses import dataclass
from typing import Dict, Any

# Estimated cost per million tokens (input / output) in USD
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    # Gemini
    "gemini-3.8-flash": {"input": 0.10, "output": 0.40},
    "gemini-3.7-flash": {"input": 0.10, "output": 0.40},
    "gemini-2.5-flash": {"input": 0.10, "output": 0.40},
    "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-flash-latest": {"input": 0.10, "output": 0.40},
    "gemini-pro-latest": {"input": 1.25, "output": 5.00},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    # OpenAI
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "o3-mini": {"input": 1.10, "output": 4.40},
    "o1": {"input": 15.00, "output": 60.00},
    # Anthropic
    "claude-3-7-sonnet-20250219": {"input": 3.00, "output": 15.00},
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
    # Groq / Ollama / Local
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "deepseek-r1-distill-llama-70b": {"input": 0.75, "output": 0.99},
    "default": {"input": 0.50, "output": 1.50},
}


@dataclass
class UsageTracker:
    """Tracks token consumption, API calls, and estimated session cost."""

    total_requests: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def record_usage(self, prompt_tokens: int, completion_tokens: int) -> None:
        self.total_requests += 1
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens += (prompt_tokens + completion_tokens)

    def estimate_cost(self, model_name: str) -> float:
        """Calculate estimated session cost in USD based on model pricing."""
        # Find closest matching model price
        pricing = MODEL_PRICING.get("default", {"input": 0.50, "output": 1.50})
        for k, v in MODEL_PRICING.items():
            if k in model_name.lower():
                pricing = v
                break

        cost_in = (self.prompt_tokens / 1_000_000) * pricing["input"]
        cost_out = (self.completion_tokens / 1_000_000) * pricing["output"]
        return cost_in + cost_out

    def get_summary(self, model_name: str = "") -> Dict[str, Any]:
        return {
            "requests": self.total_requests,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": self.estimate_cost(model_name),
        }


# Global session tracker
session_tracker = UsageTracker()
