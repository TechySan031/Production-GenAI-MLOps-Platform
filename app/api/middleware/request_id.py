"""Request ID middleware.

Injects a unique X-Request-ID into every request/response cycle.
If the client sends one, we honor it (enables end-to-end tracing).
If not, we generate a UUID4.

This becomes the correlation ID for logging, Langfuse traces,
and debugging across distributed services.
"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that ensures every request has a unique trace ID."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Honor client-provided ID or generate a new one
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))

        # Store on request state so route handlers can access it
        request.state.request_id = request_id

        response = await call_next(request)

        # Echo back in response headers for client-side correlation
        response.headers["x-request-id"] = request_id

        return response
