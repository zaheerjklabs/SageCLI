"""Visual symbols and glyphs with ASCII fallback support."""

import os
import sys
from dataclasses import dataclass


def supports_unicode() -> bool:
    """Determine if current terminal environment supports UTF-8 Unicode characters."""
    if os.environ.get("SAGE_ASCII_ONLY", "").lower() in ("1", "true", "yes"):
        return False
    
    # Check stdout encoding
    encoding = getattr(sys.stdout, "encoding", None)
    if not encoding:
        return True
    
    encoding = encoding.lower()
    if "utf" in encoding:
        return True
    if encoding in ("ascii", "ansi_x3.4-1968", "cp437", "us-ascii"):
        return False
    
    return True


@dataclass(frozen=True)
class Symbols:
    """Symbol set for CLI interface."""

    # Status indicators
    SUCCESS: str
    ERROR: str
    WARNING: str
    ACTION: str
    INFO: str
    RUNNING: str
    ACTIVE: str
    
    # UI Elements
    PROMPT: str
    BULLET: str
    SPARKLE: str
    ARROW_RIGHT: str
    
    # Box drawing characters
    BOX_TOP_LEFT: str
    BOX_TOP_RIGHT: str
    BOX_BOTTOM_LEFT: str
    BOX_BOTTOM_RIGHT: str
    BOX_HORIZONTAL: str
    BOX_VERTICAL: str


UNICODE_SYMBOLS = Symbols(
    SUCCESS="✓",
    ERROR="✗",
    WARNING="⚠",
    ACTION="→",
    INFO="•",
    RUNNING="⟳",
    ACTIVE="●",
    PROMPT="❯",
    BULLET="•",
    SPARKLE="✦",
    ARROW_RIGHT="→",
    BOX_TOP_LEFT="╭",
    BOX_TOP_RIGHT="╮",
    BOX_BOTTOM_LEFT="╰",
    BOX_BOTTOM_RIGHT="╯",
    BOX_HORIZONTAL="─",
    BOX_VERTICAL="│",
)

ASCII_SYMBOLS = Symbols(
    SUCCESS="[+]",
    ERROR="[x]",
    WARNING="[!]",
    ACTION="->",
    INFO="*",
    RUNNING="[~]",
    ACTIVE="[*]",
    PROMPT=">",
    BULLET="*",
    SPARKLE="*",
    ARROW_RIGHT="->",
    BOX_TOP_LEFT="+",
    BOX_TOP_RIGHT="+",
    BOX_BOTTOM_LEFT="+",
    BOX_BOTTOM_RIGHT="+",
    BOX_HORIZONTAL="-",
    BOX_VERTICAL="|",
)


def get_symbols(force_ascii: bool = False) -> Symbols:
    """Get active symbol set based on terminal capability or override."""
    if force_ascii or not supports_unicode():
        return ASCII_SYMBOLS
    return UNICODE_SYMBOLS
