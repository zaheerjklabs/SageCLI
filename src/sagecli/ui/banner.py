"""Startup banner and contextual metadata display for SageCLI."""

import os
import shutil
from pathlib import Path
from typing import Optional

from rich.console import Console, RenderableType, Group
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.table import Table
from rich.box import ROUNDED, ASCII

from sagecli import __version__
from sagecli.ui.symbols import supports_unicode
from sagecli.ui.theme import Palette
from sagecli.ui.logo import (
    ASCII_LOGO_LINES,
    ASCII_FALLBACK_LINES,
    PRIMARY_BRAND,
    PRIMARY_TAGLINE,
    get_secondary_tagline,
    MIN_WIDTH_FULL_BOX,
    MIN_WIDTH_FULL_LOGO,
)


def get_formatted_workspace(path: Optional[str] = None) -> str:
    """Format current workspace path cleanly, replacing home dir with ~."""
    raw_path = Path(path or os.getcwd()).resolve()
    try:
        home = Path.home().resolve()
        if raw_path == home:
            return "~"
        if raw_path.is_relative_to(home):
            return f"~/{raw_path.relative_to(home)}"
    except Exception:
        pass
    return str(raw_path)


def create_banner_panel(
    terminal_width: Optional[int] = None,
    force_ascii: bool = False,
    force_compact: bool = False,
) -> RenderableType:
    """
    Construct the branded header / startup panel.
    Adapts gracefully to wide, medium, and narrow terminals:
    - Wide (>= 58 cols): Full ASCII logo in rounded panel box.
    - Medium (48-57 cols): Full ASCII logo centered without panel border.
    - Narrow (< 48 cols): Compact typographic wordmark and taglines.
    """
    if terminal_width is None:
        terminal_width = shutil.get_terminal_size(fallback=(80, 24)).columns

    use_ascii = force_ascii or not supports_unicode()
    is_narrow = force_compact or (terminal_width < MIN_WIDTH_FULL_LOGO)
    is_medium = not is_narrow and (terminal_width < MIN_WIDTH_FULL_BOX)

    sec_tagline = get_secondary_tagline(ascii_only=use_ascii)

    # 1. Narrow Terminal Layout (< 48 cols)
    if is_narrow:
        brand_text = Text(PRIMARY_BRAND, style=f"bold {Palette.TEXT_LIGHT}")
        tagline_text = Text(PRIMARY_TAGLINE, style=f"bold {Palette.SAGE_PRIMARY}")
        sec_text = Text(sec_tagline, style=f"{Palette.TEXT_MUTED}")

        return Group(
            brand_text,
            tagline_text,
            Text(),
            sec_text,
        )

    # 2. Build ASCII Art and Tagline Group
    lines = ASCII_FALLBACK_LINES if use_ascii else ASCII_LOGO_LINES
    ascii_text = Text("\n".join(lines), style=f"bold {Palette.SAGE_PRIMARY}")
    brand_text = Text(PRIMARY_BRAND, style=f"bold {Palette.TEXT_LIGHT}")
    tagline_text = Text(PRIMARY_TAGLINE, style=f"bold {Palette.TEXT_MUTED}")
    sec_text = Text(sec_tagline, style=f"{Palette.TEXT_DIM}")

    # 3. Medium Terminal Layout (48 - 57 cols) -> Centered without border
    if is_medium:
        return Group(
            Align.center(ascii_text),
            Text(),
            Align.center(brand_text),
            Align.center(tagline_text),
            Text(),
            Align.center(sec_text),
        )

    # 4. Wide Terminal Layout (>= 58 cols) -> Centered within rounded Panel
    panel_group = Group(
        Align.center(ascii_text),
        Text(),
        Align.center(brand_text),
        Align.center(tagline_text),
        Text(),
        Align.center(sec_text),
    )

    box_style = ASCII if use_ascii else ROUNDED
    # Target optimal panel width: comfortably houses logo (43) + padding
    panel_width = min(terminal_width - 4, 68)

    return Align.center(
        Panel(
            panel_group,
            box=box_style,
            border_style=Palette.BORDER_MUTED,
            padding=(1, 2),
            width=panel_width,
        )
    )


def create_metadata_table(
    workspace: Optional[str] = None,
    provider: Optional[str] = None,
    model: str = "gemini-2.5-pro",
    mode: str = "Safe",
    version: Optional[str] = None,
) -> Table:
    """Create a minimal, clean metadata table showing context."""
    table = Table(
        show_header=False,
        box=None,
        padding=(0, 2),
        expand=False,
        show_edge=False,
    )
    table.add_column("Key", style=f"{Palette.TEXT_MUTED}", no_wrap=True)
    table.add_column("Value", no_wrap=False)

    ws_str = get_formatted_workspace(workspace)
    ver_str = version or __version__

    table.add_row("Workspace", f"[{Palette.TEXT_LIGHT}]{ws_str}[/]")
    if provider:
        table.add_row("Provider", f"[{Palette.SAGE_PRIMARY}]{provider}[/]")
    if model:
        table.add_row("Model", f"[{Palette.MINT_ACCENT}]{model}[/]")
    if mode:
        table.add_row("Mode", f"[{Palette.SAGE_LIGHT}]{mode}[/]")
    if ver_str:
        table.add_row("Version", f"[{Palette.TEXT_MUTED}]{ver_str}[/]")

    return table


def get_terminal_width(console: Optional[Console] = None) -> int:
    """Get active terminal width from console or OS terminal."""
    if console is not None:
        if getattr(console, "_width", None) is not None:
            return console._width
        return console.width
    return shutil.get_terminal_size(fallback=(80, 24)).columns


def render_startup_screen(
    console: Console,
    workspace: Optional[str] = None,
    provider: Optional[str] = None,
    model: str = "gemini-2.5-pro",
    mode: str = "Safe",
    version: Optional[str] = None,
    force_ascii: bool = False,
    force_compact: bool = False,
) -> None:
    """Render the complete official SageCLI startup screen to the console."""
    term_width = get_terminal_width(console)

    # Top spacing
    console.print()

    # Branded banner box / header
    banner = create_banner_panel(
        terminal_width=term_width,
        force_ascii=force_ascii,
        force_compact=force_compact,
    )
    console.print(banner)
    console.print()

    # Contextual metadata
    meta = create_metadata_table(
        workspace=workspace,
        provider=provider,
        model=model,
        mode=mode,
        version=version,
    )

    if term_width >= MIN_WIDTH_FULL_BOX:
        console.print(Align.center(meta))
    else:
        console.print(meta)

    console.print()
