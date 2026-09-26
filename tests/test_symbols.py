"""Tests for visual symbols and ASCII fallback mode."""

from sagecli.ui.symbols import (
    UNICODE_SYMBOLS,
    ASCII_SYMBOLS,
    get_symbols,
    supports_unicode,
)


def test_unicode_symbols_content():
    """Verify Unicode symbols match specification."""
    assert UNICODE_SYMBOLS.SUCCESS == "✓"
    assert UNICODE_SYMBOLS.ERROR == "✗"
    assert UNICODE_SYMBOLS.WARNING == "⚠"
    assert UNICODE_SYMBOLS.ACTION == "→"
    assert UNICODE_SYMBOLS.INFO == "•"
    assert UNICODE_SYMBOLS.RUNNING == "⟳"
    assert UNICODE_SYMBOLS.ACTIVE == "●"
    assert UNICODE_SYMBOLS.PROMPT == "❯"


def test_ascii_symbols_content():
    """Verify ASCII fallback symbols match specification."""
    assert ASCII_SYMBOLS.SUCCESS == "[+]"
    assert ASCII_SYMBOLS.ERROR == "[x]"
    assert ASCII_SYMBOLS.WARNING == "[!]"
    assert ASCII_SYMBOLS.ACTION == "->"
    assert ASCII_SYMBOLS.INFO == "*"
    assert ASCII_SYMBOLS.RUNNING == "[~]"
    assert ASCII_SYMBOLS.ACTIVE == "[*]"
    assert ASCII_SYMBOLS.PROMPT == ">"


def test_force_ascii_get_symbols():
    """Verify get_symbols with force_ascii returns ASCII_SYMBOLS."""
    syms = get_symbols(force_ascii=True)
    assert syms == ASCII_SYMBOLS


def test_env_var_disables_unicode(monkeypatch):
    """Verify SAGE_ASCII_ONLY disables unicode."""
    monkeypatch.setenv("SAGE_ASCII_ONLY", "1")
    assert supports_unicode() is False
    syms = get_symbols()
    assert syms == ASCII_SYMBOLS
