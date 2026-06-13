"""Application configuration using Pydantic Settings.

Loads from environment variables and .env file.
Validated at startup — the app crashes immediately if config is invalid,
not at 3 AM on a Saturday when a request hits a missing key.
"""

from enum import Enum
from functools import lru_cache

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Deployment environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LLMProvider(str, Enum):
    """Supported LLM provider backends."""

    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    GROQ = "groq"  # ← add this


class Settings(BaseSettings):
    """Application settings with typed validation and .env support."""

    # --- Application ---
    APP_NAME: str = "GenAI MLOps Platform"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False

    # --- Server ---
    HOST: str = "0.0.0.0"  # nosec B104
    PORT: int = 8000

    # --- LLM Provider Selection ---
    LLM_PROVIDER: LLMProvider = LLMProvider.OPENAI

    # --- OpenAI ---
    OPENAI_API_KEY: SecretStr = SecretStr("")
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_API_BASE: str | None = None
    OPENAI_TIMEOUT: int = 30
    OPENAI_MAX_RETRIES: int = 3

    # --- Azure OpenAI (future Phase 3) ---
    AZURE_OPENAI_API_KEY: SecretStr = SecretStr("")
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-10-21"
    AZURE_OPENAI_DEPLOYMENT: str = ""

    # --- Groq ---
    GROQ_API_KEY: SecretStr = SecretStr("")
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    # --- Langfuse Observability ---
    LANGFUSE_ENABLED: bool = False
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: SecretStr = SecretStr("")
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # --- Logging ---
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" for production, "text" for local dev

    # --- CORS ---
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

    # --- Validators ---
    @model_validator(mode="after")
    def validate_provider_configuration(self) -> "Settings":
        """
        Fail fast at startup if required provider settings are missing.
        Better to crash with a clear message at boot than fail silently at request time.
        """
        if self.LLM_PROVIDER == LLMProvider.AZURE_OPENAI:
            missing = []
            if not self.AZURE_OPENAI_ENDPOINT:
                missing.append("AZURE_OPENAI_ENDPOINT")
            if not self.AZURE_OPENAI_DEPLOYMENT:
                missing.append("AZURE_OPENAI_DEPLOYMENT")
            if not self.AZURE_OPENAI_API_KEY.get_secret_value():
                missing.append("AZURE_OPENAI_API_KEY")
            if missing:
                raise ValueError(f"LLM_PROVIDER=azure_openai requires: {', '.join(missing)}")

        if self.LLM_PROVIDER == LLMProvider.GROQ:  # ← add this block
            if not self.GROQ_API_KEY.get_secret_value():
                raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=groq")

        return self


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton. Call get_settings.cache_clear() in tests."""
    return Settings()
