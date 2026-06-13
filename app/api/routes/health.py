"""Health check endpoints.

- /health      — Liveness probe: "is the process alive?"
- /health/ready — Readiness probe: "can it serve traffic?"

Azure Container Apps (and Kubernetes) use these to decide whether
to restart a container or remove it from the load balancer.
"""

import logging

from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

from app.config import get_settings
from app.models.responses import HealthResponse, ReadinessResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    """Liveness probe — returns 200 if the process is running."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT.value,
    )


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness(request: Request) -> JSONResponse:
    """Readiness probe — validates all dependencies are operational."""
    settings = get_settings()
    llm_service = request.app.state.llm_service

    checks = {
    "api_key_configured": bool(
        settings.OPENAI_API_KEY.get_secret_value()
        or settings.AZURE_OPENAI_API_KEY.get_secret_value()
        or settings.GROQ_API_KEY.get_secret_value()
    ),
    "llm_provider_healthy": await llm_service.is_healthy(),
}

    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    logger.info(
        "Readiness check",
        extra={"status": "ready" if all_healthy else "not_ready", "checks": checks},
    )

    return JSONResponse(
        status_code=status_code,
        content=ReadinessResponse(
            status="ready" if all_healthy else "not_ready",
            checks=checks,
        ).model_dump(),
    )
