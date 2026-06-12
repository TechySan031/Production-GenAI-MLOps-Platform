"""Response schemas — OpenAI Chat Completions API compatible."""

import time
import uuid

from pydantic import BaseModel, Field


class ChatMessageResponse(BaseModel):
    """Assistant message in a completion response."""

    role: str = "assistant"
    content: str


class ChatChoice(BaseModel):
    """A single completion choice."""

    index: int = 0
    message: ChatMessageResponse
    finish_reason: str = "stop"


class UsageInfo(BaseModel):
    """Token usage statistics."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatResponse(BaseModel):
    """OpenAI-compatible chat completion response."""

    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:12]}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: list[ChatChoice]
    usage: UsageInfo


class HealthResponse(BaseModel):
    """Liveness probe response."""

    status: str = "healthy"
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    """Readiness probe response with component checks."""

    status: str
    checks: dict[str, bool]


class ErrorResponse(BaseModel):
    """Standardized error response."""

    error: str
    detail: str | None = None
    request_id: str | None = None
