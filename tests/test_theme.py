"""Tests for SageCLI theme and color palette."""

from sagecli.ui.theme import Palette, get_rich_theme, is_color_disabled


def test_palette_colors():
    """Verify Palette color definitions."""
    assert Palette.SAGE_PRIMARY == "#7DBA94"
    assert Palette.MINT_ACCENT == "#5EEAD4"
    assert Palette.TEXT_LIGHT == "#E6EDE8"
    assert Palette.TEXT_MUTED == "#8B9E94"
    assert Palette.SUCCESS == "#4ADE80"
    assert Palette.WARNING == "#FBBF24"
    assert Palette.ERROR == "#F87171"


def test_rich_theme_creation():
    """Verify Rich theme builds with proper keys."""
    theme = get_rich_theme()
    assert "sage.primary" in theme.styles
    assert "sage.accent" in theme.styles
    assert "sage.success" in theme.styles
    assert "sage.warning" in theme.styles
    assert "sage.error" in theme.styles


def test_color_disabled_environment(monkeypatch):
    """Verify NO_COLOR environment variable disables color."""
    monkeypatch.setenv("NO_COLOR", "1")
    assert is_color_disabled() is True
    theme = get_rich_theme()
    assert theme is not None
