from app.config import LLMProvider, Settings
from app.services.providers.azure_openai_provider import AzureOpenAIProvider
from app.services.providers.base import BaseProvider
from app.services.providers.groq_provider import GroqProvider          # ← add
from app.services.providers.openai_provider import OpenAIProvider


def create_provider(settings: Settings) -> BaseProvider:
    """Create the appropriate LLM provider based on configuration."""
    match settings.LLM_PROVIDER:
        case LLMProvider.OPENAI:
            return OpenAIProvider(settings)
        case LLMProvider.AZURE_OPENAI:
            return AzureOpenAIProvider(settings)
        case LLMProvider.GROQ:                                          # ← add
            return GroqProvider(settings)
        case _:
            raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")