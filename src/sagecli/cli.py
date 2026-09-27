"""CLI Entry point, commands, and interactive autonomous REPL loop for SageCLI."""

import sys
import os
from typing import Optional, List, Dict, Any
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from sagecli import __version__
from sagecli.config import SageConfig, PROVIDER_DEFAULTS
from sagecli.security import mask_secret
from sagecli.ui.theme import Palette
from sagecli.ui.logo import render_logo
from sagecli.ui.banner import render_startup_screen
from sagecli.ui.console import SageConsole
from sagecli.ui.prompts import create_prompt_session, get_prompt_text
from sagecli.wizard import run_setup_wizard
from sagecli.core.agent import SageAgent
from sagecli.core.context import WorkspaceContext
from sagecli.core.tracker import session_tracker
from sagecli.core.doctor import run_doctor_checks
from sagecli.tools.registry import default_registry

app = typer.Typer(
    name="sage",
    help="SageCLI - Autonomous AI Engineering Agent for Machine Learning & Deep Learning",
    add_completion=False,
    no_args_is_help=False,
)


def version_callback(value: bool):
    if value:
        console = Console(highlight=False)
        console.print(f"[{Palette.SAGE_PRIMARY}]SageCLI[/] [{Palette.TEXT_LIGHT}]v{__version__}[/]")
        raise typer.Exit()


def logo_callback(value: bool):
    if value:
        console = Console(highlight=False)
        console.print(render_logo())
        raise typer.Exit()


def make_permission_callback(config: SageConfig, sage_console: SageConsole):
    """Generate interactive permission callback for tool execution."""
    session_auto_approve = [False]

    def ask_permission(tool_name: str, arguments: Dict[str, Any]) -> bool:
        if session_auto_approve[0] or config.mode.lower() == "auto":
            return True

        sage_console.print()
        arg_summary = ""
        if "command" in arguments:
            arg_summary = f"Command: [bold]{arguments['command']}[/]"
        elif "path" in arguments:
            arg_summary = f"File: [bold]{arguments['path']}[/]"
        elif "message" in arguments:
            arg_summary = f"Message: {arguments['message']}"

        sage_console.warning(f"Permission Request: Execute [bold]{tool_name}[/] ({arg_summary})")
        ans = Prompt.ask(
            f"[{Palette.TEXT_LIGHT}]Approve execution? (y: yes, n: no, a: always for session)[/]",
            choices=["y", "n", "a", "yes", "no"],
            default="y",
        ).lower()

        if ans in ("a", "always"):
            session_auto_approve[0] = True
            sage_console.info("Auto-approval enabled for remaining steps in this session.")
            return True
        elif ans in ("y", "yes"):
            return True
        else:
            sage_console.warning("Action skipped by user.")
            return False

    return ask_permission


