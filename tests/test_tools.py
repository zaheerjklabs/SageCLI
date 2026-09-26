"""Unit tests for SageCLI tools and registry."""

import pandas as pd

from sagecli.tools.file_ops import ReadFileTool, WriteFileTool, PatchFileTool, ListDirectoryTool
from sagecli.tools.shell_ops import ExecuteCommandTool
from sagecli.tools.dataset_ops import InspectDatasetTool
from sagecli.tools.registry import ToolRegistry


def test_file_ops(tmp_path):
    """Verify write, read, patch, and list file operations."""
    ws = str(tmp_path)
    
    # 1. Write file
    writer = WriteFileTool()
    w_res = writer.execute(workspace=ws, path="src/main.py", content="x = 10\ny = 20\n")
    assert w_res.success is True
    assert (tmp_path / "src" / "main.py").exists()

    # 2. Read file
    reader = ReadFileTool()
    r_res = reader.execute(workspace=ws, path="src/main.py")
    assert r_res.success is True
    assert "x = 10" in r_res.output

    # 3. Patch file
    patcher = PatchFileTool()
    p_res = patcher.execute(workspace=ws, path="src/main.py", target_content="y = 20", replacement_content="y = 30")
    assert p_res.success is True
    r_res2 = reader.execute(workspace=ws, path="src/main.py")
    assert "y = 30" in r_res2.output
    assert "y = 20" not in r_res2.output

    # 4. List directory
    lister = ListDirectoryTool()
    l_res = lister.execute(workspace=ws, path=".")
    assert l_res.success is True
    assert "main.py" in l_res.output


def test_execute_command(tmp_path):
    """Verify shell command execution tool."""
    ws = str(tmp_path)
    exec_tool = ExecuteCommandTool()
    
    # Successful command
    res = exec_tool.execute(workspace=ws, command="python3 -c 'print(10 + 20)'")
    assert res.success is True
    assert "30" in res.output

    # Failing command
    res_fail = exec_tool.execute(workspace=ws, command="python3 -c 'raise ValueError(\"test error\")'")
    assert res_fail.success is False
    assert "ValueError: test error" in res_fail.output


def test_inspect_dataset(tmp_path):
    """Verify dataset inspection tool on CSV dataset."""
    ws = str(tmp_path)
    csv_path = tmp_path / "churn.csv"
    
    df = pd.DataFrame({
        "age": [25, 45, 30, 50, 22],
        "churn": [0, 1, 0, 1, 0],
        "city": ["NY", "SF", "NY", "LA", "SF"],
    })
    df.to_csv(csv_path, index=False)

    inspector = InspectDatasetTool()
    res = inspector.execute(workspace=ws, path="churn.csv", target_column="churn")
    assert res.success is True
    assert "5 rows × 3 columns" in res.output
    assert "DATASET INSPECTION REPORT" in res.output
    assert "TARGET VARIABLE DISTRIBUTION (churn)" in res.output


def test_registry_permissions():
    """Verify registry permissions in Safe, Auto, and Plan modes."""
    reg = ToolRegistry()
    schemas = reg.get_schemas()
    assert len(schemas) >= 9

    # Plan Mode should disallow write_file and execute_command
    can_write_plan, _ = reg.can_execute("write_file", mode="Plan")
    assert can_write_plan is False
    
    # Plan Mode allows read_file
    can_read_plan, _ = reg.can_execute("read_file", mode="Plan")
    assert can_read_plan is True

    # Safe Mode asks callback
    callback_calls = []
    def mock_callback(tool, args):
        callback_calls.append(tool)
        return True

    can_write_safe, _ = reg.can_execute("write_file", mode="Safe", permission_callback=mock_callback)
    assert can_write_safe is True
    assert "write_file" in callback_calls
