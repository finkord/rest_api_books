import time
import logging
from typing import Optional
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class RedisRateLimiter:
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self._redis_client = redis_client

    async def _get_client(self) -> redis.Redis:
        if self._redis_client is not None:
            return self._redis_client
        
        from app.database.redis import get_redis
        return await get_redis()

    async def check_allowance(self, key: str, limit: int, window: int = 60, redis_client: Optional[redis.Redis] = None) -> bool:
        """
        Check if the request is allowed based on the sliding window rate limiting algorithm.
        Returns True if allowed (or fail-open on error), False if limit exceeded.
        """
        try:
            client = redis_client or await self._get_client()
            now_ms = int(time.time() * 1000)
            window_start_ms = now_ms - (window * 1000)

            async with client.pipeline(transaction=True) as pipe:
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
                await client.zrem(key, str(now_ms))
                return False

            return True
        except Exception as e:
            logger.error(f"Redis rate limiting error (failing open): {e}")
            return True # Fail-open strategy
