"""Shared test fixtures.

Provides a TestClient with a mocked LLM service so tests
run without a real OpenAI API key or network access.
"""

import os

import pytest
from fastapi.testclient import TestClient

from app.models.responses import (
    ChatChoice,
    ChatMessageResponse,
    ChatResponse,
    UsageInfo,
)


def _mock_chat_response() -> ChatResponse:
    """Create a deterministic mock chat response."""
    return ChatResponse(
        id="chatcmpl-test123abc",
        created=1700000000,
        model="gpt-4o-mini",
        choices=[
            ChatChoice(
                index=0,
                message=ChatMessageResponse(
                    role="assistant",
                    content="Hello! I'm a test response from the mock LLM.",
                ),
                finish_reason="stop",
            )
        ],
        usage=UsageInfo(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
        ),
    )


@pytest.fixture()
def client():
    """Create a FastAPI TestClient with a mocked LLM service."""
    # Set required env vars BEFORE importing the app
    os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-not-real")
    os.environ.setdefault("LOG_FORMAT", "text")
    os.environ.setdefault("ENVIRONMENT", "development")

    # Clear the settings cache to pick up test env vars
    from app.config import get_settings

    get_settings.cache_clear()

    from app.main import create_app

    app = create_app()

    with TestClient(app) as test_client:
        # Override the real LLM service with a mock
        from unittest.mock import AsyncMock, MagicMock

    # Override the real LLM service with a mock
    mock_service = MagicMock()

    mock_service.provider_name = "openai"

    # async methods
    mock_service.is_healthy = AsyncMock(return_value=True)
    mock_service.chat = AsyncMock(return_value=_mock_chat_response())

    # sync method
    mock_service.shutdown = MagicMock()

    app.state.llm_service = mock_service

    yield test_client

    # Cleanup
    get_settings.cache_clear()
