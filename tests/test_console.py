"""Tests for SageConsole and prompt formatting."""

import io
from sagecli.ui.console import SageConsole
from sagecli.ui.prompts import get_prompt_text


def test_console_status_methods():
    """Verify all status indicators output correct messages."""
    buffer = io.StringIO()
    console = SageConsole(file=buffer)

    console.success("Operation succeeded")
    console.error("Operation failed")
    console.warning("Careful with parameters")
    console.action("Building pipeline")
    console.info("Info note")
    console.running("Training underway")
    console.active("Agent active")

    out = buffer.getvalue()
    assert "✓" in out
    assert "Operation succeeded" in out
    assert "✗" in out
    assert "Operation failed" in out
    assert "⚠" in out
    assert "→" in out
    assert "•" in out
    assert "⟳" in out
    assert "●" in out


def test_console_ascii_fallback():
    """Verify ASCII fallback status indicators."""
    buffer = io.StringIO()
    console = SageConsole(force_ascii=True, file=buffer)

    console.success("Operation succeeded")
    console.error("Operation failed")
    console.warning("Warning note")
    console.action("Action note")

    out = buffer.getvalue()
    assert "[+]" in out
    assert "[x]" in out
    assert "[!]" in out
    assert "->" in out


def test_prompt_formatting():
    """Verify prompt formatting for unicode and ascii."""
    unicode_prompt = get_prompt_text(force_ascii=False)
    assert unicode_prompt == "sage ❯ "

    ascii_prompt = get_prompt_text(force_ascii=True)
    assert ascii_prompt == "sage > "


def test_thinking_stream_and_chunk_streaming():
    """Verify ThinkingStream transitions from thinking status to word-by-word streaming."""
    buffer = io.StringIO()
    console = SageConsole(file=buffer)

    with console.create_thinking_stream("Sage is thinking...") as stream:
        assert stream.has_streamed is False
        stream.on_chunk("Hello ")
        assert stream.has_streamed is True
        stream.on_chunk("world!")

    out = buffer.getvalue()
    assert "Hello world!" in out


def test_console_spinner_status():
    """Verify console.status context manager runs cleanly."""
    buffer = io.StringIO()
    console = SageConsole(file=buffer)

    with console.status("Inspecting model..."):
        pass

