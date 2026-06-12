"""FastAPI application factory.

Uses the modern lifespan context manager pattern (not the deprecated
@app.on_event decorators) to manage startup and shutdown lifecycle.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware.request_id import RequestIDMiddleware
from app.api.routes import chat, health
from app.config import Environment, get_settings
from app.logging_config import setup_logging
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup and shutdown logic."""
    # --- Startup ---
    settings = get_settings()
    setup_logging()

    logger.info(
        "Starting %s v%s",
        settings.APP_NAME,
        settings.APP_VERSION,
        extra={"environment": settings.ENVIRONMENT.value},
    )

    # Initialize LLM Service with the configured provider
    app.state.llm_service = LLMService(settings)

    logger.info(
        "Application startup complete",
        extra={"provider": app.state.llm_service.provider_name},
    )

    yield

    # --- Shutdown ---
    app.state.llm_service.shutdown()  # Flushes Langfuse before process exits
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    """Application factory — creates and configures the FastAPI instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Production GenAI MLOps Platform — LLM Gateway",
        docs_url="/docs" if settings.ENVIRONMENT != Environment.PRODUCTION else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != Environment.PRODUCTION else None,
        lifespan=lifespan,
    )

    # --- Middleware (order matters: first added = outermost layer) ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIDMiddleware)

    # --- Routes ---
    app.include_router(health.router)
    app.include_router(chat.router)

    return app


# Module-level app instance for uvicorn
app = create_app()
