from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from aegis_middleware import SlidingWindowRateLimiter

app = FastAPI(title="Aegis Mini Demo")

# Redis connection
redis = Redis.from_url("redis://localhost:6379")

# Aegis rate limiter (library usage)
limiter = SlidingWindowRateLimiter(
    redis=redis,
    rate_limit=5,
    window_size=60,
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host

    allowed = await limiter.is_allowed(client_ip)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )

    return await call_next(request)


@app.get("/ping")
async def ping():
    return {"message": "pong"}
