from redis.asyncio import Redis
from app.core.config import settings

# Global Redis client (singleton style)
redis_client: Redis | None = None


async def get_redis() -> Redis:
    """
    Returns a singleton async Redis client.
    Creates the connection only once.
    """
    global redis_client

    if redis_client is None:
        redis_client = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )

    return redis_client
