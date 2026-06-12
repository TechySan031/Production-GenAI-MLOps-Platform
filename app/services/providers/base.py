"""Abstract base class for LLM providers.

Every provider (OpenAI, Azure OpenAI, Anthropic, local models) must
implement this interface. This is the core of the provider abstraction
layer — routes and services never know which provider they're talking to.
"""

from abc import ABC, abstractmethod

from app.models.requests import ChatRequest
from app.models.responses import ChatResponse


class BaseProvider(ABC):
    """Abstract base class that all LLM providers must implement."""

    @abstractmethod
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Execute a chat completion request and return a structured response."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is reachable and operational."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return a human-readable provider identifier."""
        ...
