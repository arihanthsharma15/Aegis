import time
from app.services.redis_client import get_redis
from app.core.config import settings


class SlidingWindowRateLimiter:
    """
    Sliding Window Rate Limiter using Redis Sorted Sets.
    """

    def __init__(self):
        self.rate_limit = settings.RATE_LIMIT
        self.window_size = settings.WINDOW_SIZE

    async def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed for given identifier (IP).
        Returns True if allowed, False if rate-limited.
        """
        redis = await get_redis()
        current_time = time.time()

        key = f"rate_limit:{identifier}"

        # 1. Remove timestamps outside the window
        await redis.zremrangebyscore(
            key,
            0,
            current_time - self.window_size
        )

        # 2. Count requests in current window
        request_count = await redis.zcard(key)

        if request_count >= self.rate_limit:
            return False

        # 3. Add current request timestamp
        await redis.zadd(key, {str(current_time): current_time})

        # 4. Set expiry slightly greater than window
        await redis.expire(key, self.window_size + 1)

        return True
