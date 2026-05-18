"""Minimal Anthropic provider adapter — async, typed, retry-aware."""
from __future__ import annotations
 
from dataclasses import dataclass
from typing import Any
 
from anthropic import AsyncAnthropic
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
 
from shopllm.config import get_settings
 
 
@dataclass(slots=True, frozen=True)
class ChatResult:
    """Provider-agnostic result returned by adapters."""
 
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    raw: dict[str, Any]
 
 
class AnthropicAdapter:
    """Thin wrapper around the official Anthropic SDK."""
 
    def __init__(self, api_key: str | None = None, default_model: str | None = None) -> None:
        settings = get_settings()
        self._client = AsyncAnthropic(api_key=api_key or settings.anthropic_api_key)
        self._default_model = default_model or settings.default_anthropic_model
 
    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def chat(
        self,
        prompt: str,
        *,
        model: str | None = None,
        max_tokens: int = 512,
        system: str | None = None,
    ) -> ChatResult:
        response = await self._client.messages.create(
            model=model or self._default_model,
            max_tokens=max_tokens,
            system=system or "You are a helpful assistant for an e-commerce platform.",
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )
        return ChatResult(
            text=text,
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            raw=response.model_dump(),
        )