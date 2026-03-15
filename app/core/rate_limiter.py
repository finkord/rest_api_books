import os
import time
import logging
from typing import Optional
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class RedisRateLimiter:
    def __init__(self, redis_url: Optional[str] = None):
        if redis_url is None:
            redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.redis_client = redis.from_url(redis_url, decode_responses=True)

    async def check_allowance(self, key: str, limit: int, window: int = 60) -> bool:
        """
        Check if the request is allowed based on the sliding window rate limiting algorithm.
        Returns True if allowed (or fail-open on error), False if limit exceeded.
        """
        try:
            now_ms = int(time.time() * 1000)
            window_start_ms = now_ms - (window * 1000)

            async with self.redis_client.pipeline(transaction=True) as pipe:
                # 1. Remove timestamps older than the window
                pipe.zremrangebyscore(key, 0, window_start_ms)
                # 2. Add current timestamp
                pipe.zadd(key, {str(now_ms): now_ms})
                # 3. Count requests in the window
                pipe.zcard(key)
                # 4. Set TTL for the key to avoid memory leaks
                pipe.pexpire(key, window * 1000)
                
                results = await pipe.execute()

            request_count = results[2]  # result of zcard

            if request_count > limit:
                # Limit exceeded, remove the request we just added to prevent endlessly punishing the user
                await self.redis_client.zrem(key, now_ms)
                return False

            return True
        except redis.RedisError as e:
            logger.error(f"Redis rate limiting error (failing open): {e}")
            return True # Fail-open strategy
