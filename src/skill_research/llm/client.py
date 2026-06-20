from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final


OPENAI_ALIASES: Final[set[str]] = {"openai", "openai-compatible", "azure-openai", "openrouter", "vllm"}
GEMINI_ALIASES: Final[set[str]] = {"gemini", "google"}
ANTHROPIC_ALIASES: Final[set[str]] = {"anthropic", "claude"}


@dataclass
class ChatMessage:
    role: str
    content: str

    def as_openai_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class LLMConfig:
    provider: str
    model: str
    api_key: str
    base_url: str | None = None


@dataclass
class LLMClient:
    provider: str
    model: str
    sdk_client: object

    def complete(self, messages: list[ChatMessage], temperature: float, max_tokens: int) -> str:
        if self.provider == "openai":
            response = self.sdk_client.chat.completions.create(
                model=self.model,
                temperature=temperature,
                max_completion_tokens=max_tokens,
                messages=[message.as_openai_dict() for message in messages],
            )
            return response.choices[0].message.content or ""

        if self.provider == "anthropic":
            system_text = "\n\n".join(message.content for message in messages if message.role == "system")
            non_system_messages = [
                {"role": message.role, "content": message.content}
                for message in messages
                if message.role != "system"
            ]
            response = self.sdk_client.messages.create(
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                system=system_text,
                messages=non_system_messages,
            )
            return "".join(block.text for block in response.content)

        if self.provider == "gemini":
            prompt = "\n\n".join(f"{message.role.upper()}: {message.content}" for message in messages)
            response = self.sdk_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                },
            )
            return response.text or ""

        raise ValueError(f"Unsupported LLM provider: {self.provider}")



def _load_project_env() -> None:
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _normalize_provider(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized in OPENAI_ALIASES:
        return "openai"
    if normalized in ANTHROPIC_ALIASES:
        return "anthropic"
    if normalized in GEMINI_ALIASES:
        return "gemini"
    raise ValueError(f"Unsupported LLM provider: {provider}")



def _resolve_api_key(provider: str, api_key: str | None) -> str:
    if api_key:
        return api_key

    env_var = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }[provider]
    value = os.getenv(env_var)
    if not value:
        raise RuntimeError(f"{env_var} not found")
    return value



def resolve_llm_config(provider: str, model: str, api_key: str | None = None, base_url: str | None = None) -> LLMConfig:
    _load_project_env()
    normalized_provider = _normalize_provider(provider)
    resolved_api_key = _resolve_api_key(normalized_provider, api_key)

    resolved_base_url = base_url
    if normalized_provider == "openai" and resolved_base_url is None:
        resolved_base_url = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("OPENAI_BASE_URL")

    return LLMConfig(
        provider=normalized_provider,
        model=model,
        api_key=resolved_api_key,
        base_url=resolved_base_url,
    )



def _make_openai_sdk_client(config: LLMConfig) -> object:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai package is required for OpenAI-compatible providers") from exc

    kwargs: dict[str, str] = {"api_key": config.api_key}
    if config.base_url:
        kwargs["base_url"] = config.base_url
    return OpenAI(**kwargs)



def _make_anthropic_sdk_client(config: LLMConfig) -> object:
    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise RuntimeError("anthropic package is required for Anthropic providers") from exc

    return Anthropic(api_key=config.api_key)



def _make_gemini_sdk_client(config: LLMConfig) -> object:
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError("google-genai package is required for Gemini providers") from exc

    return genai.Client(api_key=config.api_key)



def build_llm_client(config: LLMConfig) -> LLMClient:
    if config.provider == "openai":
        sdk_client = _make_openai_sdk_client(config)
    elif config.provider == "anthropic":
        sdk_client = _make_anthropic_sdk_client(config)
    elif config.provider == "gemini":
        sdk_client = _make_gemini_sdk_client(config)
    else:
        raise ValueError(f"Unsupported LLM provider: {config.provider}")

    return LLMClient(provider=config.provider, model=config.model, sdk_client=sdk_client)
