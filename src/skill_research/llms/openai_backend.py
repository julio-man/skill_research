"""OpenAI-compatible chat backend for hosted LLM providers."""

from __future__ import annotations

from dataclasses import dataclass
import os

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
    verbosity: str | None = None


class OpenAIChatBackend(LLMBackendBase):
    def __init__(self, config: OpenAIBackendConfig, client=None):
        api_key = config.api_key or os.environ.get("OPENAI_API_KEY")
        if client is None and not api_key:
            raise ValueError("OpenAI backend requires an api key")
        super().__init__(LLMBackendInfo(name=config.name, provider=config.provider, model=config.model))
        self.config = config
        self.client = client or OpenAI(api_key=api_key, base_url=config.base_url)

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
        response = self.client.chat.completions.create(**kwargs)
        return CompletionResponse(content=response.choices[0].message.content or "", info=self.info, metadata={"model": getattr(response, "model", self.config.model)})
