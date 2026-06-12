"""OpenAI provider implementation.

Wraps the official OpenAI Python SDK. Supports any OpenAI-compatible
endpoint via OPENAI_API_BASE (LiteLLM, vLLM, Ollama, etc.).
"""

import logging
import time
import uuid

from openai import AsyncOpenAI

from app.config import Settings
from app.models.requests import ChatRequest
from app.models.responses import (
    ChatChoice,
    ChatMessageResponse,
    ChatResponse,
    UsageInfo,
)
from app.services.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """OpenAI API provider using the official async SDK."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY.get_secret_value(),
            base_url=settings.OPENAI_API_BASE,
            timeout=settings.OPENAI_TIMEOUT,
            max_retries=settings.OPENAI_MAX_RETRIES,
        )

    @property
    def provider_name(self) -> str:
        return "openai"

    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Send a chat completion request to the OpenAI API."""
        model = request.model or self._settings.OPENAI_MODEL

        logger.info(
            "Sending chat completion request",
            extra={
                "provider": self.provider_name,
                "model": model,
                "message_count": len(request.messages),
                "temperature": request.temperature,
            },
        )

        start_time = time.monotonic()

        response = await self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": m.role, "content": m.content} for m in request.messages
            ],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        latency_ms = (time.monotonic() - start_time) * 1000

        usage = UsageInfo(
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            total_tokens=response.usage.total_tokens if response.usage else 0,
        )

        logger.info(
            "Chat completion successful",
            extra={
                "provider": self.provider_name,
                "model": model,
                "latency_ms": round(latency_ms, 2),
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
            },
        )

        return ChatResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
            created=int(time.time()),
            model=response.model,
            choices=[
                ChatChoice(
                    index=i,
                    message=ChatMessageResponse(
                        role=choice.message.role,
                        content=choice.message.content or "",
                    ),
                    finish_reason=choice.finish_reason or "stop",
                )
                for i, choice in enumerate(response.choices)
            ],
            usage=usage,
        )

    async def health_check(self) -> bool:
        """Verify connectivity by listing available models."""
        try:
            await self._client.models.list()
            return True
        except Exception as e:
            logger.warning("OpenAI health check failed: %s", e)
            return False
