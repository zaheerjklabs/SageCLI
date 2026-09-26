"""Interactive prompt formatting, completion, and session management for SageCLI."""

from typing import Dict
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import NestedCompleter, Completer, Completion
from prompt_toolkit.styles import Style as PtStyle

from sagecli.ui.symbols import get_symbols
from sagecli.ui.theme import Palette


SLASH_COMMANDS: Dict[str, str] = {
    "/help": "Display command list and assistance",
    "/setup": "Launch interactive setup wizard",
    "/config": "View and manage SageCLI settings",
    "/mode": "Switch execution mode (safe, auto, plan)",
    "/model": "Switch or inspect active LLM model",
    "/provider": "Switch LLM provider (gemini, openai, anthropic, groq, ollama)",
    "/cost": "Show token consumption and estimated session cost",
    "/usage": "Show session token usage statistics",
    "/doctor": "Run system diagnostics & environment health check",
    "/context": "Display workspace repository and dataset context",
    "/memory": "View task history and recorded metrics",
    "/dataset": "Inspect dataset shape, schema, and statistics",
    "/checkpoint": "Create a Git checkpoint before risky changes",
    "/diff": "Inspect uncommitted code modifications",
    "/rollback": "Revert uncommitted changes to previous checkpoint",
    "/compact": "Toggle compact logo display mode",
    "/ascii": "Toggle ASCII fallback symbol mode",
    "/demo": "Demonstrate the SageCLI visual language",
    "/clear": "Clear terminal and reprint startup banner",
    "/exit": "Exit SageCLI",
    "/quit": "Exit SageCLI",
}


class SlashCommandCompleter(Completer):
    """Completer for slash commands with rich descriptions."""

    def __init__(self):
        self.commands = SLASH_COMMANDS
        self.sub_completer = NestedCompleter.from_nested_dict({
            "/mode": {"safe": None, "auto": None, "plan": None},
            "/provider": {"gemini": None, "openai": None, "anthropic": None, "groq": None, "openrouter": None, "ollama": None},
            "/config": {
                "show": None,
                "set": {
                    "mode": {"safe": None, "auto": None, "plan": None},
                    "timeout": None,
                    "max_iterations": None,
                    "ascii_only": {"true": None, "false": None},
                },
            },
        })

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # If typing arguments for subcommands
        if " " in text:
            yield from self.sub_completer.get_completions(document, complete_event)
            return

        # Slash command completion
        word = document.get_word_before_cursor(WORD=True)
        if word.startswith("/") or text.startswith("/"):
            for cmd, desc in self.commands.items():
                if cmd.startswith(word):
                    display_meta = desc
                    yield Completion(
                        cmd,
                        start_position=-len(word),
                        display=cmd,
                        display_meta=display_meta,
                    )


def get_prompt_text(force_ascii: bool = False) -> str:
    """Return plain formatted prompt text."""
    symbols = get_symbols(force_ascii=force_ascii)
    return f"sage {symbols.PROMPT} "


def get_prompt_tokens(force_ascii: bool = False) -> FormattedText:
    """Return formatted tokens for prompt_toolkit."""
    symbols = get_symbols(force_ascii=force_ascii)
    return FormattedText([
        ("class:prompt.name", "sage"),
        ("class:prompt.space", " "),
        ("class:prompt.symbol", f"{symbols.PROMPT} "),
    ])


def get_prompt_toolkit_style() -> PtStyle:
    """Return custom prompt_toolkit style for SageCLI."""
    return PtStyle.from_dict({
        "prompt.name": f"{Palette.SAGE_PRIMARY} bold",
        "prompt.space": "",
        "prompt.symbol": f"{Palette.MINT_ACCENT} bold",
        # Auto-completion menu styling
        "completion-menu": f"bg:{Palette.BG_CARD} #{Palette.TEXT_LIGHT[1:]}",
        "completion-menu.completion": f"bg:{Palette.BG_CARD} #{Palette.TEXT_LIGHT[1:]}",
        "completion-menu.completion.current": f"bg:{Palette.SAGE_PRIMARY} #0F1412 bold",
        "completion-menu.meta.completion": f"bg:{Palette.BG_CARD} #{Palette.MINT_ACCENT[1:]}",
        "completion-menu.meta.completion.current": f"bg:{Palette.SAGE_PRIMARY} #0F1412",
        "auto-suggestion": f"#{Palette.TEXT_DIM[1:]}",
    })


def create_prompt_session(force_ascii: bool = False) -> PromptSession:
    """Create a configured interactive prompt session with auto-completion."""
    return PromptSession(
        message=lambda: get_prompt_tokens(force_ascii=force_ascii),
        style=get_prompt_toolkit_style(),
        history=InMemoryHistory(),
        auto_suggest=AutoSuggestFromHistory(),
        completer=SlashCommandCompleter(),
    )
