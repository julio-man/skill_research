from __future__ import annotations

from skill_research.llms import build_llm_backend, llm_backend_registry
from skill_research.llms.base import ChatMessage, CompletionRequest, CompletionResponse, LLMBackend, LLMBackendBase, LLMBackendInfo
from skill_research.llms.replay import ReplayLLMBackend


class EchoBackend(LLMBackendBase):
    def __init__(self) -> None:
        super().__init__(LLMBackendInfo(name="echo", provider="unit", model="echo-model"))

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(content=request.messages[-1].content, info=self.info, metadata={"temperature": request.temperature})


def test_llm_backend_base_uses_generic_completion_contract() -> None:
    backend = EchoBackend()
    request = CompletionRequest(messages=[ChatMessage("user", "hello")], temperature=0.0, max_tokens=5, seed=7)

    response = backend.complete(request)

    assert response.content == "hello"
    assert response.info.name == "echo"
    assert response.metadata["temperature"] == 0.0


def test_replay_llm_backend_returns_seeded_responses() -> None:
    backend = ReplayLLMBackend(["first", "second"], name="replay-a")

    assert backend.complete(CompletionRequest([ChatMessage("user", "x")])).content == "first"
    assert backend.complete(CompletionRequest([ChatMessage("user", "x")])).content == "second"
    assert backend.info.provider == "replay"


def test_llm_registry_builds_replay_backend() -> None:
    assert "replay" in llm_backend_registry.names()
    backend = build_llm_backend("replay", responses=["ok"])
    assert isinstance(backend, LLMBackend)
    assert backend.complete(CompletionRequest([ChatMessage("user", "x")])).content == "ok"
