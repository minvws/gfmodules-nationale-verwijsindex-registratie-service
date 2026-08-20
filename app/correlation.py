"""Correlation-id origination and propagation.

The registratie-service is the entry point of the chain, so it mints an
``X-GF-Correlation-ID`` when the caller does not supply one, binds it for the
duration of the request, echoes it on the response and attaches it to every
outbound call. That lets a single request be followed across the landscape.
"""

import logging
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

CORRELATION_ID_HEADER = "X-GF-Correlation-ID"
UNSET = "-"

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default=UNSET)


def correlation_headers() -> dict[str, str]:
    correlation_id = correlation_id_var.get()
    if correlation_id == UNSET:
        return {}
    return {CORRELATION_ID_HEADER: correlation_id}


class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        inbound = request.headers.get(CORRELATION_ID_HEADER)
        correlation_id = inbound or str(uuid.uuid4())
        token = correlation_id_var.set(correlation_id)
        logger.info(
            "correlation_id=%s %s %s (%s)",
            correlation_id,
            request.method,
            request.url.path,
            "from caller" if inbound else "minted",
        )
        try:
            response = await call_next(request)
            response.headers[CORRELATION_ID_HEADER] = correlation_id
            return response
        finally:
            correlation_id_var.reset(token)
