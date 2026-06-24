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


def test_openai_backend_can_omit_temperature_for_default_only_models() -> None:
    client = FakeClient()
    backend = OpenAIChatBackend(OpenAIBackendConfig(model="gpt-5.5", api_key="x", include_temperature=False), client=client)

    backend.complete(CompletionRequest([ChatMessage("user", "x")], temperature=0.0, max_tokens=10))

    assert "temperature" not in client.chat.completions.kwargs