def display_help_palette(sage_console: SageConsole):
    """Display categorized slash command palette and shortcut assistance."""
    sage_console.print()
    sage_console.print(f"[{Palette.SAGE_PRIMARY} bold]SageCLI Command Palette & Slash Commands[/]")
    sage_console.print(f"[{Palette.TEXT_MUTED}]Type [bold]/[/] in the interactive prompt for live auto-completion.[/]\n")

    table = Table(
        header_style=f"bold {Palette.SAGE_PRIMARY}",
        border_style=Palette.BORDER_MUTED,
        show_edge=True,
    )
    table.add_column("Category", style=f"bold {Palette.MINT_ACCENT}", width=18)
    table.add_column("Command", style=f"bold {Palette.TEXT_LIGHT}", width=26)
    table.add_column("Description", style=f"{Palette.TEXT_MUTED}", width=40)

    # Agent & Configuration
    table.add_row("Configuration", "/setup", "Launch interactive setup wizard")
    table.add_row("Configuration", "/config [set <k> <v>]", "View or modify settings")
    table.add_row("Configuration", "/mode <safe|auto|plan>", "Switch execution mode")
    table.add_row("Configuration", "/model <name>", "Switch or view active LLM model")
    table.add_row("Configuration", "/provider <name>", "Switch provider (gemini, openai, etc.)")
    
    # Workspace & Engineering
    table.add_row("Engineering", "/dataset [path]", "Inspect dataset schema & statistics")
    table.add_row("Engineering", "/context", "View workspace repository & dataset context")
    table.add_row("Engineering", "/memory", "View task history and logged ML metrics")
    table.add_row("Engineering", "/doctor", "Run system diagnostics & health check")
    
    # Version Control
    table.add_row("Git Safety", "/diff", "View uncommitted code changes")
    table.add_row("Git Safety", "/checkpoint [msg]", "Create a manual Git checkpoint")
    table.add_row("Git Safety", "/rollback [hash]", "Revert uncommitted changes")
    
    # Session & UI
    table.add_row("Session & UI", "/cost, /usage", "Show token consumption & estimated cost")
    table.add_row("Session & UI", "/compact", "Toggle compact logo display")
    table.add_row("Session & UI", "/ascii", "Toggle ASCII symbol mode")
    table.add_row("Session & UI", "/clear", "Clear terminal and reprint startup banner")
    table.add_row("Session & UI", "/exit, /quit", "Exit SageCLI")

    sage_console.print(table)
    sage_console.print()
    sage_console.print(f"[{Palette.TEXT_MUTED}]Keyboard Shortcuts:[/] [bold]Tab[/] to complete, [bold]Ctrl+C[/] to cancel prompt, [bold]Up/Down[/] for history.")
    sage_console.print()


def display_config_table(config: SageConfig, sage_console: SageConsole):
    """Display active configuration in a structured table."""
    table = Table(
        title="[bold]SageCLI Active Configuration[/]",
        header_style=f"bold {Palette.SAGE_PRIMARY}",
        border_style=Palette.BORDER_MUTED,
        show_edge=True,
    )
    table.add_column("Setting", style=f"bold {Palette.TEXT_LIGHT}", width=20)
    table.add_column("Value", style=f"{Palette.MINT_ACCENT}", width=40)
    table.add_column("Description", style=f"{Palette.TEXT_MUTED}", width=28)

    prov_display = PROVIDER_DEFAULTS.get(config.provider, {}).get("name", config.provider)
    table.add_row("Provider", prov_display, "Active AI Provider (/provider)")
    table.add_row("Model", config.model, "Active LLM Model (/model)")
    table.add_row("Mode", config.mode, "Safe | Auto | Plan (/mode)")
    table.add_row("Workspace", config.workspace, "Project working directory")
    table.add_row("Max Iterations", str(config.max_iterations), "Max agent loop steps")
    table.add_row("Timeout (s)", str(config.timeout_seconds), "Command execution timeout")
    table.add_row("ASCII Mode", str(config.ascii_only), "Force ASCII symbols (/ascii)")
    table.add_row("API Key", mask_secret(config.api_key), "Masked API credentials")

    sage_console.print(table)
    sage_console.print(f"\n[{Palette.TEXT_MUTED}]Modify settings with: [bold]/config set <setting> <value>[/]\n")


def display_usage_stats(config: SageConfig, sage_console: SageConsole):
    """Display session token consumption and estimated cost."""
    summary = session_tracker.get_summary(config.model)
    table = Table(
        title="[bold]Session Token Usage & Cost[/]",
        header_style=f"bold {Palette.SAGE_PRIMARY}",
        border_style=Palette.BORDER_MUTED,
        show_edge=True,
    )
    table.add_column("Metric", style=f"bold {Palette.TEXT_LIGHT}", width=24)
    table.add_column("Value", style=f"{Palette.MINT_ACCENT}", width=24)

    table.add_row("Total Requests", f"{summary['requests']:,}")
    table.add_row("Prompt Tokens", f"{summary['prompt_tokens']:,}")
    table.add_row("Completion Tokens", f"{summary['completion_tokens']:,}")
    table.add_row("Total Tokens", f"{summary['total_tokens']:,}")
    table.add_row("Estimated Cost", f"${summary['estimated_cost_usd']:.4f} USD")

    sage_console.print(table)
    sage_console.print()


