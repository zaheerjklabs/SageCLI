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


def create_tips_renderable() -> RenderableType:
    """Render the 'Tips for getting started' block."""
    text = Text()
    text.append("Tips for getting started:\n", style=f"bold {Palette.TEXT_LIGHT}")
    text.append("1. Ask questions, edit files, or run commands.\n", style=f"{Palette.TEXT_MUTED}")
    text.append("2. Be specific for the best results.\n", style=f"{Palette.TEXT_MUTED}")
    text.append("3. Create ", style=f"{Palette.TEXT_MUTED}")
    text.append("SAGE.md", style=f"bold {Palette.SAGE_PRIMARY}")
    text.append(" files to customize your interactions with Sage.\n", style=f"{Palette.TEXT_MUTED}")
    text.append("4. ", style=f"{Palette.TEXT_MUTED}")
    text.append("/help", style=f"bold {Palette.MINT_ACCENT}")
    text.append(" for more information.", style=f"{Palette.TEXT_MUTED}")
    return text


def create_prompt_container_box(
    workspace: Optional[str] = None,
    mode: str = "Safe",
    model: str = "gemini-2.5-pro",
    terminal_width: Optional[int] = None,
    force_ascii: bool = False,
    active_tools_count: int = 7,
) -> RenderableType:
    """
    Construct the modern prompt & status container box:
    - Top row: 'Using 1 SAGE.md file' (or 'Using workspace context') ... '7 tools active'
    - Input bar: '> Ask Sage to scaffold an ML pipeline'
    - Bottom row: '~/Developer/playground' ... 'safe-exec (interactive)' ... 'gemini-2.5-pro'
    """
    if terminal_width is None:
        terminal_width = shutil.get_terminal_size(fallback=(80, 24)).columns

    use_ascii = force_ascii or not supports_unicode()
    box_style = ASCII if use_ascii else ROUNDED
    panel_width = min(terminal_width - 4, 72)

    ws_path = Path(workspace or os.getcwd()).resolve()
    sage_file = ws_path / "SAGE.md"
    if sage_file.exists():
        context_left = "Using 1 SAGE.md file"
    else:
        context_left = "Using workspace context"

    context_right = f"{active_tools_count} tools active"

    # Top line inside box
    top_table = Table.grid(expand=True)
    top_table.add_column(justify="left")
    top_table.add_column(justify="right")
    top_table.add_row(
        Text(context_left, style=f"{Palette.TEXT_MUTED}"),
        Text(context_right, style=f"{Palette.TEXT_DIM}"),
    )

    # Input row box (inner panel)
    prompt_sym = ">" if use_ascii else "❯"
    inner_text = Text()
    inner_text.append(f"{prompt_sym} ", style=f"bold {Palette.SAGE_PRIMARY}")
    inner_text.append("▌ ", style=f"bold {Palette.TEXT_LIGHT}")
    inner_text.append("Ask Sage to scaffold an ML pipeline or analyze datasets...", style=f"{Palette.TEXT_DIM}")

    inner_box = Panel(
        inner_text,
        box=box_style,
        border_style=Palette.BORDER_LIGHT if not use_ascii else Palette.BORDER_MUTED,
        padding=(0, 1),
    )

    # Bottom status row (Left: Folder location, Center: Mode, Right: Model)
    ws_str = get_formatted_workspace(str(ws_path))
    # Shorten workspace path cleanly so columns never collide
    max_ws_len = 22
    if len(ws_str) > max_ws_len:
        parts = [p for p in ws_str.split("/") if p]
        if len(parts) >= 2 and len(f".../{parts[-2]}/{parts[-1]}") <= max_ws_len:
            ws_display = f".../{parts[-2]}/{parts[-1]}"
        elif parts:
            ws_display = f".../{parts[-1]}"
            if len(ws_display) > max_ws_len:
                ws_display = ws_display[:max_ws_len-3] + "..."
        else:
            ws_display = ws_str[:max_ws_len-3] + "..."
    else:
        ws_display = ws_str

    mode_clean = mode.lower()
    if mode_clean == "safe":
        mode_str = "safe-exec (interactive)"
    elif mode_clean == "auto":
        mode_str = "auto-exec (autonomous)"
    else:
        mode_str = f"{mode_clean}-exec (plan)"
    model_str = model or "gemini-2.5-pro"

    bottom_table = Table.grid(expand=True)
    bottom_table.add_column(justify="left", ratio=4, no_wrap=True)
    bottom_table.add_column(justify="center", ratio=4, no_wrap=True)
    bottom_table.add_column(justify="right", ratio=3, no_wrap=True)
    bottom_table.add_row(
        Text(ws_display, style=f"{Palette.SAGE_PRIMARY}"),
        Text(mode_str, style=f"{Palette.MINT_ACCENT}"),
        Text(model_str, style=f"{Palette.CYAN_ACCENT}"),
    )

    container_group = Group(
        top_table,
        inner_box,
        bottom_table,
    )

    return Align.center(
        Panel(
            container_group,
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

    # Tips for getting started
    tips = create_tips_renderable()
    panel_width = min(term_width - 4, 72)
    if term_width >= MIN_WIDTH_FULL_BOX:
        console.print(Align.center(tips, width=panel_width))
    else:
        console.print(tips)

    console.print()

    # Modern Prompt & Status Container Box
    container_box = create_prompt_container_box(
        workspace=workspace,
        mode=mode,
        model=model,
        terminal_width=term_width,
        force_ascii=force_ascii,
    )
    console.print(container_box)
    console.print()
