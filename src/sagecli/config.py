"""Configuration and runtime state management for SageCLI."""

import json
import os
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any

from sagecli import __version__

# Default supported providers and default recommended models
PROVIDER_DEFAULTS = {
    "gemini": {
        "name": "Google Gemini",
        "default_model": "gemini-3.7-flash",
        "available_models": [
            "gemini-3.7-flash",
            "gemini-3.5-flash",
            "gemini-3.8-flash",
            "gemini-flash-latest",
            "gemini-pro-latest",
            "gemini-3.1-flash-lite",
        ],
        "env_var": "GEMINI_API_KEY",
        "api_base": "https://generativelanguage.googleapis.com",
    },
    "openai": {
        "name": "OpenAI",
        "default_model": "gpt-4o",
        "available_models": [
            "gpt-4o",
            "gpt-4o-mini",
            "o3-mini",
            "o1",
        ],
        "env_var": "OPENAI_API_KEY",
        "api_base": "https://api.openai.com/v1",
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "default_model": "claude-3-7-sonnet-20250219",
        "available_models": [
            "claude-3-7-sonnet-20250219",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
        ],
        "env_var": "ANTHROPIC_API_KEY",
        "api_base": "https://api.anthropic.com/v1",
    },
    "groq": {
        "name": "Groq",
        "default_model": "llama-3.3-70b-versatile",
        "available_models": [
            "llama-3.3-70b-versatile",
            "deepseek-r1-distill-llama-70b",
            "mixtral-8x7b-32768",
        ],
        "env_var": "GROQ_API_KEY",
        "api_base": "https://api.groq.com/openai/v1",
    },
    "openrouter": {
        "name": "OpenRouter",
        "default_model": "deepseek/deepseek-r1",
        "available_models": [
            "deepseek/deepseek-r1",
            "anthropic/claude-3.7-sonnet",
            "openai/gpt-4o",
            "meta-llama/llama-3.3-70b-instruct",
        ],
        "env_var": "OPENROUTER_API_KEY",
        "api_base": "https://openrouter.ai/api/v1",
    },
    "ollama": {
        "name": "Ollama (Local)",
        "default_model": "llama3.2:latest",
        "available_models": [
            "llama3.2:latest",
            "deepseek-r1:latest",
            "qwen2.5-coder:latest",
            "mistral:latest",
        ],
        "env_var": "OLLAMA_BASE_URL",
        "api_base": "http://localhost:11434",
    },
    "custom": {
        "name": "Custom OpenAI-compatible",
        "default_model": "default",
        "available_models": ["default"],
        "env_var": "CUSTOM_API_KEY",
        "api_base": "http://localhost:8000/v1",
    },
}


def get_global_config_path() -> Path:
    """Return ~/.sage/config.json path."""
    home = Path.home()
    sage_dir = home / ".sage"
    sage_dir.mkdir(parents=True, exist_ok=True)
    return sage_dir / "config.json"


def get_project_config_path(workspace: Optional[str] = None) -> Path:
    """Return .sage/config.json path in current workspace."""
    ws = Path(workspace or os.getcwd()).resolve()
    sage_dir = ws / ".sage"
    sage_dir.mkdir(parents=True, exist_ok=True)
    return sage_dir / "config.json"


