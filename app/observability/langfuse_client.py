"""
Langfuse observability client — Null Object Pattern implementation.

Design decision — why Null Object instead of if-guards:
    Bad:  if self._observability_enabled: self._client.trace(...)
    Good: context = self.create_trace(...)   # always returns something callable
          context.record_generation(...)     # works whether enabled or not

This means observability failures NEVER propagate to inference failures.
Langfuse being unreachable = silent no-op, not a 500 error.

Langfuse data model used here:
    Trace      → one per HTTP request, keyed on X-Request-ID
    Generation → one per LLM call, nested inside the trace
                 first-class fields: model, tokens, cost, latency

The trace_id == request_id correlation is the key observability win:
any request in your HTTP logs can be looked up directly in Langfuse.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.config import Settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Abstract interface — callers depend only on this
# ---------------------------------------------------------------------------


class ObservabilityContext(ABC):
    """Per-request observability context."""

    @abstractmethod
    def record_generation(
        self,
        *,
        model: str,
        model_parameters: dict,
        input_messages: list[dict],
        output: str,
        usage: dict,
        start_time: datetime,
        end_time: datetime,
        metadata: dict | None = None,
    ) -> None:
        pass

    @abstractmethod
    def record_error(
        self,
        *,
        error: Exception,
        metadata: dict | None = None,
    ) -> None:
        pass


# ---------------------------------------------------------------------------
# Null Object implementation
# ---------------------------------------------------------------------------


class NullObservabilityContext(ObservabilityContext):
    """No-op context."""

    def record_generation(self, **kwargs: Any) -> None:
        pass

    def record_error(self, **kwargs: Any) -> None:
        pass


# ---------------------------------------------------------------------------
# Langfuse-backed implementation
# ---------------------------------------------------------------------------


class LangfuseObservabilityContext(ObservabilityContext):
    """Wraps a live Langfuse trace."""

    def __init__(self, trace: Any) -> None:
        self._trace = trace

    def record_generation(
        self,
        *,
        model: str,
        model_parameters: dict,
        input_messages: list[dict],
        output: str,
        usage: dict,
        start_time: datetime,
        end_time: datetime,
        metadata: dict | None = None,
    ) -> None:
        try:
            self._trace.generation(
                name="llm-inference",
                model=model,
                model_parameters=model_parameters,
                input=input_messages,
                output=output,
                usage=usage,
                start_time=start_time,
                end_time=end_time,
                metadata=metadata or {},
            )
        except Exception as exc:
            logger.warning("Langfuse record_generation failed: %s", exc)

    def record_error(
        self,
        *,
        error: Exception,
        metadata: dict | None = None,
    ) -> None:
        try:
            self._trace.event(
                name="inference-error",
                level="ERROR",
                metadata={
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    **(metadata or {}),
                },
            )
        except Exception as exc:
            logger.warning("Langfuse record_error failed: %s", exc)


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class LangfuseClient:
    """
    Langfuse SDK lifecycle manager.

    LANGFUSE_ENABLED=false
        -> Null Object mode

    LANGFUSE_ENABLED=true
        -> Attempts SDK initialization
        -> Falls back safely on failure
    """

    def __init__(self, settings: "Settings") -> None:
        self._enabled = settings.LANGFUSE_ENABLED
        self._client: Any | None = None

        if not self._enabled:
            logger.info("Langfuse disabled (LANGFUSE_ENABLED=false)")
            return

        try:
            # Explicit credential validation
            if not settings.LANGFUSE_PUBLIC_KEY:
                raise ValueError("LANGFUSE_PUBLIC_KEY is required")

            if not settings.LANGFUSE_SECRET_KEY.get_secret_value():
                raise ValueError("LANGFUSE_SECRET_KEY is required")

            from langfuse import Langfuse

            self._client = Langfuse(
                public_key=settings.LANGFUSE_PUBLIC_KEY,
                secret_key=settings.LANGFUSE_SECRET_KEY.get_secret_value(),
                host=settings.LANGFUSE_HOST,
            )

            logger.info(
                "Langfuse initialized",
                extra={"host": settings.LANGFUSE_HOST},
            )

        except Exception as exc:
            logger.warning(
                "Langfuse initialization failed — tracing disabled: %s",
                exc,
            )
            self._enabled = False

    @property
    def is_enabled(self) -> bool:
        return self._enabled and self._client is not None

    def create_trace(
        self,
        *,
        trace_id: str,
        name: str,
        metadata: dict | None = None,
        tags: list[str] | None = None,
    ) -> ObservabilityContext:
        """
        Create one trace per request.

        Always returns an ObservabilityContext.
        Never raises.
        """
        if not self.is_enabled:
            return NullObservabilityContext()

        if self._client is None:
            return NullObservabilityContext()

        try:
            trace = self._client.trace(
                id=trace_id,
                name=name,
                metadata=metadata or {},
                tags=tags or [],
            )

            return LangfuseObservabilityContext(trace)

        except Exception as exc:
            logger.warning("Failed to create Langfuse trace: %s", exc)
            return NullObservabilityContext()

    def flush(self) -> None:
        """Flush pending events."""
        if self.is_enabled:
            if self._client is None:
                return

            try:
                self._client.flush()
            except Exception as exc:
                logger.warning("Langfuse flush failed: %s", exc)


    def shutdown(self) -> None:
        """Graceful shutdown."""
        if self.is_enabled:
            if self._client is None:
                return

            try:
                self._client.shutdown()
                logger.info("Langfuse shut down gracefully")
            except Exception as exc:
                logger.warning("Langfuse shutdown error: %s", exc)