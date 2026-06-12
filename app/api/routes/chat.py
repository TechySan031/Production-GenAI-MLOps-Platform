"""Chat completion endpoint — OpenAI-compatible.

This is the primary inference endpoint. It accepts the same schema
as OpenAI's /v1/chat/completions and delegates to the configured
LLM provider via LLMService.
"""

import logging

from fastapi import APIRouter, HTTPException, Request
from openai import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    RateLimitError,
)

from app.models.requests import ChatRequest
from app.models.responses import ChatResponse, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        502: {"model": ErrorResponse, "description": "LLM provider error"},
    },
)
async def chat_completion(
    chat_request: ChatRequest, request: Request
) -> ChatResponse:
    """Process a chat completion request."""
    request_id = getattr(request.state, "request_id", "unknown")
    llm_service = request.app.state.llm_service

    logger.info(
        "Chat request received",
        extra={
            "request_id": request_id,
            "model": chat_request.model,
            "message_count": len(chat_request.messages),
        },
    )

    # Streaming not yet implemented — fail explicitly
    if chat_request.stream:
        raise HTTPException(
            status_code=501,
            detail="Streaming is not yet supported. Set stream=false.",
        )

    try:
        response = await llm_service.chat(chat_request, request_id=request_id)

        logger.info(
            "Chat request completed",
            extra={
                "request_id": request_id,
                "model": response.model,
                "total_tokens": response.usage.total_tokens,
            },
        )

        return response

    except AuthenticationError as e:
        logger.error(
            "Authentication failed",
            extra={"request_id": request_id, "error": str(e)},
        )
        raise HTTPException(
            status_code=401, detail="LLM provider authentication failed."
        )

    except RateLimitError as e:
        logger.warning(
            "Rate limit exceeded",
            extra={"request_id": request_id, "error": str(e)},
        )
        raise HTTPException(
            status_code=429,
            detail="LLM provider rate limit exceeded. Retry later.",
        )

    except APIConnectionError as e:
        logger.error(
            "Connection error",
            extra={"request_id": request_id, "error": str(e)},
        )
        raise HTTPException(
            status_code=502, detail="Failed to connect to LLM provider."
        )

    except APIError as e:
        logger.error(
            "LLM API error",
            extra={"request_id": request_id, "error": str(e)},
        )
        raise HTTPException(
            status_code=502, detail=f"LLM provider error: {e.message}"
        )

    except Exception as e:
        logger.exception(
            "Unexpected error during chat completion",
            extra={"request_id": request_id},
        )
        raise HTTPException(status_code=500, detail="Internal server error.")
