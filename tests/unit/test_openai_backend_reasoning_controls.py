from __future__ import annotations

from skill_research.llms.base import ChatMessage, CompletionRequest
from skill_research.llms.openai_backend import OpenAIBackendConfig, OpenAIChatBackend


class FakeChoiceMessage:
    content = "ok"


class FakeChoice:
    message = FakeChoiceMessage()


class FakeCompletions:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return type("Response", (), {"choices": [FakeChoice()], "model": kwargs["model"]})()


class FakeChat:
    def __init__(self):
        self.completions = FakeCompletions()


class FakeClient:
    def __init__(self):
        self.chat = FakeChat()


def test_openai_backend_passes_reasoning_effort_when_configured() -> None:
    client = FakeClient()
    backend = OpenAIChatBackend(
        OpenAIBackendConfig(model="gpt-5.5", api_key="x", reasoning_effort="none"),
        client=client,
    )

    backend.complete(CompletionRequest([ChatMessage("user", "x")], max_tokens=10))

    assert client.chat.completions.kwargs["reasoning_effort"] == "none"
    assert "verbosity" not in client.chat.completions.kwargs
