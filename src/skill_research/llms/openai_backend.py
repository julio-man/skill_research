"""OpenAI-compatible chat backend for hosted LLM providers."""

from __future__ import annotations

from dataclasses import dataclass
import os
import time

from openai import OpenAI

from skill_research.llms.base import CompletionRequest, CompletionResponse, LLMBackendBase, LLMBackendInfo


@dataclass(frozen=True)
class OpenAIBackendConfig:
    model: str
    name: str = "openai"
    api_key: str | None = None
    base_url: str | None = None
    provider: str = "openai"
    max_tokens_parameter: str | None = "max_tokens"
    include_temperature: bool = True
    reasoning_effort: str | None = None


class OpenAIChatBackend(LLMBackendBase):
    def __init__(self, config: OpenAIBackendConfig, client=None, client_factory=OpenAI):
        api_key = config.api_key or os.environ.get("OPENAI_API_KEY")
        base_url = config.base_url or os.environ.get("OPENAI_BASE_URL") or os.environ.get("AZURE_OPENAI_ENDPOINT")
        if client is None and not api_key:
            raise ValueError("OpenAI backend requires an api key")
        super().__init__(LLMBackendInfo(name=config.name, provider=config.provider, model=config.model))
        self.config = config
        self.client = client or client_factory(api_key=api_key, base_url=base_url)

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        kwargs = {
            "model": self.config.model,
            "messages": [{"role": message.role, "content": message.content} for message in request.messages],
        }
        if self.config.max_tokens_parameter is not None:
            kwargs[self.config.max_tokens_parameter] = request.max_tokens
        if self.config.include_temperature:
            kwargs["temperature"] = request.temperature
        if self.config.reasoning_effort is not None:
            kwargs["reasoning_effort"] = self.config.reasoning_effort
        if request.seed is not None:
            kwargs["seed"] = request.seed
        start = time.perf_counter()
        response = self.client.chat.completions.create(**kwargs)
        elapsed = time.perf_counter() - start
        usage = response.usage.model_dump() if getattr(response, "usage", None) is not None else None
        metadata = {"model": getattr(response, "model", self.config.model), "elapsed_seconds": elapsed}
        if usage is not None:
            metadata["usage"] = usage
        return CompletionResponse(content=response.choices[0].message.content or "", info=self.info, metadata=metadata)