@dataclass
class SageConfig:
    """SageCLI configuration supporting multiple providers and execution modes."""

    provider: str = "gemini"
    model: str = "gemini-3.8-flash"
    api_key: str = ""
    api_base: str = ""
    workspace: str = ""
    mode: str = "Safe"                   # Safe | Auto | Plan
    version: str = __version__
    max_iterations: int = 30
    timeout_seconds: int = 120
    ascii_only: bool = False
    debug: bool = False
    auto_approve_readonly: bool = True
    provider_keys: Dict[str, str] = field(default_factory=dict)
    custom_headers: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, workspace: Optional[str] = None) -> "SageConfig":
        """
        Hierarchical configuration resolution:
        1. Environment variables (highest precedence)
        2. Project-level .sage/config.json
        3. Global ~/.sage/config.json
        4. Auto-detected system environment keys
        5. Defaults
        """
        ws = str(Path(workspace or os.getcwd()).resolve())
        data: Dict[str, Any] = {
            "workspace": ws,
            "version": __version__,
        }

        # 1. Load global config
        global_path = get_global_config_path()
        if global_path.exists():
            try:
                with open(global_path, "r", encoding="utf-8") as f:
                    global_data = json.load(f)
                    data.update(global_data)
            except Exception:
                pass

        # 2. Load project-level config
        project_path = get_project_config_path(ws)
        if project_path.exists():
            try:
                with open(project_path, "r", encoding="utf-8") as f:
                    proj_data = json.load(f)
                    data.update(proj_data)
            except Exception:
                pass

        # 3. Detect API keys from environment
        detected_keys = dict(data.get("provider_keys", {}))
        for prov, info in PROVIDER_DEFAULTS.items():
            env_val = os.environ.get(info["env_var"], "").strip()
            if env_val:
                detected_keys[prov] = env_val

        data["provider_keys"] = detected_keys

        # 4. Determine active provider
        active_provider = os.environ.get("SAGE_PROVIDER") or data.get("provider")
        if not active_provider:
            # Auto-detect first provider with available key
            for prov in ["gemini", "openai", "anthropic", "groq", "openrouter", "ollama"]:
                if prov in detected_keys and detected_keys[prov]:
                    active_provider = prov
                    break
            if not active_provider:
                active_provider = "gemini"

        data["provider"] = active_provider

        # 5. Determine active model
        default_model = PROVIDER_DEFAULTS.get(active_provider, {}).get("default_model", "gemini-3.8-flash")
        data["model"] = os.environ.get("SAGE_MODEL") or data.get("model") or default_model

        # 6. Determine API key & API base
        api_key = os.environ.get(f"{active_provider.upper()}_API_KEY") or detected_keys.get(active_provider, "")
        data["api_key"] = api_key
        prov_default_base = PROVIDER_DEFAULTS.get(active_provider, {}).get("api_base", "")
        # Only use saved api_base if it is for custom/ollama or explicitly provided
        saved_base = data.get("api_base")
        if active_provider not in ("custom", "ollama") and (not saved_base or "googleapis" not in saved_base if active_provider == "gemini" else False):
            saved_base = prov_default_base
        data["api_base"] = os.environ.get("SAGE_API_BASE") or saved_base or prov_default_base

        # 7. Flags & Mode
        data["mode"] = os.environ.get("SAGE_MODE") or data.get("mode", "Safe")
        if os.environ.get("SAGE_ASCII_ONLY", "").lower() in ("1", "true", "yes"):
            data["ascii_only"] = True
        if os.environ.get("SAGE_DEBUG", "").lower() in ("1", "true", "yes"):
            data["debug"] = True

        data["workspace"] = ws
        data["version"] = __version__

        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def save_global(self) -> None:
        """Save configuration securely to ~/.sage/config.json with 0600 permissions."""
        global_path = get_global_config_path()
        payload = {
            "provider": self.provider,
            "model": self.model,
            "mode": self.mode,
            "api_base": self.api_base,
            "provider_keys": self.provider_keys,
            "max_iterations": self.max_iterations,
            "timeout_seconds": self.timeout_seconds,
            "ascii_only": self.ascii_only,
        }
        with open(global_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        
        # Set file permissions: user read/write only
        try:
            os.chmod(global_path, stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            pass

    def save_project(self) -> None:
        """Save project-level overrides to .sage/config.json."""
        project_path = get_project_config_path(self.workspace)
        payload = {
            "provider": self.provider,
            "model": self.model,
            "mode": self.mode,
            "max_iterations": self.max_iterations,
        }
        with open(project_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def is_configured(self) -> bool:
        """Check if an active provider and key/endpoint are configured."""
        if self.provider == "ollama":
            return True
        if self.api_key:
            return True
        if self.provider in self.provider_keys and self.provider_keys[self.provider]:
            return True
        # Check environment variable
        env_var = PROVIDER_DEFAULTS.get(self.provider, {}).get("env_var")
        if env_var and os.environ.get(env_var, "").strip():
            return True
        return False
