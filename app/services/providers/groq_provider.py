"""
Groq LPU inference provider.

Groq's API is OpenAI-compatible — the same openai SDK works here.
We use a separate class (rather than reusing OpenAIProvider with a different
base_url) so that every log line, Langfuse trace, and observability metric
correctly identifies the provider as "groq", not "openai".

Groq free tier (as of 2025): 14,400 requests/day on most models.
Best model for development: llama-3.1-8b-instant (fast, capable, free).
Best model for evaluation gate judging: llama-3.3-70b-versatile.

API reference: https://console.groq.com/docs/openai
"""

import logging
import time
import uuid
from typing import cast

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

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

_GROQ_API_BASE = "https://api.groq.com/openai/v1"


class GroqProvider(BaseProvider):
    """
    Groq inference provider via the openai SDK's OpenAI-compatible client.

    Uses the same AsyncOpenAI client as OpenAIProvider — just a different
    base_url and API key. Response parsing is identical because Groq's
    response schema matches OpenAI's exactly.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY.get_secret_value(),
            base_url=_GROQ_API_BASE,
            timeout=settings.OPENAI_TIMEOUT,
            max_retries=settings.OPENAI_MAX_RETRIES,
        )
        logger.info(
            "Groq provider initialized",
            extra={
                "default_model": settings.GROQ_MODEL,
                "base_url": _GROQ_API_BASE,
            },
        )

    @property
    def provider_name(self) -> str:
        return "groq"

    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Send a chat completion request to Groq."""
        model = request.model or self._settings.GROQ_MODEL

        logger.info(
            "Groq chat completion request",
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
            messages=cast(
                list[ChatCompletionMessageParam],
                [{"role": m.role, "content": m.content} for m in request.messages],
            ),
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
            "Groq chat completion successful",
            extra={
                "provider": self.provider_name,
                "model": response.model,
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
        """
        Verify Groq connectivity by listing available models.

        Groq supports the OpenAI models.list() endpoint.
        This makes no completion call and costs no tokens.
        """
        try:
            await self._client.models.list()
            return True
        except Exception as exc:
            logger.warning("Groq health check failed: %s", exc)
            return False
