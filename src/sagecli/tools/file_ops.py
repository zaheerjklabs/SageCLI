"""File system manipulation tools for reading, writing, patching, and listing files."""

from pathlib import Path
from typing import Optional
from sagecli.tools.base import BaseTool, ToolResult
from sagecli.security import is_path_safe


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read the contents of a file in the workspace with line numbers."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file relative to workspace root"},
            "start_line": {"type": "integer", "description": "Starting line number (1-indexed, optional)"},
            "end_line": {"type": "integer", "description": "Ending line number (inclusive, optional)"},
        },
        "required": ["path"],
    }
    is_destructive = False
    requires_approval_in_safe_mode = False

    def execute(self, workspace: str, path: str, start_line: Optional[int] = None, end_line: Optional[int] = None, **kwargs) -> ToolResult:
        safe, msg = is_path_safe(path, workspace)
        if not safe:
            return ToolResult(success=False, output="", error=msg)

        target = (Path(workspace) / path).resolve()
        if not target.exists():
            return ToolResult(success=False, output="", error=f"File not found: '{path}'")
        if not target.is_file():
            return ToolResult(success=False, output="", error=f"Path is not a file: '{path}'")

        try:
            content = target.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            total_lines = len(lines)

            s = max(1, start_line or 1)
            e = min(total_lines, end_line or total_lines)

            if s > total_lines:
                return ToolResult(success=True, output=f"File has {total_lines} lines (start_line {s} out of bounds).")

            selected = lines[s - 1:e]
            numbered = [f"{i:4d} | {line}" for i, line in enumerate(selected, start=s)]
            output = f"File: {path} (Lines {s}-{e} of {total_lines})\n" + "\n".join(numbered)
            return ToolResult(success=True, output=output)
        except Exception as exc:
            return ToolResult(success=False, output="", error=f"Error reading file '{path}': {exc}")


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write or overwrite full contents to a file in the workspace. Auto-creates directories."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Target relative file path"},
            "content": {"type": "string", "description": "Full file content to write"},
        },
        "required": ["path", "content"],
    }
    is_destructive = True
    requires_approval_in_safe_mode = True

    def execute(self, workspace: str, path: str, content: str, **kwargs) -> ToolResult:
        safe, msg = is_path_safe(path, workspace)
        if not safe:
            return ToolResult(success=False, output="", error=msg)

        target = (Path(workspace) / path).resolve()
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            existed = target.exists()
            target.write_text(content, encoding="utf-8")
            line_count = len(content.splitlines())
            action = "Updated" if existed else "Created"
            return ToolResult(success=True, output=f"✓ {action} file '{path}' ({line_count} lines, {len(content)} bytes).")
        except Exception as exc:
            return ToolResult(success=False, output="", error=f"Failed to write file '{path}': {exc}")


class PatchFileTool(BaseTool):
    name = "patch_file"
    description = "Surgically replace an exact block of text in a file."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Target relative file path"},
            "target_content": {"type": "string", "description": "Exact existing text to be replaced"},
            "replacement_content": {"type": "string", "description": "New replacement text"},
        },
        "required": ["path", "target_content", "replacement_content"],
    }
    is_destructive = True
    requires_approval_in_safe_mode = True

    def execute(self, workspace: str, path: str, target_content: str, replacement_content: str, **kwargs) -> ToolResult:
        safe, msg = is_path_safe(path, workspace)
        if not safe:
            return ToolResult(success=False, output="", error=msg)

        target = (Path(workspace) / path).resolve()
        if not target.exists() or not target.is_file():
            return ToolResult(success=False, output="", error=f"File '{path}' does not exist.")

        try:
            content = target.read_text(encoding="utf-8")
            if target_content not in content:
                return ToolResult(success=False, output="", error=f"Target content not found in '{path}'. Make sure exact characters match.")
            
            count = content.count(target_content)
            if count > 1:
                return ToolResult(success=False, output="", error=f"Target content occurs {count} times in '{path}'. Please provide more surrounding lines for unique match.")

            new_content = content.replace(target_content, replacement_content, 1)
            target.write_text(new_content, encoding="utf-8")
            return ToolResult(success=True, output=f"✓ Successfully patched '{path}'.")
        except Exception as exc:
            return ToolResult(success=False, output="", error=f"Failed to patch file '{path}': {exc}")


class ListDirectoryTool(BaseTool):
    name = "list_directory"
    description = "List files and directories in the workspace with sizes and types."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative directory path (default: root '.')"},
            "max_depth": {"type": "integer", "description": "Maximum tree recursion depth (default: 2)"},
        },
        "required": [],
    }
    is_destructive = False
    requires_approval_in_safe_mode = False

    IGNORE_DIRS = {".git", ".sage", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules", ".eggs"}

    def execute(self, workspace: str, path: str = ".", max_depth: int = 2, **kwargs) -> ToolResult:
        safe, msg = is_path_safe(path, workspace)
        if not safe:
            return ToolResult(success=False, output="", error=msg)

        target = (Path(workspace) / path).resolve()
        if not target.exists() or not target.is_dir():
            return ToolResult(success=False, output="", error=f"Directory '{path}' not found.")

        tree_lines = []

        def build_tree(current_dir: Path, prefix: str = "", depth: int = 0):
            if depth > max_depth:
                return
            try:
                entries = sorted(list(current_dir.iterdir()), key=lambda p: (not p.is_dir(), p.name.lower()))
                entries = [e for e in entries if e.name not in self.IGNORE_DIRS]
                for i, entry in enumerate(entries):
                    is_last = (i == len(entries) - 1)
                    connector = "└── " if is_last else "├── "
                    sub_prefix = "    " if is_last else "│   "
                    
                    if entry.is_dir():
                        tree_lines.append(f"{prefix}{connector}{entry.name}/")
                        build_tree(entry, prefix + sub_prefix, depth + 1)
                    else:
                        size = entry.stat().st_size
                        size_str = f"{size} B" if size < 1024 else f"{size/1024:.1f} KB"
                        tree_lines.append(f"{prefix}{connector}{entry.name} ({size_str})")
            except Exception:
                pass

        tree_lines.append(f"{path}/")
        build_tree(target, "", 1)
        return ToolResult(success=True, output="\n".join(tree_lines))
