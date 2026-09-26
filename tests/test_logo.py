"""Tests for SageCLI logo constants, formatting, and responsive behavior."""

from rich.console import Console

from sagecli.ui.logo import (
    ASCII_LOGO_LINES,
    PRIMARY_BRAND,
    PRIMARY_TAGLINE,
    SECONDARY_TAGLINE_UNICODE,
    SECONDARY_TAGLINE_ASCII,
    SAGECLI_LOGO,
    SAGECLI_COMPACT_LOGO,
    LOGO_WIDTH,
    LOGO_HEIGHT,
    render_logo_text,
    render_logo,
)


def test_ascii_logo_dimensions():
    """Verify ASCII logo has 6 lines and is 43 characters wide."""
    assert len(ASCII_LOGO_LINES) == 6
    assert LOGO_HEIGHT == 6
    assert LOGO_WIDTH == 43
    # Check max width of art lines
    max_line_len = max(len(line) for line in ASCII_LOGO_LINES)
    assert max_line_len == 43


def test_ascii_logo_content_exact():
    """Verify exact character groups in the primary ASCII logo."""
    assert ASCII_LOGO_LINES[0] == " ███████╗    █████╗     ██████╗    ███████╗"
    assert ASCII_LOGO_LINES[1] == " ██╔════╝   ██╔══██╗   ██╔════╝    ██╔════╝"
    assert ASCII_LOGO_LINES[2] == " ███████╗   ███████║   ██║  ███╗   █████╗"
    assert ASCII_LOGO_LINES[3] == " ╚════██║   ██╔══██║   ██║   ██║   ██╔══╝"
    assert ASCII_LOGO_LINES[4] == " ███████║   ██║  ██║   ╚██████╔╝   ███████╗"
    assert ASCII_LOGO_LINES[5] == " ╚══════╝   ╚═╝  ╚═╝    ╚═════╝    ╚══════╝"


def test_branding_constants():
    """Verify brand name and taglines."""
    assert PRIMARY_BRAND == "S A G E C L I"
    assert PRIMARY_TAGLINE == "AI ENGINEERING AGENT"
    assert SECONDARY_TAGLINE_UNICODE == "Build • Train • Debug • Evaluate • Deploy"
    assert SECONDARY_TAGLINE_ASCII == "Build * Train * Debug * Evaluate * Deploy"


def test_full_logo_constant():
    """Verify SAGECLI_LOGO constant contains ASCII art and taglines."""
    assert "S A G E C L I" in SAGECLI_LOGO
    assert "AI ENGINEERING AGENT" in SAGECLI_LOGO
    assert "███████╗" in SAGECLI_LOGO


def test_compact_logo_constant():
    """Verify compact logo for narrow terminals."""
    assert SAGECLI_COMPACT_LOGO == "S A G E C L I\nAI ENGINEERING AGENT"


def test_render_logo_text_responsive():
    """Verify plain text logo rendering adapts to terminal width."""
    # Wide terminal
    wide_output = render_logo_text(terminal_width=80)
    assert "███████╗" in wide_output
    assert "S A G E C L I" in wide_output

    # Narrow terminal (< 48 chars)
    narrow_output = render_logo_text(terminal_width=40)
    assert narrow_output == SAGECLI_COMPACT_LOGO
    assert "███████╗" not in narrow_output

    # Force compact
    forced_compact = render_logo_text(force_compact=True, terminal_width=100)
    assert forced_compact == SAGECLI_COMPACT_LOGO


def test_render_logo_text_ascii():
    """Verify ASCII fallback rendering."""
    ascii_out = render_logo_text(force_ascii=True, terminal_width=80)
    assert "____" in ascii_out
    assert "S A G E C L I" in ascii_out


def test_render_logo_rich_renderable():
    """Verify Rich renderable logo rendering."""
    console = Console(width=80, record=True)
    renderable = render_logo(terminal_width=80)
    console.print(renderable)
    rendered_text = console.export_text()
    assert "S A G E C L I" in rendered_text
    assert "AI ENGINEERING AGENT" in rendered_text
