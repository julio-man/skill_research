from __future__ import annotations

import os

import pytest

from skill_research.llm.client import ChatMessage, LLMConfig, build_llm_client, resolve_llm_config


class _FakeOpenAIClient:
    def __init__(self, *, api_key: str, base_url: str | None = None):
        self.api_key = api_key
        self.base_url = base_url


class _FakeAnthropicClient:
    def __init__(self, *, api_key: str):
        self.api_key = api_key


class _FakeGeminiClient:
    def __init__(self, *, api_key: str):
        self.api_key = api_key


def test_resolve_llm_config_for_openai_compatible_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:8000/v1")

    config = resolve_llm_config(provider="openai", model="gpt-5.4")

    assert config.provider == "openai"
    assert config.model == "gpt-5.4"
    assert config.api_key == "openai-key"
    assert config.base_url == "http://localhost:8000/v1"


def test_resolve_llm_config_for_anthropic_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-key")

    config = resolve_llm_config(provider="anthropic", model="claude-sonnet-4-5")

    assert config.provider == "anthropic"
    assert config.api_key == "anthropic-key"
    assert config.base_url is None


def test_resolve_llm_config_for_gemini_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")

    config = resolve_llm_config(provider="gemini", model="gemini-2.5-pro")

    assert config.provider == "gemini"
    assert config.api_key == "gemini-key"


def test_resolve_llm_config_rejects_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        resolve_llm_config(provider="openai", model="gpt-5.4")


def test_build_llm_client_for_openai_compatible(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("skill_research.llm.client._make_openai_sdk_client", lambda config: _FakeOpenAIClient(api_key=config.api_key, base_url=config.base_url))

    client = build_llm_client(
        LLMConfig(provider="openai", model="gpt-5.4", api_key="k", base_url="http://localhost:8000/v1")
    )

    assert client.provider == "openai"
    assert isinstance(client.sdk_client, _FakeOpenAIClient)
    assert client.sdk_client.base_url == "http://localhost:8000/v1"


def test_build_llm_client_for_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("skill_research.llm.client._make_anthropic_sdk_client", lambda config: _FakeAnthropicClient(api_key=config.api_key))

    client = build_llm_client(
        LLMConfig(provider="anthropic", model="claude-sonnet-4-5", api_key="k")
    )

    assert client.provider == "anthropic"
    assert isinstance(client.sdk_client, _FakeAnthropicClient)


def test_build_llm_client_for_gemini(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("skill_research.llm.client._make_gemini_sdk_client", lambda config: _FakeGeminiClient(api_key=config.api_key))

    client = build_llm_client(
        LLMConfig(provider="gemini", model="gemini-2.5-pro", api_key="k")
    )

    assert client.provider == "gemini"
    assert isinstance(client.sdk_client, _FakeGeminiClient)


def test_chat_message_to_openai_payload() -> None:
    message = ChatMessage(role="user", content="hello")

    assert message.as_openai_dict() == {"role": "user", "content": "hello"}


def test_provider_aliases_normalize() -> None:
    assert resolve_llm_config(provider="openai-compatible", model="x", api_key="k").provider == "openai"
    assert resolve_llm_config(provider="azure-openai", model="x", api_key="k").provider == "openai"
    assert resolve_llm_config(provider="google", model="x", api_key="k").provider == "gemini"
