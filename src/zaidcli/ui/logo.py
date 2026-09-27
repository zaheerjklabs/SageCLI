"""Official SageCLI ASCII logo and terminal branding components."""

import shutil
from typing import List, Optional
from rich.console import RenderableType
from rich.text import Text
from rich.align import Align

from sagecli.ui.symbols import supports_unicode
from sagecli.ui.theme import Palette

# Primary ASCII Art Lines - 43 characters wide
ASCII_LOGO_LINES: List[str] = [
    " ███████╗    █████╗     ██████╗    ███████╗",
    " ██╔════╝   ██╔══██╗   ██╔════╝    ██╔════╝",
    " ███████╗   ███████║   ██║  ███╗   █████╗",
    " ╚════██║   ██╔══██║   ██║   ██║   ██╔══╝",
    " ███████║   ██║  ██║   ╚██████╔╝   ███████╗",
    " ╚══════╝   ╚═╝  ╚═╝    ╚═════╝    ╚══════╝",
]

# Standard 7-bit ASCII fallback for non-UTF8 terminals
ASCII_FALLBACK_LINES: List[str] = [
    "  ____     _      ____  _____ ",
    " / ___|   / \\    / ___|| ____|",
    " \\___ \\  / _ \\  | |  _ |  _|  ",
    "  ___) |/ ___ \\ | |_| || |___ ",
    " |____//_/   \\_\\\\____(_)_____|",
]

PRIMARY_BRAND: str = "S A G E C L I"
PRIMARY_TAGLINE: str = "AI ENGINEERING AGENT"
SECONDARY_TAGLINE_UNICODE: str = "Build • Train • Debug • Evaluate • Deploy"
SECONDARY_TAGLINE_ASCII: str = "Build * Train * Debug * Evaluate * Deploy"

# Max width of the full ASCII logo
LOGO_WIDTH: int = 43
LOGO_HEIGHT: int = len(ASCII_LOGO_LINES)

# Thresholds for responsive terminal behavior
MIN_WIDTH_FULL_BOX: int = 60
MIN_WIDTH_FULL_LOGO: int = 48


def get_full_ascii_art() -> str:
    """Return the raw ASCII art string for the SageCLI wordmark."""
    return "\n".join(ASCII_LOGO_LINES)


# Complete official logo string
SAGECLI_LOGO: str = f"""{get_full_ascii_art()}

              {PRIMARY_BRAND}
        {PRIMARY_TAGLINE}"""

# Compact logo string for narrow terminals
SAGECLI_COMPACT_LOGO: str = f"""{PRIMARY_BRAND}
{PRIMARY_TAGLINE}"""


def get_secondary_tagline(ascii_only: bool = False) -> str:
    """Return the secondary tagline with proper bullet styling."""
    if ascii_only or not supports_unicode():
        return SECONDARY_TAGLINE_ASCII
    return SECONDARY_TAGLINE_UNICODE


def render_logo_text(
    force_compact: bool = False,
    force_ascii: bool = False,
    terminal_width: Optional[int] = None,
) -> str:
    """Render plain-text version of the logo according to terminal width constraints."""
    if terminal_width is None:
        terminal_width = shutil.get_terminal_size(fallback=(80, 24)).columns

    if force_compact or terminal_width < MIN_WIDTH_FULL_LOGO:
        return SAGECLI_COMPACT_LOGO

    if force_ascii or not supports_unicode():
        # Clean ASCII fallback
        fallback_art = "\n".join(ASCII_FALLBACK_LINES)
        return f"{fallback_art}\n\n        {PRIMARY_BRAND}\n  {PRIMARY_TAGLINE}"

    return SAGECLI_LOGO


def render_logo(
    force_compact: bool = False,
    force_ascii: bool = False,
    terminal_width: Optional[int] = None,
    color: bool = True,
    center: bool = True,
) -> RenderableType:
    """
    Render a styled Rich Renderable representing the SageCLI logo.
    
    Adheres strictly to the visual identity:
    - Primary single color (Sage Green) for ASCII wordmark
    - Soft white / muted slate for brand and taglines
    - Dynamic responsive terminal sizing (wide, medium, narrow)
    """
    if terminal_width is None:
        terminal_width = shutil.get_terminal_size(fallback=(80, 24)).columns

    is_narrow = force_compact or (terminal_width < MIN_WIDTH_FULL_LOGO)
    use_ascii = force_ascii or not supports_unicode()

    primary_color = Palette.SAGE_PRIMARY if color else "default"
    brand_color = Palette.TEXT_LIGHT if color else "default"
    tagline_color = Palette.TEXT_MUTED if color else "default"

    if is_narrow:
        # Compact logo for narrow terminals
        text = Text()
        text.append(PRIMARY_BRAND, style=f"bold {brand_color}")
        text.append("\n")
        text.append(PRIMARY_TAGLINE, style=f"{tagline_color}")
        return Align.center(text) if center else text

    # Full logo
    lines = ASCII_FALLBACK_LINES if use_ascii else ASCII_LOGO_LINES
    ascii_text = Text("\n".join(lines), style=f"bold {primary_color}")
    brand_text = Text(PRIMARY_BRAND, style=f"bold {brand_color}")
    tagline_text = Text(PRIMARY_TAGLINE, style=f"bold {tagline_color}")

    if center:
        from rich.console import Group
        return Group(
            Align.center(ascii_text),
            Text(),
            Align.center(brand_text),
            Align.center(tagline_text),
        )

    # Left-aligned / raw
    combined = Text()
    combined.append(ascii_text)
    combined.append("\n\n")
    combined.append(f"              {PRIMARY_BRAND}\n", style=f"bold {brand_color}")
    combined.append(f"        {PRIMARY_TAGLINE}", style=f"bold {tagline_color}")
    return combined
