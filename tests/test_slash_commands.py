"""Unit tests for slash commands, settings management, usage tracker, and doctor checks."""

from typer.testing import CliRunner

from sagecli.cli import app
from sagecli.core.tracker import UsageTracker
from sagecli.ui.prompts import SlashCommandCompleter

runner = CliRunner()


def test_usage_tracker_calculation():
    """Verify UsageTracker records tokens and calculates cost correctly."""
    tracker = UsageTracker()
    tracker.record_usage(prompt_tokens=1000, completion_tokens=500)
    
    summary = tracker.get_summary(model_name="gemini-3.8-flash")
    assert summary["requests"] == 1
    assert summary["prompt_tokens"] == 1000
    assert summary["completion_tokens"] == 500
    assert summary["total_tokens"] == 1500
    assert summary["estimated_cost_usd"] > 0


def test_slash_command_completer():
    """Verify SlashCommandCompleter returns all slash commands."""
    completer = SlashCommandCompleter()
    assert "/help" in completer.commands
    assert "/config" in completer.commands
    assert "/doctor" in completer.commands
    assert "/mode" in completer.commands
    assert "/cost" in completer.commands


def test_cli_help_command():
    """Verify sage help displays command palette."""
    result = runner.invoke(app, ["help"])
    assert result.exit_code == 0
    assert "SageCLI Command Palette" in result.output
    assert "/doctor" in result.output
    assert "/config" in result.output


def test_cli_config_command():
    """Verify sage config displays active configuration."""
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert "SageCLI Active Configuration" in result.output
    assert "Provider" in result.output
    assert "Model" in result.output


def test_cli_cost_command():
    """Verify sage cost displays usage table."""
    result = runner.invoke(app, ["cost"])
    assert result.exit_code == 0
    assert "Session Token Usage & Cost" in result.output
    assert "Total Requests" in result.output
