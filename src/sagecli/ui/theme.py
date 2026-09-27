"""Theme and color system for SageCLI."""

import os
from dataclasses import dataclass
from rich.style import Style
from rich.theme import Theme


@dataclass(frozen=True)
class Palette:
    """Distinctive SageCLI color palette."""

    # Primary colors
    SAGE_PRIMARY: str = "#7DBA94"       # Distinctive sage green (primary brand)
    SAGE_LIGHT: str = "#A3D9B8"         # Bright sage highlight
    SAGE_DARK: str = "#4E8C68"          # Deep sage anchor
    
    # Accent colors
    MINT_ACCENT: str = "#5EEAD4"        # Subtle cyan / mint AI glow
    CYAN_ACCENT: str = "#6FE3D1"        # Soft cyan
    
    # Neutral & Background
    TEXT_LIGHT: str = "#E6EDE8"         # Soft white
    TEXT_MUTED: str = "#8B9E94"         # Slate sage gray
    TEXT_DIM: str = "#566B60"           # Dim gray
    BORDER_MUTED: str = "#3D4F45"       # Charcoal-sage border
    BORDER_LIGHT: str = "#5A7365"       # Active border
    BG_DARK: str = "#0F1412"           # Near black background
    BG_CARD: str = "#161D19"           # Deep charcoal surface
    
    # Semantic status colors
    SUCCESS: str = "#4ADE80"           # Emerald success
    WARNING: str = "#FBBF24"           # Warm amber warning
    ERROR: str = "#F87171"             # Coral red error
    INFO: str = "#94A3B8"              # Muted info
    ACTION: str = "#6FE3D1"            # Cyan mint action
    ACTIVE: str = "#7DBA94"            # Sage active dot


def is_color_disabled() -> bool:
    """Check if color output is explicitly disabled via env vars or non-tty."""
    if os.environ.get("NO_COLOR", "").strip():
        return True
    if os.environ.get("TERM", "").lower() == "dumb":
        return True
    return False


def get_rich_theme() -> Theme:
    """Construct Rich Theme configured with SageCLI visual identity."""
    if is_color_disabled():
        return Theme({
            "sage.primary": Style(),
            "sage.light": Style(),
            "sage.accent": Style(),
            "sage.muted": Style(dim=True),
            "sage.text": Style(),
            "sage.dim": Style(dim=True),
            "sage.border": Style(),
            "sage.success": Style(bold=True),
            "sage.warning": Style(bold=True),
            "sage.error": Style(bold=True),
            "sage.info": Style(),
            "sage.action": Style(bold=True),
            "sage.tagline": Style(bold=True),
        })

    return Theme({
        # Brand identities
        "sage.primary": Style(color=Palette.SAGE_PRIMARY, bold=True),
        "sage.light": Style(color=Palette.SAGE_LIGHT, bold=True),
        "sage.dark": Style(color=Palette.SAGE_DARK),
        "sage.accent": Style(color=Palette.MINT_ACCENT, bold=True),
        "sage.mint": Style(color=Palette.CYAN_ACCENT),
        
        # Text styles
        "sage.text": Style(color=Palette.TEXT_LIGHT),
        "sage.muted": Style(color=Palette.TEXT_MUTED),
        "sage.dim": Style(color=Palette.TEXT_DIM),
        "sage.border": Style(color=Palette.BORDER_MUTED),
        "sage.border.active": Style(color=Palette.BORDER_LIGHT),
        "sage.tagline": Style(color=Palette.TEXT_MUTED, bold=True),
        "sage.subtagline": Style(color=Palette.TEXT_DIM),
        
        # Meta info styles
        "sage.meta.label": Style(color=Palette.TEXT_MUTED),
        "sage.meta.value": Style(color=Palette.TEXT_LIGHT, bold=True),
        "sage.meta.model": Style(color=Palette.MINT_ACCENT, bold=True),
        "sage.meta.mode": Style(color=Palette.SAGE_LIGHT),
        
        # Status styles
        "sage.success": Style(color=Palette.SUCCESS, bold=True),
        "sage.warning": Style(color=Palette.WARNING, bold=True),
        "sage.error": Style(color=Palette.ERROR, bold=True),
        "sage.info": Style(color=Palette.INFO),
        "sage.action": Style(color=Palette.ACTION, bold=True),
        "sage.running": Style(color=Palette.MINT_ACCENT, bold=True),
        "sage.active": Style(color=Palette.ACTIVE, bold=True),
        
        # Prompt
        "sage.prompt.name": Style(color=Palette.SAGE_PRIMARY, bold=True),
        "sage.prompt.symbol": Style(color=Palette.MINT_ACCENT, bold=True),
    })
