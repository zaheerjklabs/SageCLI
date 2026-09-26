"""Interactive setup wizard for first-run configuration and `sage setup`."""

import os
import getpass
from typing import Optional
from rich.table import Table
from rich.prompt import Prompt, Confirm

from sagecli.config import SageConfig, PROVIDER_DEFAULTS
from sagecli.ui.theme import Palette
from sagecli.ui.console import SageConsole
from sagecli.llm.factory import create_llm_provider
from sagecli.security import mask_secret


def run_setup_wizard(console: Optional[SageConsole] = None, workspace: Optional[str] = None) -> SageConfig:
    """Run interactive setup wizard for SageCLI."""
    c = console or SageConsole()
    cfg = SageConfig.load(workspace)

    c.print()
    c.print(f"[{Palette.SAGE_PRIMARY} bold]Welcome to SageCLI Setup Wizard[/]")
    c.print(f"[{Palette.TEXT_MUTED}]Configure your AI engineering agent in just a few steps.[/]\n")

    # Step 1: Detect existing keys
    c.info("Detecting configured environment keys...")
    provider_keys_list = list(PROVIDER_DEFAULTS.keys())

    table = Table(show_header=True, header_style=f"bold {Palette.SAGE_PRIMARY}", box=None)
    table.add_column("#", style=f"{Palette.MINT_ACCENT}", width=4)
    table.add_column("Provider", style=f"bold {Palette.TEXT_LIGHT}", width=24)
    table.add_column("Default Model", style=f"{Palette.TEXT_MUTED}", width=26)
    table.add_column("Status", width=18)

    for i, prov in enumerate(provider_keys_list, start=1):
        info = PROVIDER_DEFAULTS[prov]
        env_var = info["env_var"]
        has_key = bool(os.environ.get(env_var) or cfg.provider_keys.get(prov))
        
        status = f"[{Palette.SUCCESS}]✓ Detected ({env_var})[/]" if has_key else f"[{Palette.TEXT_MUTED}]Not configured[/]"
        if prov == "ollama":
            status = f"[{Palette.MINT_ACCENT}]Local server[/]"

        table.add_row(str(i), info["name"], info["default_model"], status)

    c.print(table)
    c.print()

    # Step 2: Choose provider
    c.action("Select your LLM Provider:")
    default_choice = "1"
    # If gemini or openai detected, default to that
    for i, prov in enumerate(provider_keys_list, start=1):
        if prov in cfg.provider_keys and cfg.provider_keys[prov]:
            default_choice = str(i)
            break

    choice_str = Prompt.ask(
        f"[{Palette.TEXT_LIGHT}]Enter provider number (1-{len(provider_keys_list)})[/]",
        default=default_choice,
    )
    try:
        choice_idx = int(choice_str) - 1
        if 0 <= choice_idx < len(provider_keys_list):
            selected_prov = provider_keys_list[choice_idx]
        else:
            selected_prov = "gemini"
    except Exception:
        selected_prov = "gemini"

    prov_info = PROVIDER_DEFAULTS[selected_prov]
    c.success(f"Selected Provider: [bold]{prov_info['name']}[/]")
    c.print()

    # Step 3: Configure API Key (if not Ollama)
    existing_key = os.environ.get(prov_info["env_var"]) or cfg.provider_keys.get(selected_prov, "")
    api_key = existing_key

    if selected_prov != "ollama":
        if existing_key:
            c.info(f"Existing key found: {mask_secret(existing_key)}")
            use_existing = Confirm.ask("Use this existing API key?", default=True)
            if not use_existing:
                api_key = getpass.getpass(f"Enter {prov_info['name']} API key: ").strip()
        else:
            api_key = getpass.getpass(f"Enter {prov_info['name']} API key ({prov_info['env_var']}): ").strip()

    # Step 4: Configure Model
    c.print()
    c.action(f"Select Model for {prov_info['name']}:")
    models = prov_info.get("available_models", [prov_info["default_model"]])
    for i, m in enumerate(models, start=1):
        c.print(f"  [{Palette.MINT_ACCENT}]{i}[/] {m}")

    model_choice = Prompt.ask(
        f"[{Palette.TEXT_LIGHT}]Enter model number or custom model name[/]",
        default="1",
    )
    if model_choice.isdigit() and 1 <= int(model_choice) <= len(models):
        selected_model = models[int(model_choice) - 1]
    else:
        selected_model = model_choice.strip() or prov_info["default_model"]

    c.success(f"Selected Model: [bold]{selected_model}[/]")
    c.print()

    # Step 5: Execution Mode
    c.action("Select Execution Mode:")
    c.print(f"  [{Palette.MINT_ACCENT}]1[/] [{Palette.SUCCESS}]Safe Mode[/] (Recommended) — Prompts before write/exec actions")
    c.print(f"  [{Palette.MINT_ACCENT}]2[/] [{Palette.SAGE_LIGHT}]Auto Mode[/] — Executes autonomous steps inside workspace")
    c.print(f"  [{Palette.MINT_ACCENT}]3[/] [{Palette.TEXT_MUTED}]Plan Mode[/] — Generates plan without modifying disk")

    mode_choice = Prompt.ask("Enter mode number (1-3)", default="1")
    mode_map = {"1": "Safe", "2": "Auto", "3": "Plan"}
    selected_mode = mode_map.get(mode_choice, "Safe")
    c.success(f"Execution Mode: [bold]{selected_mode}[/]")
    c.print()

    # Step 6: Validate Connection
    c.running("Validating provider credentials...")
    test_cfg = SageConfig(
        provider=selected_prov,
        model=selected_model,
        api_key=api_key,
        mode=selected_mode,
        workspace=cfg.workspace,
    )
    provider_inst = create_llm_provider(test_cfg)
    valid, val_msg = provider_inst.validate_connection()

    if valid:
        c.success(f"API Connection Verified: {val_msg}")
    else:
        c.warning(f"Connection validation warning: {val_msg}")
        save_anyway = Confirm.ask("Do you want to save this configuration anyway?", default=True)
        if not save_anyway:
            c.info("Setup aborted without saving.")
            return cfg

    # Step 7: Save Configuration
    cfg.provider = selected_prov
    cfg.model = selected_model
    cfg.mode = selected_mode
    if api_key:
        cfg.api_key = api_key
        cfg.provider_keys[selected_prov] = api_key

    cfg.save_global()
    c.print()
    c.success("Configuration saved to ~/.sage/config.json with secure 0600 permissions.")
    c.active("SageCLI setup complete! Ready for AI engineering.")
    c.print()

    return cfg
