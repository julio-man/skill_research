from __future__ import annotations

import pytest

from skill_research.llms import build_llm_backend, llm_backend_registry
from skill_research.llms.base import ChatMessage, CompletionRequest
from skill_research.llms.openai_backend import OpenAIChatBackend, OpenAIBackendConfig


class FakeChoiceMessage:
    content = "hello"


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


def test_openai_backend_maps_completion_request_to_chat_completion() -> None:
    client = FakeClient()
    backend = OpenAIChatBackend(OpenAIBackendConfig(name="task_llm", model="gpt-test", api_key="x"), client=client)

    response = backend.complete(CompletionRequest([ChatMessage("system", "s"), ChatMessage("user", "u")], temperature=0.0, max_tokens=10, seed=3))

    assert response.content == "hello"
    assert response.info.name == "task_llm"
    assert client.chat.completions.kwargs == {
        "model": "gpt-test",
        "messages": [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}],
        "temperature": 0.0,
        "max_tokens": 10,
        "seed": 3,
    }


def test_openai_backend_requires_api_key_without_client(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="api key"):
        OpenAIChatBackend(OpenAIBackendConfig(model="gpt-test"))


def test_llm_registry_builds_openai_backend_with_injected_client() -> None:
    assert "openai" in llm_backend_registry.names()
    backend = build_llm_backend("openai", model="gpt-test", api_key="x", client=FakeClient())
    assert isinstance(backend, OpenAIChatBackend)
