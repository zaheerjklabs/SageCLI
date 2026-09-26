"""Provider factory for instantiating LLM providers."""

from typing import Optional
from sagecli.config import SageConfig, PROVIDER_DEFAULTS
from sagecli.llm.base import BaseLLMProvider
from sagecli.llm.gemini_provider import GeminiProvider
from sagecli.llm.openai_provider import OpenAIProvider
from sagecli.llm.anthropic_provider import AnthropicProvider


def create_llm_provider(config: Optional[SageConfig] = None) -> BaseLLMProvider:
    """Instantiate appropriate LLM provider based on active configuration."""
    cfg = config or SageConfig.load()
    provider_name = (cfg.provider or "gemini").lower()
    
    # Retrieve active API key
    api_key = cfg.api_key or cfg.provider_keys.get(provider_name, "")
    api_base = cfg.api_base or PROVIDER_DEFAULTS.get(provider_name, {}).get("api_base", "")
    model = cfg.model or PROVIDER_DEFAULTS.get(provider_name, {}).get("default_model", "")
    timeout = cfg.timeout_seconds

    if provider_name == "gemini":
        return GeminiProvider(api_key=api_key, model=model, api_base=api_base, timeout_seconds=timeout)
    
    elif provider_name == "anthropic":
        return AnthropicProvider(api_key=api_key, model=model, api_base=api_base, timeout_seconds=timeout)
    
    elif provider_name == "openai":
        return OpenAIProvider(api_key=api_key, model=model, api_base=api_base, timeout_seconds=timeout)
    
    elif provider_name == "groq":
        return OpenAIProvider(
            api_key=api_key,
            model=model or "llama-3.3-70b-versatile",
            api_base=api_base or "https://api.groq.com/openai/v1",
            timeout_seconds=timeout,
        )
    
    elif provider_name == "openrouter":
        return OpenAIProvider(
            api_key=api_key,
            model=model or "deepseek/deepseek-r1",
            api_base=api_base or "https://openrouter.ai/api/v1",
            timeout_seconds=timeout,
            extra_headers={"HTTP-Referer": "https://github.com/SageCLI", "X-Title": "SageCLI"},
        )
    
    elif provider_name == "ollama":
        return OpenAIProvider(
            api_key="ollama",
            model=model or "llama3.2:latest",
            api_base=f"{api_base.rstrip('/')}/v1" if not api_base.endswith("/v1") else api_base,
            timeout_seconds=timeout,
        )
    
    else:  # Custom or fallback
        return OpenAIProvider(
            api_key=api_key,
            model=model,
            api_base=api_base,
            timeout_seconds=timeout,
        )