def run_interactive_repl(config: SageConfig, sage_console: SageConsole):
    """Run interactive engineering REPL loop with autonomous agent and slash commands."""
    try:
        session = create_prompt_session(force_ascii=config.ascii_only)
    except Exception:
        session = None

    agent = SageAgent(config=config, console=sage_console)
    permission_callback = make_permission_callback(config, sage_console)

    while True:
        try:
            if session:
                user_input = session.prompt()
            else:
                prompt_str = get_prompt_text(force_ascii=config.ascii_only)
                user_input = input(prompt_str)

            cmd = user_input.strip()
            if not cmd:
                continue

            # 1. Exit Commands
            if cmd.lower() in ("exit", "quit", ":q", "/exit", "/quit"):
                sage_console.info("Exiting SageCLI. Happy engineering!")
                break
            
            # 2. Help Command
            elif cmd.lower() in ("/help", "help", "?"):
                display_help_palette(sage_console)

            # 3. Setup Wizard
            elif cmd.lower() in ("/setup", "setup"):
                config = run_setup_wizard(console=sage_console, workspace=config.workspace)
                agent = SageAgent(config=config, console=sage_console)

            # 4. Settings & Config
            elif cmd.lower().startswith("/config") or cmd.lower().startswith("/settings"):
                parts = cmd.split()
                if len(parts) >= 4 and parts[1].lower() == "set":
                    key = parts[2].lower()
                    val = parts[3]
                    if key == "mode":
                        config.mode = val.capitalize()
                    elif key == "timeout":
                        config.timeout_seconds = int(val)
                    elif key == "max_iterations":
                        config.max_iterations = int(val)
                    elif key == "model":
                        config.model = val
                    elif key == "ascii_only":
                        config.ascii_only = val.lower() in ("true", "1", "yes")
                    config.save_project()
                    sage_console.success(f"Updated [bold]{key}[/] = {val}")
                else:
                    display_config_table(config, sage_console)

            # 5. Mode Switcher
            elif cmd.lower().startswith("/mode"):
                parts = cmd.split(maxsplit=1)
                if len(parts) > 1 and parts[1].lower() in ("safe", "auto", "plan"):
                    config.mode = parts[1].capitalize()
                    config.save_project()
                    sage_console.success(f"Switched execution mode to [bold]{config.mode}[/]")
                else:
                    sage_console.info(f"Current mode: {config.mode}. Options: safe, auto, plan. Usage: /mode <name>")

            # 6. Model Switcher
            elif cmd.lower().startswith("/model"):
                parts = cmd.split(maxsplit=1)
                if len(parts) > 1:
                    config.model = parts[1].strip()
                    config.save_project()
                    agent = SageAgent(config=config, console=sage_console)
                    sage_console.success(f"Switched model to [bold]{config.model}[/]")
                else:
                    available = PROVIDER_DEFAULTS.get(config.provider, {}).get("available_models", [config.model])
                    sage_console.info(f"Current model: [bold]{config.model}[/]")
                    sage_console.print(f"[{Palette.TEXT_MUTED}]Available models for {config.provider}:[/]")
                    for m in available:
                        sage_console.print(f"  • [bold {Palette.MINT_ACCENT}]{m}[/]")
                    sage_console.print(f"[{Palette.TEXT_MUTED}]Usage: [bold]/model <model_name>[/][/]\n")

            # 7. Provider Switcher
            elif cmd.lower().startswith("/provider"):
                parts = cmd.split(maxsplit=1)
                if len(parts) > 1 and parts[1].lower() in PROVIDER_DEFAULTS:
                    config.provider = parts[1].lower()
                    config.model = PROVIDER_DEFAULTS[config.provider]["default_model"]
                    config.save_project()
                    agent = SageAgent(config=config, console=sage_console)
                    sage_console.success(f"Switched provider to [bold]{PROVIDER_DEFAULTS[config.provider]['name']}[/] (Model: {config.model})")
                else:
                    provs = ", ".join(PROVIDER_DEFAULTS.keys())
                    sage_console.info(f"Current provider: {config.provider}. Available: {provs}. Usage: /provider <name>")

            # 8. Token & Cost Tracker
            elif cmd.lower() in ("/cost", "/usage", "cost", "usage"):
                display_usage_stats(config, sage_console)

            # 9. Doctor Health Check
            elif cmd.lower() in ("/doctor", "doctor"):
                run_doctor_checks(config, sage_console)

            # 10. Context Inspector
            elif cmd.lower() in ("/context", "context"):
                ctx = WorkspaceContext(config.workspace)
                sage_console.print(Panel(ctx.build_system_context(), title="[bold]Workspace Context[/]", border_style=Palette.BORDER_MUTED))

            # 11. Memory & State Inspector
            elif cmd.lower() in ("/memory", "memory"):
                state = agent.state
                sage_console.print()
                sage_console.info(f"Active Task: {state.active_task or 'None'}")
                sage_console.info(f"Task History: {len(state.task_history)} tasks logged")
                if state.metrics:
                    sage_console.success(f"Logged Metrics: {state.metrics}")
                sage_console.print()

            # 12. Dataset Tool
            elif cmd.lower().startswith("/dataset"):
                parts = cmd.split(maxsplit=1)
                if len(parts) > 1:
                    ds_path = parts[1].strip()
                    res = default_registry.dispatch("inspect_dataset", config.workspace, {"path": ds_path})
                    sage_console.print(res.output if res.success else f"[{Palette.ERROR}]{res.error}[/]")
                else:
                    ctx = WorkspaceContext(config.workspace)
                    datasets = ctx.scan_datasets()
                    sage_console.info(f"Detected datasets: {', '.join(datasets) if datasets else 'None found in workspace'}")

            # 13. Git Diff
            elif cmd.lower() in ("/diff", "diff"):
                res = default_registry.dispatch("git_diff", config.workspace, {})
                sage_console.print(res.output if res.success else f"[{Palette.ERROR}]{res.error}[/]")

            # 14. Git Checkpoint
            elif cmd.lower().startswith("/checkpoint"):
                parts = cmd.split(maxsplit=1)
                msg = parts[1] if len(parts) > 1 else "manual checkpoint"
                res = default_registry.dispatch("git_checkpoint", config.workspace, {"message": msg})
                sage_console.print(res.output if res.success else f"[{Palette.ERROR}]{res.error}[/]")

            # 15. Git Rollback
            elif cmd.lower().startswith("/rollback"):
                parts = cmd.split(maxsplit=1)
                commit = parts[1] if len(parts) > 1 else None
                res = default_registry.dispatch("git_rollback", config.workspace, {"commit_hash": commit} if commit else {})
                sage_console.print(res.output if res.success else f"[{Palette.ERROR}]{res.error}[/]")

            # 16. Toggle Compact Mode
            elif cmd.lower() in ("/compact", "compact"):
                config.save_project()
                sage_console.success("Toggled compact mode.")

            # 17. Toggle ASCII Mode
            elif cmd.lower() in ("/ascii", "ascii"):
                config.ascii_only = not config.ascii_only
                config.save_project()
                mode_str = "ASCII Mode" if config.ascii_only else "Unicode Mode"
                sage_console.success(f"Switched symbol mode to [bold]{mode_str}[/]")

            # 18. Demo
            elif cmd.lower() in ("/demo", "demo"):
                run_demo_workflow(sage_console)

            # 19. Clear Screen
            elif cmd.lower() in ("/clear", "clear"):
                os.system("clear" if os.name != "nt" else "cls")
                render_startup_screen(
                    console=sage_console.console,
                    workspace=config.workspace,
                    provider=PROVIDER_DEFAULTS.get(config.provider, {}).get("name", config.provider),
                    model=config.model,
                    mode=config.mode,
                    version=config.version,
                    force_ascii=config.ascii_only,
                )

            else:
                # Dispatch autonomous engineering task
                agent.run_task(cmd, permission_callback=permission_callback)

        except (KeyboardInterrupt, EOFError):
            sage_console.print()
            sage_console.info("Session terminated.")
            break


