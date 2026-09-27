"""Workspace scanner and contextual environment analyzer for ML/DL projects."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any


class WorkspaceContext:
    """Gathers repository context, dataset files, environment specs, and CUDA status."""

    def __init__(self, workspace: str):
        self.workspace = Path(workspace).resolve()

    def scan_datasets(self) -> List[str]:
        """Find data files in workspace."""
        extensions = {".csv", ".tsv", ".parquet", ".pq", ".json", ".jsonl", ".xlsx", ".npy", ".npz"}
        datasets = []
        try:
            for p in self.workspace.rglob("*"):
                if p.is_file() and p.suffix.lower() in extensions:
                    # Ignore .git, .sage, .venv
                    if not any(part.startswith((".", "venv", "__pycache__")) for part in p.relative_to(self.workspace).parts):
                        datasets.append(str(p.relative_to(self.workspace)))
        except Exception:
            pass
        return sorted(datasets)

    def scan_project_tree(self, max_files: int = 50) -> str:
        """Return concise directory layout."""
        lines = []
        count = 0
        ignore = {".git", ".sage", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules"}

        for root, dirs, files in os.walk(self.workspace):
            dirs[:] = [d for d in dirs if d not in ignore and not d.startswith(".")]
            rel_dir = os.path.relpath(root, self.workspace)
            level = rel_dir.count(os.sep) if rel_dir != "." else 0
            indent = "  " * level
            if rel_dir != ".":
                lines.append(f"{indent}📁 {os.path.basename(root)}/")
            for f in sorted(files):
                if f.startswith(".") or f.endswith((".pyc", ".pyo")):
                    continue
                lines.append(f"{indent}  📄 {f}")
                count += 1
                if count >= max_files:
                    lines.append(f"{indent}  ... (truncated after {max_files} files)")
                    return "\n".join(lines)
        return "\n".join(lines) if lines else "(empty directory)"

    def detect_environment(self) -> Dict[str, Any]:
        """Detect Python version, CUDA/GPU capability, and installed key ML packages."""
        info: Dict[str, Any] = {
            "python": subprocess.getoutput("python3 --version") or "unknown",
            "cuda_available": False,
            "gpu_name": None,
            "installed_ml_packages": [],
        }

        # Check GPU via nvidia-smi
        if shutil.which("nvidia-smi"):
            try:
                gpu_out = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                    text=True,
                    timeout=2,
                ).strip()
                if gpu_out:
                    info["cuda_available"] = True
                    info["gpu_name"] = gpu_out
            except Exception:
                pass

        # Check key ML packages
        key_pkgs = ["torch", "tensorflow", "scikit-learn", "xgboost", "lightgbm", "catboost", "pandas", "numpy", "fastapi"]
        for pkg in key_pkgs:
            try:
                __import__(pkg)
                info["installed_ml_packages"].append(pkg)
            except Exception:
                pass

        return info

    def build_system_context(self) -> str:
        """Construct prompt system context describing current workspace and environment."""
        env = self.detect_environment()
        datasets = self.scan_datasets()
        tree = self.scan_project_tree(max_files=40)

        parts = [
            f"Workspace Root: {self.workspace}",
            f"Environment: {env['python']} | GPU: {env.get('gpu_name') or 'CPU only'}",
            f"Installed ML Stack: {', '.join(env['installed_ml_packages']) if env['installed_ml_packages'] else 'standard Python'}",
        ]

        if datasets:
            parts.append(f"Detected Datasets: {', '.join(datasets)}")
        else:
            parts.append("Detected Datasets: None found in workspace root.")

        parts.append(f"\nProject Structure:\n{tree}")
        return "\n".join(parts)
