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


# Global default console instance
default_console = SageConsole()
