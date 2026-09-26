"""Security utilities: API key masking, secret protection, and permission validation."""

import re
from pathlib import Path
from typing import Tuple, Optional

# Regex patterns for common secret keys to prevent accidental leaks
SECRET_PATTERNS = [
    re.compile(r"(sk-[a-zA-Z0-9_\-]{20,})"),                         # OpenAI / Anthropic
    re.compile(r"(AIzaSy[a-zA-Z0-9_\-]{33})"),                        # Google Gemini
    re.compile(r"(gsk_[a-zA-Z0-9_\-]{20,})"),                        # Groq
    re.compile(r"Bearer\s+([a-zA-Z0-9_\-\.]{20,})", re.IGNORECASE),  # Generic Bearer
]

# High-risk command keywords requiring explicit approval in Safe/Auto mode
DANGEROUS_COMMANDS = [
    "rm -rf", "mkfs", "dd if=", ":(){ :|:& };:", "shutdown", "reboot",
    "chmod 777", "chmod -R 777", "chown -R", "drop database", "truncate table",
    "git reset --hard", "git clean -fdx", "curl | bash", "wget | bash"
]


def mask_secret(secret: Optional[str]) -> str:
    """Safely mask API key or secret for UI display (e.g. sk-proj...4f2A)."""
    if not secret:
        return "None"
    s = str(secret).strip()
    if len(s) <= 8:
        return "****"
    return f"{s[:6]}...{s[-4:]}"


def sanitize_text(text: str) -> str:
    """Scrub sensitive API keys from strings, error messages, and logs."""
    sanitized = text
    for pattern in SECRET_PATTERNS:
        sanitized = pattern.sub(r"[REDACTED_SECRET]", sanitized)
    return sanitized


def is_path_safe(target_path: str, workspace_root: str) -> Tuple[bool, str]:
    """Verify target path is safely contained within workspace directory."""
    try:
        ws_resolved = Path(workspace_root).resolve()
        target_resolved = (ws_resolved / target_path).resolve()
        
        # Check if target is inside workspace
        if target_resolved == ws_resolved or ws_resolved in target_resolved.parents:
            return True, ""
        
        # Target escapes workspace
        return False, f"Path '{target_path}' is outside workspace root '{workspace_root}'"
    except Exception as e:
        return False, f"Invalid path resolution: {e}"


def check_command_safety(command: str) -> Tuple[bool, str]:
    """Check if shell command contains known high-risk destructive patterns."""
    cmd_lower = command.lower()
    for dangerous in DANGEROUS_COMMANDS:
        if dangerous in cmd_lower:
            return False, f"Command contains high-risk operation: '{dangerous}'"
    
    # Check for curl/wget piped to bash/sh
    if re.search(r"(curl|wget)\s+.*\|\s*(bash|sh|zsh)", cmd_lower):
        return False, "Command pipes remote script to shell interpreter."

    return True, ""


def ensure_gitignore_has_sage(workspace_root: str) -> None:
    """Ensure .sage/ cache and .env are included in .gitignore to prevent secret leaks."""
    try:
        gitignore_path = Path(workspace_root) / ".gitignore"
        entries_to_add = [".sage/", "*.env", ".env.*", "!*.env.example"]
        
        existing_lines = []
        if gitignore_path.exists():
            existing_lines = gitignore_path.read_text(encoding="utf-8").splitlines()

        to_append = [e for e in entries_to_add if e not in existing_lines]
        if to_append:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                if existing_lines and existing_lines[-1] != "":
                    f.write("\n")
                f.write("\n# SageCLI state and secrets\n")
                for item in to_append:
                    f.write(f"{item}\n")
    except Exception:
        pass
