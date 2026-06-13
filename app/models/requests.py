"""Request schemas — OpenAI Chat Completions API compatible."""

from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in the conversation."""

    role: Literal["system", "user", "assistant"] = Field(
        ..., description="The role of the message author."
    )
    content: str = Field(..., description="The content of the message.", min_length=1)


class ChatRequest(BaseModel):
    """OpenAI-compatible chat completion request."""

    model: str | None = Field(
        default=None,
        description="Model to use. Defaults to server configuration if omitted.",
    )
    messages: list[ChatMessage] = Field(
        ..., description="List of messages in the conversation.", min_length=1
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature between 0 and 2.",
    )
    max_tokens: int | None = Field(
        default=None,
        ge=1,
        le=128_000,
        description="Maximum number of tokens to generate.",
    )
    stream: bool = Field(
        default=False,
        description="Whether to stream the response. Not yet supported.",
    )
