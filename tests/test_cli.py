"""Tests for SageCLI CLI commands, flags, and runner."""

from typer.testing import CliRunner
from sagecli.cli import app
from sagecli import __version__

runner = CliRunner()


def test_cli_version_flag():
    """Verify sage --version outputs version and exits cleanly."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "SageCLI" in result.output
    assert f"v{__version__}" in result.output
    # Ensure startup screen is not printed
    assert "Build • Train • Debug • Evaluate • Deploy" not in result.output


def test_cli_short_version_flag():
    """Verify sage -v outputs version."""
    result = runner.invoke(app, ["-v"])
    assert result.exit_code == 0
    assert "SageCLI" in result.output
    assert f"v{__version__}" in result.output


def test_cli_logo_flag():
    """Verify sage --logo outputs ASCII logo."""
    result = runner.invoke(app, ["--logo"])
    assert result.exit_code == 0
    assert "███████╗" in result.output
    assert "S A G E C L I" in result.output


def test_cli_demo_command():
    """Verify sage demo command runs visual language demonstration."""
    result = runner.invoke(app, ["demo"])
    assert result.exit_code == 0
    assert "Workspace initialized" in result.output
    assert "Model trained successfully" in result.output


def test_cli_direct_prompt_argument(monkeypatch):
    """Verify sage <prompt> executes prompt without opening REPL."""
    from sagecli.core.agent import SageAgent
    def mock_run_task(self, prompt, **kwargs):
        self.console.active(f"Task: [bold]{prompt}[/]")
        return "Task completed successfully"
    monkeypatch.setattr(SageAgent, "run_task", mock_run_task)
    result = runner.invoke(app, ["build", "churn", "model"])
    assert result.exit_code == 0
    assert "Task: build churn model" in result.output
