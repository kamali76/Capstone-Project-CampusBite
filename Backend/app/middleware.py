"""Request-level middleware: request id, logging, response time."""
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("campusbite.requests")


def register_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def log_and_time_requests(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        start = time.perf_counter()
        logger.info("[%s] --> %s %s", request_id, request.method, request.url.path)

        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "[%s] !! %s %s crashed after %.1f ms",
                request_id, request.method, request.url.path, elapsed_ms,
            )
            response = JSONResponse(
                status_code=500, content={"detail": "Internal server error"}
            )

        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time"] = f"{elapsed_ms:.2f}ms"
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "[%s] <-- %s %s %s (%.1f ms)",
            request_id, request.method, request.url.path, response.status_code, elapsed_ms,
        )
        return response
