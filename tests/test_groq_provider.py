"""Tests for the Groq provider."""

import os
from unittest.mock import AsyncMock, patch


def _make_settings():
    os.environ["GROQ_API_KEY"] = "gsk-test-key-not-real"
    os.environ["LLM_PROVIDER"] = "groq"
    os.environ.setdefault("OPENAI_API_KEY", "sk-test")

    from app.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    get_settings.cache_clear()
    return settings


class TestGroqProvider:
    def test_provider_name_is_groq(self):
        with patch("app.services.providers.groq_provider.AsyncOpenAI"):
            from app.services.providers.groq_provider import GroqProvider

            provider = GroqProvider(_make_settings())

            assert provider.provider_name == "groq"

    def test_uses_groq_base_url(self):
        with patch("app.services.providers.groq_provider.AsyncOpenAI") as mock_openai:
            from app.services.providers.groq_provider import (
                _GROQ_API_BASE,
                GroqProvider,
            )

            GroqProvider(_make_settings())

            call_kwargs = mock_openai.call_args.kwargs

            assert call_kwargs["base_url"] == _GROQ_API_BASE

    def test_default_model_from_settings(self):
        with patch("app.services.providers.groq_provider.AsyncOpenAI"):
            from app.services.providers.groq_provider import GroqProvider

            settings = _make_settings()
            provider = GroqProvider(settings)

            assert provider._settings.GROQ_MODEL == "llama-3.1-8b-instant"


class TestGroqViaHTTPEndpoint:
    """Integration-style tests using the FastAPI TestClient with a mocked Groq service."""

    VALID_PAYLOAD = {
        "messages": [{"role": "user", "content": "Hello!"}],
    }

    def _get_client(self):
        os.environ["GROQ_API_KEY"] = "gsk-test-not-real"
        os.environ["LLM_PROVIDER"] = "groq"
        os.environ.setdefault("OPENAI_API_KEY", "sk-test")
        os.environ.setdefault("LOG_FORMAT", "text")
        os.environ.setdefault("ENVIRONMENT", "development")

        from app.config import get_settings

        get_settings.cache_clear()

        from app.main import create_app
        from app.models.responses import ChatChoice, ChatMessageResponse, ChatResponse, UsageInfo

        app = create_app()

        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            mock_service = AsyncMock()
            mock_service.provider_name = "groq"
            mock_service.is_healthy.return_value = True
            mock_service.chat.return_value = ChatResponse(
                id="chatcmpl-groqtest",
                created=1700000000,
                model="llama-3.1-8b-instant",
                choices=[
                    ChatChoice(
                        index=0,
                        message=ChatMessageResponse(
                            role="assistant",
                            content="Hello from Groq!",
                        ),
                        finish_reason="stop",
                    )
                ],
                usage=UsageInfo(prompt_tokens=8, completion_tokens=12, total_tokens=20),
            )
            app.state.llm_service = mock_service
            yield client

        get_settings.cache_clear()

    def test_returns_200_with_groq_response(self):
        for client in self._get_client():
            response = client.post("/chat", json=self.VALID_PAYLOAD)
            assert response.status_code == 200
            assert response.json()["model"] == "llama-3.1-8b-instant"
            break

    def test_health_shows_groq_provider(self):
        for client in self._get_client():
            response = client.get("/health/ready")
            assert response.status_code == 200
            break
