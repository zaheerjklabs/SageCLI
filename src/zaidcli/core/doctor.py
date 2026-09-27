"""System diagnostics and environment health check for SageCLI."""

import shutil
import subprocess
import sys
import time
from rich.table import Table

from sagecli.config import SageConfig, PROVIDER_DEFAULTS
from sagecli.llm.factory import create_llm_provider
from sagecli.ui.theme import Palette
from sagecli.ui.console import SageConsole




def run_doctor_checks(config: SageConfig, console: SageConsole) -> None:
    """Run comprehensive system health checks and print diagnostics."""
    console.print()
    console.active("Running SageCLI System Diagnostics & Health Check...")
    console.print()

    table = Table(
        title="[bold]SageCLI Environment Diagnostics[/]",
        header_style=f"bold {Palette.SAGE_PRIMARY}",
        border_style=Palette.BORDER_MUTED,
        show_edge=True,
    )
    table.add_column("Component", style=f"bold {Palette.TEXT_LIGHT}", width=22)
    table.add_column("Status", width=14)
    table.add_column("Details", style=f"{Palette.TEXT_MUTED}", width=46)

    # 1. Python Environment
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    venv_str = "Virtualenv Active" if in_venv else "Global / Conda Environment"
    table.add_row("Python", f"[{Palette.SUCCESS}]✓ OK[/]", f"v{py_ver} ({venv_str})")

    # 2. Git Repository
    git_installed = bool(shutil.which("git"))
    if git_installed:
        try:
            status = subprocess.run(["git", "status", "-s"], cwd=config.workspace, capture_output=True, text=True)
            if status.returncode == 0:
                table.add_row("Git Repository", f"[{Palette.SUCCESS}]✓ OK[/]", "Initialized and accessible")
            else:
                table.add_row("Git Repository", f"[{Palette.WARNING}]⚠ Warning[/]", "Not a git repository (run git init)")
        except Exception:
            table.add_row("Git Repository", f"[{Palette.WARNING}]⚠ Warning[/]", "Unable to check git status")
    else:
        table.add_row("Git", f"[{Palette.ERROR}]✗ Missing[/]", "git CLI not found in PATH")

    # 3. GPU / Hardware Acceleration
    has_nvidia = bool(shutil.which("nvidia-smi"))
    if has_nvidia:
        try:
            gpu_out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                text=True,
                timeout=2,
            ).strip()
            table.add_row("GPU / CUDA", f"[{Palette.SUCCESS}]✓ Detected[/]", gpu_out)
        except Exception:
            table.add_row("GPU / CUDA", f"[{Palette.WARNING}]⚠ Warning[/]", "nvidia-smi error")
    else:
        table.add_row("GPU / CUDA", f"[{Palette.INFO}]• CPU Mode[/]", "No NVIDIA GPU detected; running on CPU")

    # 4. LLM Provider API Connectivity
    prov_name = PROVIDER_DEFAULTS.get(config.provider, {}).get("name", config.provider)
    provider_inst = create_llm_provider(config)
    t0 = time.time()
    valid, val_msg = provider_inst.validate_connection()
    latency = (time.time() - t0) * 1000

    if valid:
        table.add_row("LLM Provider", f"[{Palette.SUCCESS}]✓ Connected[/]", f"{prov_name} ({config.model}) ~{latency:.0f}ms")
    else:
        table.add_row("LLM Provider", f"[{Palette.ERROR}]✗ Error[/]", f"{prov_name}: {val_msg[:40]}")

    # 5. Core ML Stack Libraries
    ml_packages = [
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
        ("scikit-learn", "Scikit-Learn"),
        ("torch", "PyTorch"),
        ("xgboost", "XGBoost"),
        ("lightgbm", "LightGBM"),
        ("fastapi", "FastAPI"),
    ]
    
    installed_pkgs = []
    missing_pkgs = []
    for mod_name, disp_name in ml_packages:
        try:
            __import__(mod_name)
            installed_pkgs.append(disp_name)
        except Exception:
            missing_pkgs.append(disp_name)

    pkg_summary = f"{len(installed_pkgs)}/7 installed ({', '.join(installed_pkgs[:4])}...)"
    status_pkgs = f"[{Palette.SUCCESS}]✓ Ready[/]" if len(installed_pkgs) >= 3 else f"[{Palette.WARNING}]⚠ Partial[/]"
    table.add_row("ML Libraries", status_pkgs, pkg_summary)

    # 6. Workspace Storage
    try:
        total, used, free = shutil.disk_usage(config.workspace)
        free_gb = free // (2**30)
        table.add_row("Workspace Disk", f"[{Palette.SUCCESS}]✓ OK[/]", f"{free_gb} GB free space available")
    except Exception:
        pass

    console.print(table)
    console.print()

    # Recommendations
    if not valid:
        console.warning("Recommendation: Run [bold]/setup[/] or [bold]/provider[/] to reconfigure your API credentials.")
    if missing_pkgs and "PyTorch" in missing_pkgs and "XGBoost" in missing_pkgs:
        console.info("Recommendation: You can install ML packages anytime via prompt or pip (e.g. `pip install torch xgboost`).")
    console.print()
