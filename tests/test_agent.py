"""Unit tests for SageAgent autonomous loop and state tracking."""

from typing import List, Dict, Any, Optional

from sagecli.config import SageConfig
from sagecli.llm.base import BaseLLMProvider, Message, LLMResponse, ToolCall
from sagecli.core.agent import SageAgent
from sagecli.core.state import ProjectState, TaskStep
from sagecli.core.context import WorkspaceContext
from sagecli.ui.console import SageConsole


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider that simulates autonomous planning, coding, and debugging."""

    def __init__(self, responses: List[LLMResponse]):
        super().__init__(api_key="mock", model="mock-model")
        self.responses = list(responses)
        self.call_count = 0
        self.received_messages: List[List[Message]] = []

    def generate(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        self.received_messages.append(messages)
        if self.call_count < len(self.responses):
            resp = self.responses[self.call_count]
            self.call_count += 1
            return resp
        return LLMResponse(content="Task completed.", tool_calls=[])

    def validate_connection(self):
        return True, "Mock connected."


def test_workspace_context_and_state(tmp_path):
    """Verify WorkspaceContext scans files and ProjectState records steps."""
    ws = tmp_path / "project"
    ws.mkdir()
    (ws / "data").mkdir()
    (ws / "data" / "raw.csv").write_text("a,b,c\n1,2,3\n")
    (ws / "train.py").write_text("print('train')\n")

    context = WorkspaceContext(str(ws))
    datasets = context.scan_datasets()
    assert "data/raw.csv" in datasets

    tree = context.scan_project_tree()
    assert "train.py" in tree

    state = ProjectState.load(str(ws))
    state.record_metric("RandomForest", "accuracy", 0.95)
    state.add_step(TaskStep(id="1", phase="Plan", description="Plan created"))
    
    # Reload from disk
    reloaded = ProjectState.load(str(ws))
    assert reloaded.metrics["RandomForest"]["accuracy"] == 0.95
    assert len(reloaded.steps) == 1


def test_agent_autonomous_execution_and_debugging(tmp_path):
    """Verify SageAgent autonomous loop: write file -> execute -> see error -> fix -> execute -> finish."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    config = SageConfig(workspace=str(ws), mode="Auto", max_iterations=10)
    console = SageConsole(force_ascii=True)

    # Step 1: Model writes buggy code
    resp1 = LLMResponse(
        content="I will write the training script.",
        tool_calls=[
            ToolCall(
                id="call_1",
                name="write_file",
                arguments={"path": "train.py", "content": "import math\nprint(undefined_variable)\n"},
            )
        ],
    )

    # Step 2: Model executes the buggy script
    resp2 = LLMResponse(
        content="Now executing training script.",
        tool_calls=[
            ToolCall(
                id="call_2",
                name="execute_command",
                arguments={"command": "python3 train.py"},
            )
        ],
    )

    # Step 3: Model sees NameError in tool output and patches the file
    resp3 = LLMResponse(
        content="Detected NameError. Fixing variable definition.",
        tool_calls=[
            ToolCall(
                id="call_3",
                name="write_file",
                arguments={"path": "train.py", "content": "import math\nundefined_variable = 42\nprint(f'Trained with {undefined_variable}')\n"},
            )
        ],
    )

    # Step 4: Model re-executes the fixed script
    resp4 = LLMResponse(
        content="Re-running fixed training script.",
        tool_calls=[
            ToolCall(
                id="call_4",
                name="execute_command",
                arguments={"command": "python3 train.py"},
            )
        ],
    )

    # Step 5: Model finishes
    resp5 = LLMResponse(
        content="Model trained successfully with value 42.",
        tool_calls=[],
    )

    mock_llm = MockLLMProvider([resp1, resp2, resp3, resp4, resp5])
    agent = SageAgent(config=config, provider=mock_llm, console=console)

    final = agent.run_task("Train the model")
    assert "Model trained successfully" in final

    # Check file exists and has fixed content
    train_file = ws / "train.py"
    assert train_file.exists()
    assert "undefined_variable = 42" in train_file.read_text()
