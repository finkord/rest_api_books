import redis.asyncio as redis
from app.core.config import settings
from typing import Optional

redis_pool: Optional[redis.Redis] = None

def init_redis():
    global redis_pool
    if redis_pool is None:
        redis_pool = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def close_redis():
    global redis_pool
    if redis_pool:
        await redis_pool.aclose()
        redis_pool = None

async def get_redis() -> redis.Redis:
    global redis_pool
    if redis_pool is None:
        init_redis()
    return redis_pool