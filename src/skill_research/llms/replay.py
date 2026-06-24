"""Deterministic replay LLM backend for tests and reproducible smoke runs."""

from __future__ import annotations

from collections.abc import Sequence

from skill_research.llms.base import CompletionRequest, CompletionResponse, LLMBackendBase, LLMBackendInfo


class ReplayLLMBackend(LLMBackendBase):
    def __init__(self, responses: Sequence[str], name: str = "replay", model: str = "replay"):
        super().__init__(LLMBackendInfo(name=name, provider="replay", model=model))
        self._responses = list(responses)
        self._index = 0

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        if self._index >= len(self._responses):
            raise IndexError("ReplayLLMBackend has no remaining responses")
        content = self._responses[self._index]
        self._index += 1
        return CompletionResponse(content=content, info=self.info)
