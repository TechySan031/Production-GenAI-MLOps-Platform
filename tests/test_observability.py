"""Tests for the Langfuse observability client."""

import os
from datetime import datetime
from unittest.mock import patch

from app.observability.langfuse_client import LangfuseClient


def _make_settings(langfuse_enabled: bool = False):
    """Create a Settings instance with Langfuse configured."""
    os.environ.setdefault("OPENAI_API_KEY", "sk-test-key")
    env_overrides = {
        "LANGFUSE_ENABLED": str(langfuse_enabled).lower(),
        "LANGFUSE_PUBLIC_KEY": "",
        "LANGFUSE_SECRET_KEY": "",
    }

    from app.config import get_settings

    get_settings.cache_clear()

    with patch.dict(os.environ, env_overrides):
        get_settings.cache_clear()
        settings = get_settings()

    get_settings.cache_clear()
    return settings


class TestLangfuseClientDisabled:
    """Behaviour when LANGFUSE_ENABLED=false (the safe default)."""

    def test_is_not_enabled(self):
        from app.observability.langfuse_client import LangfuseClient

        client = LangfuseClient(_make_settings(langfuse_enabled=False))
        assert not client.is_enabled

    def test_create_trace_returns_null_context(self):
        from app.observability.langfuse_client import LangfuseClient, NullObservabilityContext

        client = LangfuseClient(_make_settings(langfuse_enabled=False))
        ctx = client.create_trace(trace_id="test-id", name="test")
        assert isinstance(ctx, NullObservabilityContext)

    def test_flush_does_not_raise(self):
        from app.observability.langfuse_client import LangfuseClient

        LangfuseClient(_make_settings(langfuse_enabled=False)).flush()

    def test_shutdown_does_not_raise(self):
        from app.observability.langfuse_client import LangfuseClient

        LangfuseClient(_make_settings(langfuse_enabled=False)).shutdown()


class TestNullObservabilityContext:
    """NullObservabilityContext must be safe to call unconditionally."""

    # pyrefly: ignore [missing-attribute]
    _now = datetime.now(datetime.UTC)

    def _context(self):
        from app.observability.langfuse_client import NullObservabilityContext

        return NullObservabilityContext()

    def test_record_generation_does_not_raise(self):
        self._context().record_generation(
            model="gpt-4o-mini",
            model_parameters={"temperature": 0.7, "max_tokens": None},
            input_messages=[{"role": "user", "content": "Hello"}],
            output="Hi!",
            usage={"input": 5, "output": 3, "total": 8, "unit": "TOKENS"},
            start_time=self._now,
            end_time=self._now,
            metadata={"latency_ms": 123.4},
        )

    def test_record_error_does_not_raise(self):
        self._context().record_error(
            error=RuntimeError("provider down"),
            metadata={"latency_ms": 50.0},
        )


class TestLangfuseClientEnabled:
    """Behaviour when Langfuse SDK is available but credentials are fake."""

    def test_initialization_failure_degrades_to_disabled(self):
        pass

    with patch.dict(
        os.environ,
        {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "",
            "LANGFUSE_SECRET_KEY": "",
        },
        clear=False,
    ):
        settings = _make_settings(langfuse_enabled=True)
        client = LangfuseClient(settings)

        assert not client.is_enabled

    def test_create_trace_returns_null_context_when_sdk_init_failed(self):
        from app.observability.langfuse_client import LangfuseClient, NullObservabilityContext

        client = LangfuseClient(_make_settings(langfuse_enabled=True))
        ctx = client.create_trace(trace_id="abc", name="test")
        assert isinstance(ctx, NullObservabilityContext)
