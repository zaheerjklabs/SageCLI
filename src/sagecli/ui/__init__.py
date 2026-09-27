"""SageCLI UI module exposing branding, logo, theme, symbols, and console."""

from sagecli.ui.theme import Palette, get_rich_theme
from sagecli.ui.symbols import (
    Symbols,
    UNICODE_SYMBOLS,
    ASCII_SYMBOLS,
    get_symbols,
    supports_unicode,
)
from sagecli.ui.logo import (
    ASCII_LOGO_LINES,
    ASCII_FALLBACK_LINES,
    PRIMARY_BRAND,
    PRIMARY_TAGLINE,
    SECONDARY_TAGLINE_UNICODE,
    SECONDARY_TAGLINE_ASCII,
    SAGECLI_LOGO,
    SAGECLI_COMPACT_LOGO,
    render_logo,
    render_logo_text,
    get_secondary_tagline,
)
from sagecli.ui.banner import (
    create_banner_panel,
    create_metadata_table,
    render_startup_screen,
    get_formatted_workspace,
)
from sagecli.ui.console import SageConsole, default_console
from sagecli.ui.prompts import (
    get_prompt_text,
    get_prompt_tokens,
    create_prompt_session,
)

__all__ = [
    "Palette",
    "get_rich_theme",
    "Symbols",
    "UNICODE_SYMBOLS",
    "ASCII_SYMBOLS",
    "get_symbols",
    "supports_unicode",
    "ASCII_LOGO_LINES",
    "ASCII_FALLBACK_LINES",
    "PRIMARY_BRAND",
    "PRIMARY_TAGLINE",
    "SECONDARY_TAGLINE_UNICODE",
    "SECONDARY_TAGLINE_ASCII",
    "SAGECLI_LOGO",
    "SAGECLI_COMPACT_LOGO",
    "render_logo",
    "render_logo_text",
    "get_secondary_tagline",
    "create_banner_panel",
    "create_metadata_table",
    "render_startup_screen",
    "get_formatted_workspace",
    "SageConsole",
    "default_console",
    "get_prompt_text",
    "get_prompt_tokens",
    "create_prompt_session",
]
