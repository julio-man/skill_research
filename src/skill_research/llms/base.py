from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True)
class CompletionRequest:
    messages: list[ChatMessage]
    temperature: float = 0.0
    max_tokens: int = 2500
    seed: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMBackendInfo:
    name: str
    provider: str
    model: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CompletionResponse:
    content: str
    info: LLMBackendInfo
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class LLMBackend(Protocol):
    info: LLMBackendInfo

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        ...


class LLMBackendBase:
    def __init__(self, info: LLMBackendInfo):
        self.info = info
