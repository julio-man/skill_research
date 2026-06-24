from __future__ import annotations

from skill_research.llms.openai_backend import OpenAIBackendConfig, OpenAIChatBackend


class FakeClientFactory:
    def __init__(self):
        self.kwargs = None

    def __call__(self, **kwargs):
        self.kwargs = kwargs
        return object()


def test_openai_backend_uses_azure_endpoint_env_when_base_url_omitted(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://azure.example/openai/v1")
    factory = FakeClientFactory()

    OpenAIChatBackend(OpenAIBackendConfig(model="gpt-5.5"), client_factory=factory)

    assert factory.kwargs["base_url"] == "https://azure.example/openai/v1"
