import time
import logging

logger = logging.getLogger("mcp.middleware")

async def logging_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    logger.info(
        f"{request.method} {request.url.path} "
        f"status={response.status_code} "
        f"duration={duration:.4f}s"
    )

    return response