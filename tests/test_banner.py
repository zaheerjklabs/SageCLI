"""Tests for SageCLI banner and startup screen components."""

from pathlib import Path
from rich.console import Console

from sagecli.ui.banner import (
    create_banner_panel,
    create_metadata_table,
    create_tips_renderable,
    create_prompt_container_box,
    render_startup_screen,
    get_formatted_workspace,
)


def test_get_formatted_workspace(monkeypatch):
    """Verify home path is replaced with ~."""
    home = Path.home()
    workspace = home / "projects" / "churn-prediction"
    formatted = get_formatted_workspace(str(workspace))
    assert formatted == "~/projects/churn-prediction"


def test_create_banner_panel_wide():
    """Verify banner panel at wide width returns formatted renderable."""
    console = Console(width=90, record=True)
    panel = create_banner_panel(terminal_width=90)
    console.print(panel)
    text = console.export_text()
    assert "S A G E C L I" in text
    assert "AI ENGINEERING AGENT" in text
    assert "Build • Train • Debug • Evaluate • Deploy" in text


def test_create_banner_panel_narrow():
    """Verify banner panel at narrow width switches to compact."""
    console = Console(width=40, record=True)
    panel = create_banner_panel(terminal_width=40)
    console.print(panel)
    text = console.export_text()
    assert "S A G E C L I" in text
    assert "AI ENGINEERING AGENT" in text
    assert "███████╗" not in text


def test_create_metadata_table():
    """Verify metadata table renders key context info."""
    console = Console(width=80, record=True)
    table = create_metadata_table(
        workspace="/home/zaheer/projects/churn",
        model="Gemini 2.5 Pro",
        mode="Safe",
        version="0.1.0",
    )
    console.print(table)
    text = console.export_text()
    assert "Workspace" in text
    assert "Model" in text
    assert "Gemini 2.5 Pro" in text
    assert "Mode" in text
    assert "Safe" in text
    assert "Version" in text
    assert "0.1.0" in text


def test_create_tips_renderable():
    """Verify tips section contains starting instructions."""
    console = Console(width=80, record=True)
    tips = create_tips_renderable()
    console.print(tips)
    text = console.export_text()
    assert "Tips for getting started:" in text
    assert "1. Ask questions" in text
    assert "SAGE.md" in text
    assert "/help" in text


def test_create_prompt_container_box():
    """Verify Gemini-style prompt & status container box renders folder, mode, and model."""
    console = Console(width=80, record=True)
    box = create_prompt_container_box(
        workspace="/home/zaheer/Developer/playground",
        mode="Safe",
        model="gemini-2.5-pro",
        terminal_width=80,
    )
    console.print(box)
    text = console.export_text()
    assert "~/Developer/playground" in text
    assert "safe-exec" in text
    assert "gemini-2.5-pro" in text
    assert "tools active" in text


def test_render_startup_screen():
    """Verify full startup screen renders without error."""
    console = Console(width=80, record=True)
    render_startup_screen(
        console=console,
        workspace="/home/zaheer/projects/test",
        model="gemini-2.5-pro",
        mode="Safe",
        version="0.1.0",
    )
    text = console.export_text()
    assert "S A G E C L I" in text
    assert "Tips for getting started:" in text
    assert "gemini-2.5-pro" in text
    assert "~/projects/test" in text