def run_demo_workflow(sage_console: SageConsole):
    """Demonstrate SageCLI visual language."""
    sage_console.print()
    sage_console.active("Agent initializing ML pipeline workflow")
    sage_console.success("Workspace initialized")
    sage_console.success("Project structure created")
    sage_console.action("Inspecting dataset")
    sage_console.action("Building preprocessing pipeline")
    sage_console.running("Training model (LightGBM & XGBoost ensemble)")
    sage_console.success("Model trained successfully (Val ROC-AUC: 0.942)")
    sage_console.action("Evaluating test metrics and feature importance")
    sage_console.info("Artifacts saved to ./models/churn_detector_v1.pkl")
    sage_console.success("Deployment ready with FastAPI endpoint")
    sage_console.print()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    prompt: Optional[List[str]] = typer.Argument(
        None,
        help="Engineering task or prompt to run directly",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show SageCLI version and exit",
        callback=version_callback,
        is_eager=True,
    ),
    logo: Optional[bool] = typer.Option(
        None,
        "--logo",
        help="Display the official SageCLI ASCII logo and exit",
        callback=logo_callback,
        is_eager=True,
    ),
    ascii_mode: bool = typer.Option(
        False,
        "--ascii",
        help="Force standard ASCII characters instead of Unicode",
    ),
    compact: bool = typer.Option(
        False,
        "--compact",
        help="Force compact logo display",
    ),
):
    """
    SageCLI - Autonomous AI Engineering Agent for Machine Learning & Deep Learning.
    """
    if ctx.invoked_subcommand is not None:
        return

    config = SageConfig.load()
    if ascii_mode:
        config.ascii_only = True

    sage_console = SageConsole(force_ascii=config.ascii_only)

    # Check for direct subcommands passed as positional arguments
    if prompt and len(prompt) == 1:
        cmd_arg = prompt[0].lower().lstrip("/")
        if cmd_arg == "demo":
            run_demo_workflow(sage_console)
            return
        elif cmd_arg == "doctor":
            run_doctor_checks(config, sage_console)
            return
        elif cmd_arg == "setup":
            run_setup_wizard(console=sage_console, workspace=config.workspace)
            return
        elif cmd_arg in ("config", "settings"):
            display_config_table(config, sage_console)
            return
        elif cmd_arg in ("cost", "usage"):
            display_usage_stats(config, sage_console)
            return
        elif cmd_arg == "help":
            display_help_palette(sage_console)
            return

    # Check if first-run setup is required
    if not config.is_configured() and sys.stdin.isatty():
        config = run_setup_wizard(console=sage_console, workspace=config.workspace)

    # If prompt arguments were provided, execute prompt directly with agent
    if prompt:
        prompt_str = " ".join(prompt)
        agent = SageAgent(config=config, console=sage_console)
        permission_callback = make_permission_callback(config, sage_console)
        agent.run_task(prompt_str, permission_callback=permission_callback)
        return

    # Otherwise, display startup screen and launch interactive session
    prov_display = PROVIDER_DEFAULTS.get(config.provider, {}).get("name", config.provider)
    render_startup_screen(
        console=sage_console.console,
        workspace=config.workspace,
        provider=prov_display,
        model=config.model,
        mode=config.mode,
        version=config.version,
        force_ascii=config.ascii_only,
        force_compact=compact,
    )

    if sys.stdin.isatty():
        run_interactive_repl(config, sage_console)


@app.command(name="setup")
def setup_command():
    """Run interactive setup wizard to configure API keys, models, and providers."""
    sage_console = SageConsole()
    run_setup_wizard(console=sage_console)


@app.command(name="demo")
def demo_command(
    ascii_mode: bool = typer.Option(False, "--ascii", help="Force ASCII symbols")
):
    """Run a demonstration of the SageCLI visual language and status indicators."""
    sage_console = SageConsole(force_ascii=ascii_mode)
    run_demo_workflow(sage_console)


@app.command(name="doctor")
def doctor_command():
    """Run system diagnostics and environment health check."""
    config = SageConfig.load()
    sage_console = SageConsole()
    run_doctor_checks(config, sage_console)


if __name__ == "__main__":
    app()
