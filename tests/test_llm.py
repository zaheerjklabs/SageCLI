"""Unit tests for LLM providers, conversions, and factory."""

from sagecli.config import SageConfig
from sagecli.llm.base import Message, ToolCall
from sagecli.llm.gemini_provider import GeminiProvider
from sagecli.llm.openai_provider import OpenAIProvider
from sagecli.llm.anthropic_provider import AnthropicProvider
from sagecli.llm.factory import create_llm_provider


def test_provider_factory():
    """Verify factory instantiates appropriate provider."""
    gemini = create_llm_provider(SageConfig(provider="gemini", api_key="test"))
    assert isinstance(gemini, GeminiProvider)

    openai = create_llm_provider(SageConfig(provider="openai", api_key="test"))
    assert isinstance(openai, OpenAIProvider)

    anthropic = create_llm_provider(SageConfig(provider="anthropic", api_key="test"))
    assert isinstance(anthropic, AnthropicProvider)


def test_gemini_message_conversion():
    """Verify conversion of Message list to Gemini API format."""
    provider = GeminiProvider(api_key="test")
    messages = [
        Message(role="system", content="You are Sage."),
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi", tool_calls=[ToolCall(id="1", name="read_file", arguments={"path": "a.txt"})]),
        Message(role="tool", content="file content", name="read_file", tool_call_id="1"),
    ]
    sys_inst, contents = provider._convert_messages(messages)
    assert sys_inst["parts"][0]["text"] == "You are Sage."
    assert len(contents) == 3
    assert contents[0]["role"] == "user"
    assert contents[1]["role"] == "model"
    assert contents[2]["role"] == "user"


def test_anthropic_message_conversion():
    """Verify conversion of Message list to Anthropic API format."""
    provider = AnthropicProvider(api_key="test")
    messages = [
        Message(role="system", content="System instruction"),
        Message(role="user", content="Build model"),
        Message(role="assistant", content="Planning", tool_calls=[ToolCall(id="tc1", name="write_file", arguments={"path": "x.py"})]),
        Message(role="tool", content="OK", tool_call_id="tc1"),
    ]
    sys_prompt, formatted = provider._convert_messages(messages)
    assert sys_prompt == "System instruction"
    assert len(formatted) == 3
    assert formatted[0]["role"] == "user"
    assert formatted[1]["role"] == "assistant"
    assert formatted[2]["role"] == "user"
