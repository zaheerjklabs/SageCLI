"""SageCLI Console wrapper with branded visual language and status formatters."""

import sys
from typing import Optional, Any
from rich.console import Console

from sagecli.ui.theme import get_rich_theme, Palette
from sagecli.ui.symbols import get_symbols


from rich.markup import escape


class SageConsole:
    """Rich Console configured specifically for SageCLI visual language."""

    def __init__(
        self,
        force_ascii: bool = False,
        force_color: Optional[bool] = None,
        width: Optional[int] = None,
        file: Optional[Any] = None,
    ):
        self.force_ascii = force_ascii
        self.theme = get_rich_theme()
        self._console = Console(
            theme=self.theme,
            force_terminal=force_color,
            no_color=(force_color is False),
            width=width,
            file=file or sys.stdout,
            highlight=False,
        )

    @property
    def console(self) -> Console:
        return self._console

    @property
    def width(self) -> int:
        return self._console.width

    def get_symbols(self):
        return get_symbols(force_ascii=self.force_ascii)

    def print(self, *args, **kwargs) -> None:
        self._console.print(*args, **kwargs)

    def markdown(self, content: str, code_theme: str = "monokai") -> None:
        """Render markdown text with rich styling, headings, lists, and syntax-highlighted code blocks."""
        from rich.markdown import Markdown
        if not content:
            return
        md = Markdown(content.strip(), code_theme=code_theme)
        self._console.print(md)

    def rule(self, title: str = "", **kwargs) -> None:
        self._console.rule(title, style=Palette.BORDER_MUTED, **kwargs)

    # Branded Visual Language Status Methods

    def success(self, message: str) -> None:
        """Print success status: ✓ <message>"""
        sym = escape(self.get_symbols().SUCCESS)
        self._console.print(f"[{Palette.SUCCESS}]{sym}[/] [{Palette.TEXT_LIGHT}]{message}[/]")

    def error(self, message: str) -> None:
        """Print error status: ✗ <message>"""
        sym = escape(self.get_symbols().ERROR)
        self._console.print(f"[{Palette.ERROR}]{sym}[/] [{Palette.TEXT_LIGHT}]{message}[/]")

    def warning(self, message: str) -> None:
        """Print warning status: ⚠ <message>"""
        sym = escape(self.get_symbols().WARNING)
        self._console.print(f"[{Palette.WARNING}]{sym}[/] [{Palette.TEXT_LIGHT}]{message}[/]")

    def action(self, message: str) -> None:
        """Print action in progress: → <message>"""
        sym = escape(self.get_symbols().ACTION)
        self._console.print(f"[{Palette.ACTION}]{sym}[/] [{Palette.TEXT_LIGHT}]{message}[/]")

    def info(self, message: str) -> None:
        """Print informational bullet: • <message>"""
        sym = escape(self.get_symbols().INFO)
        self._console.print(f"[{Palette.INFO}]{sym}[/] [{Palette.TEXT_MUTED}]{message}[/]")

    def running(self, message: str) -> None:
        """Print running status indicator: ⟳ <message>"""
        sym = escape(self.get_symbols().RUNNING)
        self._console.print(f"[{Palette.MINT_ACCENT}]{sym}[/] [{Palette.TEXT_LIGHT}]{message}[/]")

    def active(self, message: str) -> None:
        """Print active status dot: ● <message>"""
        sym = escape(self.get_symbols().ACTIVE)
        self._console.print(f"[{Palette.SAGE_PRIMARY}]{sym}[/] [{Palette.TEXT_LIGHT}]{message}[/]")

    # Thinking, Doing & Streaming Helpers

    def status(self, message: str, spinner: str = "dots"):
        """Context manager displaying a live animated spinner with Sage styling."""
        sym = escape(self.get_symbols().RUNNING)
        return self._console.status(
            f"[{Palette.MINT_ACCENT}]{sym} {message}[/]",
            spinner=spinner,
            spinner_style=Palette.MINT_ACCENT,
        )

    def thinking(self, message: str = "Sage is thinking..."):
        """Context manager for agent thinking state with live spinner."""
        return self.status(message)

    def stream_chunk(self, chunk: str) -> None:
        """Output a text chunk immediately for real-time word-by-word streaming."""
        self._console.print(chunk, end="", highlight=False)
        if hasattr(self._console.file, "flush"):
            try:
                self._console.file.flush()
            except Exception:
                pass

    def create_thinking_stream(self, message: str = "Sage is thinking..."):
        """Create a thinking & streaming context manager."""
        return ThinkingStream(self, message)


class ThinkingStream:
    """Manages dynamic transition between 'thinking' animated spinner and live word-by-word streaming."""

    def __init__(self, console: SageConsole, message: str = "Sage is thinking..."):
        self.console = console
        self.message = message
        self._status = None
        self.has_streamed = False

    def __enter__(self):
        sym = escape(self.console.get_symbols().ACTIVE)
        self._status = self.console.console.status(
            f"[{Palette.SAGE_PRIMARY}]{sym}[/] [{Palette.MINT_ACCENT} bold]{self.message}[/]",
            spinner="dots",
            spinner_style=Palette.MINT_ACCENT,
        )
        self._status.start()
        return self

    def on_chunk(self, chunk: str) -> None:
        if not chunk:
            return
        if not self.has_streamed:
            if self._status:
                self._status.stop()
                self._status = None
            self.has_streamed = True
            self.console.print()  # Clean line break before stream

        self.console.stream_chunk(chunk)

    def update_status(self, message: str) -> None:
        self.message = message
        if self._status:
            sym = escape(self.console.get_symbols().ACTIVE)
            self._status.update(f"[{Palette.SAGE_PRIMARY}]{sym}[/] [{Palette.MINT_ACCENT} bold]{message}[/]")

    def stop_status(self) -> None:
        if self._status:
            self._status.stop()
            self._status = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._status:
            self._status.stop()
            self._status = None
        if self.has_streamed:
            self.console.print()
            self.console.print()


# Global default console instance
default_console = SageConsole()

