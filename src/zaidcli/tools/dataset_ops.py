"""Dataset inspection and exploratory data analysis tool for ML/DL pipelines."""

from pathlib import Path
from typing import Optional

from sagecli.tools.base import BaseTool, ToolResult
from sagecli.security import is_path_safe


class InspectDatasetTool(BaseTool):
    name = "inspect_dataset"
    description = "Inspect and analyze a dataset file (CSV, Parquet, JSON, TSV, NumPy, etc.) to get shape, schema, missing values, statistics, and sample rows."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative path to dataset file (e.g. 'data/raw/churn.csv')"},
            "sample_rows": {"type": "integer", "description": "Number of sample rows to preview (default: 5)"},
            "target_column": {"type": "string", "description": "Target/label column name for distribution analysis (optional)"},
        },
        "required": ["path"],
    }
    is_destructive = False
    requires_approval_in_safe_mode = False

    def execute(self, workspace: str, path: str, sample_rows: int = 5, target_column: Optional[str] = None, **kwargs) -> ToolResult:
        safe, msg = is_path_safe(path, workspace)
        if not safe:
            return ToolResult(success=False, output="", error=msg)

        target = (Path(workspace) / path).resolve()
        if not target.exists() or not target.is_file():
            return ToolResult(success=False, output="", error=f"Dataset file '{path}' does not exist.")

        file_ext = target.suffix.lower()

        try:
            import pandas as pd
            import numpy as np

            # Load dataset according to format
            if file_ext in (".csv", ".txt"):
                # Try comma, then tab, then semicolon delimiter
                try:
                    df = pd.read_csv(target, nrows=50000)
                except Exception:
                    df = pd.read_csv(target, sep=None, engine="python", nrows=50000)
            elif file_ext in (".tsv",):
                df = pd.read_csv(target, sep="\t", nrows=50000)
            elif file_ext in (".parquet", ".pq"):
                df = pd.read_parquet(target)
            elif file_ext in (".json", ".jsonl"):
                try:
                    df = pd.read_json(target, lines=True, nrows=50000)
                except Exception:
                    df = pd.read_json(target)
            elif file_ext in (".xlsx", ".xls"):
                df = pd.read_excel(target, nrows=50000)
            elif file_ext in (".npy", ".npz"):
                arr = np.load(target)
                if isinstance(arr, np.ndarray):
                    return ToolResult(
                        success=True,
                        output=f"NumPy Array: Shape={arr.shape}, Dtype={arr.dtype}, Min={np.min(arr)}, Max={np.max(arr)}, Mean={np.mean(arr):.4f}",
                    )
                else:
                    keys = list(arr.keys())
                    return ToolResult(
                        success=True,
                        output=f"NumPy NPZ Archive: Keys={keys}",
                    )
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Unsupported dataset format '{file_ext}'. Supported: CSV, TSV, Parquet, JSON, Excel, NumPy.",
                )

            # Analyze DataFrame
            rows, cols = df.shape
            mem_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)

            report = []
            report.append("═══════════════════════════════════════════════════════════════════")
            report.append(f"DATASET INSPECTION REPORT: {path}")
            report.append(f"Dimensions: {rows:,} rows × {cols} columns | Memory: {mem_mb:.2f} MB")
            report.append("═══════════════════════════════════════════════════════════════════\n")

            # Column Types & Nulls
            report.append("--- SCHEMA & MISSING VALUES ---")
            null_counts = df.isnull().sum()
            for col in df.columns:
                nulls = null_counts[col]
                null_pct = (nulls / rows) * 100 if rows > 0 else 0
                dtype_str = str(df[col].dtype)
                unique_cnt = df[col].nunique()
                report.append(f"  • {col:<25} | Type: {dtype_str:<10} | Missing: {nulls:,} ({null_pct:.1f}%) | Unique: {unique_cnt:,}")

            # Numerical Summary
            numeric_df = df.select_dtypes(include=[np.number])
            if not numeric_df.empty:
                report.append("\n--- NUMERICAL FEATURE STATISTICS ---")
                stats = numeric_df.describe().T[["mean", "std", "min", "50%", "max"]]
                stats.columns = ["Mean", "Std", "Min", "Median", "Max"]
                report.append(stats.to_string())

            # Categorical Summary
            cat_df = df.select_dtypes(include=["object", "string", "category", "bool"])
            if not cat_df.empty:
                report.append("\n--- CATEGORICAL FEATURE CARDINALITY ---")
                for col in cat_df.columns[:8]:
                    top_vals = df[col].value_counts(dropna=False).head(3).to_dict()
                    top_str = ", ".join([f"{k}: {v}" for k, v in top_vals.items()])
                    report.append(f"  • {col}: [{top_str}]")

            # Target Column Analysis
            if target_column and target_column in df.columns:
                report.append(f"\n--- TARGET VARIABLE DISTRIBUTION ({target_column}) ---")
                t_counts = df[target_column].value_counts(dropna=False)
                for k, v in t_counts.items():
                    pct = (v / rows) * 100
                    report.append(f"  {k}: {v:,} ({pct:.2f}%)")

            # Sample Preview Rows
            report.append(f"\n--- SAMPLE PREVIEW (Top {min(sample_rows, rows)} rows) ---")
            report.append(df.head(sample_rows).to_string(index=False))

            return ToolResult(
                success=True,
                output="\n".join(report),
                data={
                    "rows": rows,
                    "columns": list(df.columns),
                    "dtypes": {c: str(df[c].dtype) for c in df.columns},
                    "missing": {c: int(null_counts[c]) for c in df.columns},
                },
            )

        except Exception as exc:
            return ToolResult(success=False, output="", error=f"Failed to inspect dataset '{path}': {exc}")
