from skill_research.core.registry import ComponentRegistry
from skill_research.llms.base import ChatMessage, CompletionRequest, CompletionResponse, LLMBackend, LLMBackendBase, LLMBackendInfo
from skill_research.llms.openai_backend import OpenAIBackendConfig, OpenAIChatBackend
from skill_research.llms.replay import ReplayLLMBackend


llm_backend_registry = ComponentRegistry()
llm_backend_registry.register("replay", lambda responses, **kwargs: ReplayLLMBackend(responses, **kwargs))
llm_backend_registry.register("openai", lambda model, api_key=None, base_url=None, name="openai", client=None, max_tokens_parameter="max_tokens", include_temperature=True, reasoning_effort=None, **kwargs: OpenAIChatBackend(OpenAIBackendConfig(model=model, api_key=api_key, base_url=base_url, name=name, max_tokens_parameter=max_tokens_parameter, include_temperature=include_temperature, reasoning_effort=reasoning_effort), client=client))


def build_llm_backend(name: str, **kwargs):
    return llm_backend_registry.build(name, **kwargs)


__all__ = [
    "ChatMessage",
    "CompletionRequest",
    "CompletionResponse",
    "LLMBackend",
    "LLMBackendBase",
    "LLMBackendInfo",
    "OpenAIBackendConfig",
    "OpenAIChatBackend",
    "ReplayLLMBackend",
    "build_llm_backend",
    "llm_backend_registry",
]
