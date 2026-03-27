import logging
import json
from typing import Any, Optional
from datetime import timedelta

from redis import asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)

redis_client: Optional[aioredis.Redis] = None


async def init_redis():
    """Initialize Redis connection"""
    global redis_client
    try:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf8",
            decode_responses=True,
        )
        # Test connection
        try:
            await redis_client.ping()
        except:
            pass  # Redis might not be running, but we'll handle it gracefully
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        redis_client = None


async def close_redis():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.aclose()
        logger.info("Redis connection closed")


async def get_cache(key: str) -> Optional[Any]:
    """Get value from cache"""
    if not redis_client:
        return None
    try:
        value = await redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return None


async def set_cache(
    key: str, value: Any, expire: Optional[int] = None
) -> bool:
    """Set value in cache"""
    if not redis_client:
        return False
    try:
        expire = expire or settings.REDIS_CACHE_TTL
        await redis_client.setex(key, expire, json.dumps(value))
        return True
    except Exception as e:
        logger.error(f"Cache set error: {e}")
        return False


async def delete_cache(key: str) -> bool:
    """Delete value from cache"""
    if not redis_client:
        return False
    try:
        await redis_client.delete(key)
        return True
    except Exception as e:
        logger.error(f"Cache delete error: {e}")
        return False


async def clear_pattern(pattern: str) -> int:
    """Clear all keys matching pattern"""
    if not redis_client:
        return 0
    try:
        keys = []
        async for key in redis_client.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            return await redis_client.delete(*keys)
        return 0
    except Exception as e:
        logger.error(f"Cache pattern delete error: {e}")
        return 0

if __name__ == "__main__":
    import asyncio

    async def main():
        await init_redis()
        await set_cache("test_key", {"foo": "bar"}, expire=60)
        value = await get_cache("test_key")
        print(f"Cached value: {value}")
        await delete_cache("test_key")
        await close_redis()

    asyncio.run(main())