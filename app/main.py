from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.middleware.rate_limiter import SlidingWindowRateLimiter
from app.api.endpoints import router as api_router
from app.core.logger import setup_logging

import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Aegis API")

rate_limiter = SlidingWindowRateLimiter()


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    Middleware that rate limits incoming requests
    before they hit any route.
    """

    client_ip = request.client.host if request.client else "unknown"

    allowed = await rate_limiter.is_allowed(client_ip)

    if not allowed:
        logger.warning(f"Rate limit exceeded | IP={client_ip}")
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."}
        )

    response = await call_next(request)
    return response


# Register API routes
app.include_router(api_router)
