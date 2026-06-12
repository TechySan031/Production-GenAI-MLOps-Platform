"""
High-level LLM service.

Phase 2 additions over Phase 1:
    - LangfuseClient integrated (Null Object — zero guards in business logic)
    - Per-request cost calculation via CostBreakdown
    - Structured InferenceMetrics emitted to logs (Azure Monitor foundation)
    - request_id parameter for trace/log correlation
    - shutdown() method for graceful Langfuse flush on app exit
"""

import logging
import time
import uuid
from datetime import datetime, timezone

from app.config import Settings
from app.models.requests import ChatRequest
from app.models.responses import ChatResponse
from app.observability.cost_calculator import calculate_cost
from app.observability.langfuse_client import LangfuseClient
from app.observability.metrics import InferenceMetrics, record_inference_metrics
from app.services.providers import create_provider
from app.services.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class LLMService:
    """Orchestrates LLM inference with integrated observability."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._provider: BaseProvider = create_provider(settings)
        self._observability = LangfuseClient(settings)
        logger.info(
            "LLM Service initialized",
            extra={
                "provider": self._provider.provider_name,
                "observability_enabled": self._observability.is_enabled,
            },
        )

    @property
    def provider_name(self) -> str:
        return self._provider.provider_name

    async def chat(
        self,
        request: ChatRequest,
        request_id: str | None = None,
    ) -> ChatResponse:
        """
        Execute a chat completion with full observability.

        Args:
            request:    The validated chat request.
            request_id: X-Request-ID from the middleware. Used as Langfuse
                        trace_id so every HTTP request maps 1:1 to a Langfuse trace.
                        Generated here if not provided (e.g. internal callers).
        """
        trace_id = request_id or str(uuid.uuid4())

        # create_trace() always returns a callable context — never None.
        # NullObservabilityContext is returned when Langfuse is disabled.
        obs_context = self._observability.create_trace(
            trace_id=trace_id,
            name="chat-completion",
            metadata={
                "provider": self._provider.provider_name,
                "requested_model": request.model,
                "message_count": len(request.messages),
                "temperature": request.temperature,
            },
            tags=[self._settings.ENVIRONMENT.value, self._provider.provider_name],
        )

        # Capture wall-clock timestamps for Langfuse; monotonic for latency calculation
        start_dt = datetime.now(timezone.utc)
        start_monotonic = time.monotonic()

        try:
            response = await self._provider.chat_completion(request)

            end_dt = datetime.now(timezone.utc)
            latency_ms = (time.monotonic() - start_monotonic) * 1000

            cost = calculate_cost(
                model=response.model,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
            )

            obs_context.record_generation(
                model=response.model,
                model_parameters={
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                },
                input_messages=[
                    {"role": m.role, "content": m.content} for m in request.messages
                ],
                output=response.choices[0].message.content if response.choices else "",
                # Langfuse expects "input"/"output" for token fields, not "prompt"/"completion"
                usage={
                    "input": response.usage.prompt_tokens,
                    "output": response.usage.completion_tokens,
                    "total": response.usage.total_tokens,
                    "unit": "TOKENS",
                    "input_cost": cost.prompt_cost_usd,
                    "output_cost": cost.completion_cost_usd,
                    "total_cost": cost.total_cost_usd,
                },
                start_time=start_dt,
                end_time=end_dt,
                metadata={
                    "request_id": trace_id,
                    "provider": self._provider.provider_name,
                    "latency_ms": round(latency_ms, 2),
                },
            )

            # Structured log entry for Azure Monitor Log Analytics
            record_inference_metrics(
                InferenceMetrics(
                    request_id=trace_id,
                    environment=self._settings.ENVIRONMENT.value,
                    provider=self._provider.provider_name,
                    model=response.model,
                    latency_ms=round(latency_ms, 2),
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                    cost_usd=cost.total_cost_usd,
                    success=True,
                )
            )

            logger.info(
                "Chat request completed",
                extra={
                    "request_id": trace_id,
                    "model": response.model,
                    "total_tokens": response.usage.total_tokens,
                    "latency_ms": round(latency_ms, 2),
                    "cost_usd": cost.total_cost_usd,
                },
            )

            return response

        except Exception as exc:
            latency_ms = (time.monotonic() - start_monotonic) * 1000

            obs_context.record_error(
                error=exc,
                metadata={
                    "request_id": trace_id,
                    "latency_ms": round(latency_ms, 2),
                    "provider": self._provider.provider_name,
                },
            )

            record_inference_metrics(
                InferenceMetrics(
                    request_id=trace_id,
                    environment=self._settings.ENVIRONMENT.value,
                    provider=self._provider.provider_name,
                    model=request.model or "unknown",
                    latency_ms=round(latency_ms, 2),
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    cost_usd=0.0,
                    success=False,
                    error_type=type(exc).__name__,
                )
            )

            raise  # Re-raise for the route handler to map to HTTP errors

    async def is_healthy(self) -> bool:
        return await self._provider.health_check()

    def shutdown(self) -> None:
        """Flush Langfuse and release resources. Call in app lifespan teardown."""
        self._observability.shutdown()