"""Autonomous agent core execution loop for SageCLI."""

from typing import List, Dict, Any, Optional, Callable

from sagecli.config import SageConfig
from sagecli.llm.base import BaseLLMProvider, Message, LLMResponse
from sagecli.llm.factory import create_llm_provider
from sagecli.tools.registry import ToolRegistry, default_registry
from sagecli.core.context import WorkspaceContext
from sagecli.core.state import ProjectState, TaskStep
from sagecli.core.orchestrator import build_system_message
from sagecli.ui.console import SageConsole, default_console
from sagecli.security import ensure_gitignore_has_sage


class SageAgent:
    """Autonomous tool-using AI engineering agent for ML/DL projects."""

    def __init__(
        self,
        config: Optional[SageConfig] = None,
        provider: Optional[BaseLLMProvider] = None,
        registry: Optional[ToolRegistry] = None,
        console: Optional[SageConsole] = None,
    ):
        self.config = config or SageConfig.load()
        self.provider = provider or create_llm_provider(self.config)
        self.registry = registry or default_registry
        self.console = console or default_console
        self.workspace = self.config.workspace
        self.state = ProjectState.load(self.workspace)
        self.context = WorkspaceContext(self.workspace)

        # Ensure .sage is ignored in git
        ensure_gitignore_has_sage(self.workspace)

    def run_task(
        self,
        user_prompt: str,
        permission_callback: Optional[Callable[[str, Dict[str, Any]], bool]] = None,
    ) -> str:
        """
        Execute an autonomous multi-step engineering task.
        Executes plan -> inspect -> code -> run -> debug -> test -> eval -> document.
        """
        self.console.active(f"Task: [bold]{user_prompt}[/]")
        self.state.active_task = user_prompt
        self.state.task_history.append(user_prompt)
        self.state.save()

        # Build system message with fresh workspace context
        system_content = build_system_message(self.context)
        messages: List[Message] = [
            Message(role="system", content=system_content),
            Message(role="user", content=user_prompt),
        ]

        tools_schema = self.registry.get_schemas()
        max_iterations = self.config.max_iterations
        iteration = 0
        final_answer = ""

        while iteration < max_iterations:
            iteration += 1

            # Call LLM provider
            response: LLMResponse = self.provider.generate(
                messages=messages,
                tools=tools_schema,
                temperature=0.2,
            )

            # Record token usage
            from sagecli.core.tracker import session_tracker
            session_tracker.record_usage(response.prompt_tokens, response.completion_tokens)

            if response.finish_reason == "error":
                self.console.error(f"LLM Provider Error: {response.content}")
                final_answer = response.content
                break

            # 1. Output thoughts/reasoning or answer if provided
            if response.content and response.content.strip():
                self.console.print()
                self.console.markdown(response.content)
                self.console.print()
                final_answer = response.content

            # 2. Add assistant message to conversation history
            assistant_msg = Message(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls,
                raw_parts=response.raw_parts,
            )
            messages.append(assistant_msg)

            # 3. If no tool calls, the agent has finished
            if not response.tool_calls:
                self.console.success("Task completed successfully.")
                break

            # 4. Dispatch tool calls sequentially
            for tc in response.tool_calls:
                step_id = f"step_{len(self.state.steps) + 1}"
                
                # Format friendly display
                if tc.name == "inspect_dataset":
                    ds_path = tc.arguments.get("path", "")
                    self.console.action(f"Inspecting dataset: [bold]{ds_path}[/]")
                elif tc.name == "write_file":
                    file_p = tc.arguments.get("path", "")
                    self.console.action(f"Writing file: [bold]{file_p}[/]")
                elif tc.name == "patch_file":
                    file_p = tc.arguments.get("path", "")
                    self.console.action(f"Patching file: [bold]{file_p}[/]")
                elif tc.name == "read_file":
                    file_p = tc.arguments.get("path", "")
                    self.console.info(f"Reading file: {file_p}")
                elif tc.name == "execute_command":
                    cmd = tc.arguments.get("command", "")
                    self.console.running(f"Executing: [bold]{cmd}[/]")
                elif tc.name == "run_tests":
                    self.console.running("Running automated test suite")
                elif tc.name == "git_checkpoint":
                    msg = tc.arguments.get("message", "")
                    self.console.action(f"Creating Git checkpoint: {msg}")
                else:
                    self.console.action(f"Running tool: {tc.name}")

                # Execute tool
                tool_result = self.registry.dispatch(
                    tool_name=tc.name,
                    workspace=self.workspace,
                    arguments=tc.arguments,
                    mode=self.config.mode,
                    permission_callback=permission_callback,
                )

                # Record state step
                step = TaskStep(
                    id=step_id,
                    phase="Action",
                    description=f"{tc.name}({tc.arguments})",
                    status="success" if tool_result.success else "failed",
                    tool_name=tc.name,
                    tool_args=tc.arguments,
                    tool_output=tool_result.output,
                    error=tool_result.error,
                )
                self.state.add_step(step)

                # Print status
                if tool_result.success:
                    if tc.name in ("write_file", "patch_file", "git_checkpoint"):
                        self.console.success(tool_result.output)
                    elif tc.name == "execute_command":
                        # Print condensed command status
                        if tool_result.data and "returncode" in tool_result.data:
                            ret = tool_result.data["returncode"]
                            dur = tool_result.data.get("duration", 0)
                            if ret == 0:
                                self.console.success(f"Command succeeded in {dur:.2f}s")
                            else:
                                self.console.error(f"Command failed (exit code {ret}) in {dur:.2f}s")
                    elif tc.name == "run_tests":
                        if tool_result.data and tool_result.data.get("passed"):
                            self.console.success("All tests passed successfully!")
                        else:
                            self.console.warning("Some tests failed. Intercepting failure for debugging...")
                else:
                    self.console.error(f"Tool {tc.name} failed: {tool_result.error}")

                # Append tool result to messages
                result_str = tool_result.to_string()
                messages.append(Message(
                    role="tool",
                    content=result_str,
                    name=tc.name,
                    tool_call_id=tc.id,
                ))

        if iteration >= max_iterations:
            self.console.warning(f"Reached maximum step limit ({max_iterations}). Task paused.")

        return final_answer
