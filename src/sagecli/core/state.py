"""Project state, conversation history, task memory, and metrics persistence in .sage/."""

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional



@dataclass
class TaskStep:
    """Individual step executed during an agent task."""
    id: str
    phase: str                      # 'Plan' | 'EDA' | 'Code' | 'Run' | 'Debug' | 'Eval' | 'Doc'
    description: str
    status: str = "pending"         # 'pending' | 'running' | 'success' | 'failed'
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_output: Optional[str] = None
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class ProjectState:
    """Project memory and metadata stored in .sage/."""
    workspace: str
    active_task: Optional[str] = None
    task_history: List[str] = field(default_factory=list)
    steps: List[TaskStep] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    known_datasets: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    @classmethod
    def load(cls, workspace: str) -> "ProjectState":
        ws_path = Path(workspace).resolve()
        sage_dir = ws_path / ".sage"
        sage_dir.mkdir(parents=True, exist_ok=True)
        state_file = sage_dir / "state.json"

        if state_file.exists():
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    steps_raw = data.get("steps", [])
                    steps = [TaskStep(**s) for s in steps_raw]
                    data["steps"] = steps
                    return cls(**data)
            except Exception:
                pass

        return cls(workspace=str(ws_path))

    def save(self) -> None:
        ws_path = Path(self.workspace).resolve()
        sage_dir = ws_path / ".sage"
        sage_dir.mkdir(parents=True, exist_ok=True)
        state_file = sage_dir / "state.json"

        self.updated_at = time.time()
        payload = {
            "workspace": self.workspace,
            "active_task": self.active_task,
            "task_history": self.task_history,
            "steps": [asdict(s) for s in self.steps],
            "metrics": self.metrics,
            "known_datasets": self.known_datasets,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def add_step(self, step: TaskStep) -> None:
        self.steps.append(step)
        self.save()

    def record_metric(self, model_name: str, metric_name: str, value: float) -> None:
        if model_name not in self.metrics:
            self.metrics[model_name] = {}
        self.metrics[model_name][metric_name] = value
        self.save()
