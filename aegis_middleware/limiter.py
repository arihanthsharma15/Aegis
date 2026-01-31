import time
from redis.asyncio import Redis

class SlidingWindowRateLimiter:
    def __init__(
        self,
        redis: Redis,
        rate_limit: int = 60,
        window_size: int = 60,
        key_prefix: str = "rate_limit",
    ):
        self.redis = redis
        self.rate_limit = rate_limit
        self.window_size = window_size
        self.key_prefix = key_prefix

    async def is_allowed(self, identifier: str) -> bool:
        current_time = time.time()
        key = f"{self.key_prefix}:{identifier}"

        await self.redis.zremrangebyscore(
            key, 0, current_time - self.window_size
        )

        count = await self.redis.zcard(key)
        if count >= self.rate_limit:
            return False

        await self.redis.zadd(key, {str(current_time): current_time})
        await self.redis.expire(key, self.window_size + 1)

        return True
