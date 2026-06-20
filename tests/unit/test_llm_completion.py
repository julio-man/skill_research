from __future__ import annotations

from skill_research.llm.client import ChatMessage, LLMClient


class _FakeOpenAICompletions:
    def create(self, **kwargs):
        self.kwargs = kwargs
        return type(
            "Response",
            (),
            {"choices": [type("Choice", (), {"message": type("Message", (), {"content": "openai-output"})()})()]},
        )()


class _FakeOpenAIChat:
    def __init__(self):
        self.completions = _FakeOpenAICompletions()


class _FakeOpenAISDK:
    def __init__(self):
        self.chat = _FakeOpenAIChat()


class _FakeAnthropicMessages:
    def create(self, **kwargs):
        self.kwargs = kwargs
        return type("Response", (), {"content": [type("Block", (), {"text": "anthropic-output"})()]})()


class _FakeAnthropicSDK:
    def __init__(self):
        self.messages = _FakeAnthropicMessages()


class _FakeGeminiModels:
    def generate_content(self, **kwargs):
        self.kwargs = kwargs
        return type("Response", (), {"text": "gemini-output"})()


class _FakeGeminiSDK:
    def __init__(self):
        self.models = _FakeGeminiModels()


MESSAGES = [
    ChatMessage(role="system", content="system prompt"),
    ChatMessage(role="user", content="user prompt"),
]


def test_openai_client_complete_uses_chat_completions_shape() -> None:
    client = LLMClient(provider="openai", model="gpt-5.4", sdk_client=_FakeOpenAISDK())

    output = client.complete(MESSAGES, temperature=0.0, max_tokens=123)

    assert output == "openai-output"
    kwargs = client.sdk_client.chat.completions.kwargs
    assert kwargs["model"] == "gpt-5.4"
    assert kwargs["temperature"] == 0.0
    assert kwargs["max_completion_tokens"] == 123
    assert kwargs["messages"] == [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "user prompt"},
    ]


def test_anthropic_client_complete_uses_messages_api_shape() -> None:
    client = LLMClient(provider="anthropic", model="claude-sonnet-4-5", sdk_client=_FakeAnthropicSDK())

    output = client.complete(MESSAGES, temperature=0.2, max_tokens=321)

    assert output == "anthropic-output"
    kwargs = client.sdk_client.messages.kwargs
    assert kwargs["model"] == "claude-sonnet-4-5"
    assert kwargs["temperature"] == 0.2
    assert kwargs["max_tokens"] == 321
    assert kwargs["system"] == "system prompt"
    assert kwargs["messages"] == [{"role": "user", "content": "user prompt"}]


def test_gemini_client_complete_flattens_messages_to_prompt() -> None:
    client = LLMClient(provider="gemini", model="gemini-2.5-pro", sdk_client=_FakeGeminiSDK())

    output = client.complete(MESSAGES, temperature=0.3, max_tokens=222)

    assert output == "gemini-output"
    kwargs = client.sdk_client.models.kwargs
    assert kwargs["model"] == "gemini-2.5-pro"
    assert kwargs["config"]["temperature"] == 0.3
    assert kwargs["config"]["max_output_tokens"] == 222
    assert "system prompt" in kwargs["contents"]
    assert "user prompt" in kwargs["contents"]
