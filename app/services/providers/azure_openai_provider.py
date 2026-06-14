"""
Azure OpenAI provider implementation.

How Azure OpenAI differs from the standard OpenAI provider:

1. Client class: AsyncAzureOpenAI (not AsyncOpenAI)
   Authentication is via api_key + azure_endpoint, not just api_key.
   Future: swap api_key for DefaultAzureCredential (Managed Identity).

2. Model identifier: Azure uses "deployment name" as the model parameter.
   You create a deployment in Azure Portal, give it a name (e.g. "my-gpt4o"),
   and use that name — not "gpt-4o" — when calling the API.

3. response.model: Azure returns the deployment name here, NOT the base model
   name. Cost calculator handles this via _normalize_model_name().

4. Health check: Azure OpenAI doesn't reliably support models.list() in all
   configurations. We use a minimal 1-token completion instead.
"""

import logging
import time
import uuid
from typing import cast

from openai import AsyncAzureOpenAI
from openai.types.chat import ChatCompletionMessageParam

from app.config import Settings
from app.models.requests import ChatRequest
from app.models.responses import ChatChoice, ChatMessageResponse, ChatResponse, UsageInfo
from app.services.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class AzureOpenAIProvider(BaseProvider):
    """Azure OpenAI provider via the openai SDK's Azure-specific client."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY.get_secret_value(),
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )
        logger.info(
            "Azure OpenAI provider initialized",
            extra={
                "endpoint": settings.AZURE_OPENAI_ENDPOINT,
                "api_version": settings.AZURE_OPENAI_API_VERSION,
                "default_deployment": settings.AZURE_OPENAI_DEPLOYMENT,
            },
        )

    @property
    def provider_name(self) -> str:
        return "azure_openai"

    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """
        Send a chat completion to Azure OpenAI.

        request.model is treated as the Azure deployment name when provided.
        Falls back to AZURE_OPENAI_DEPLOYMENT from settings.
        """
        deployment = request.model or self._settings.AZURE_OPENAI_DEPLOYMENT

        logger.info(
            "Azure OpenAI chat completion request",
            extra={
                "provider": self.provider_name,
                "deployment": deployment,
                "message_count": len(request.messages),
                "temperature": request.temperature,
            },
        )

        start_time = time.monotonic()

        response = await self._client.chat.completions.create(
            model=deployment,  # Azure SDK uses "model" param as deployment name
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
            "Azure OpenAI chat completion successful",
            extra={
                "provider": self.provider_name,
                "deployment": deployment,
                "returned_model": response.model,  # deployment name, not base model
                "latency_ms": round(latency_ms, 2),
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
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
        Verify Azure OpenAI connectivity via a minimal 1-token completion.

        Azure doesn't support models.list() reliably across all configurations,
        so we use a cheap real call instead.
        """
        try:
            await self._client.chat.completions.create(
                model=self._settings.AZURE_OPENAI_DEPLOYMENT,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
            )
            return True
        except Exception as exc:
            logger.warning("Azure OpenAI health check failed: %s", exc)
            return False
