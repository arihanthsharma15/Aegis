import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.endpoints import router as api_router
from app.core.config import settings
from app.core.logger import setup_logging
from app.middleware.rate_limiter import SlidingWindowRateLimiter
from app.services.metrics_store import metrics_store

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Aegis API")
rate_limiter = SlidingWindowRateLimiter()

cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path
    is_internal_metrics_route = path.startswith("/metrics") or path == "/dashboard"

    if not is_internal_metrics_route:
        await metrics_store.record_request()

    allowed = True if is_internal_metrics_route else await rate_limiter.is_allowed(client_ip)
    if not allowed:
        if not is_internal_metrics_route:
            await metrics_store.record_blocked_request()
        logger.warning("Rate limit exceeded | IP=%s", client_ip)
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."},
        )

    response = await call_next(request)
    return response


app.include_router(api_router)
