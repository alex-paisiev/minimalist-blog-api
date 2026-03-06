import json
from typing import Any

import redis.asyncio as redis
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()

settings = get_settings()

redis_client: redis.Redis | None = None


async def init_redis() -> None:
    """Initialize the Redis connection pool."""
    global redis_client
    try:
        redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )
        await redis_client.ping()
        logger.info("redis_connected", url=settings.redis_url)
    except Exception:
        logger.warning("redis_unavailable", url=settings.redis_url)
        redis_client = None


async def close_redis() -> None:
    """Close the Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


async def cache_get(key: str) -> Any | None:
    """Get a value from cache. Returns None on miss or error."""
    if not redis_client:
        return None
    try:
        data = await redis_client.get(key)
        return json.loads(data) if data else None
    except Exception:
        logger.warning("cache_read_failed", key=key)
        return None


async def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    """Set a value in cache with optional TTL."""
    if not redis_client:
        return
    try:
        ttl = ttl or settings.cache_ttl
        await redis_client.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception:
        logger.warning("cache_write_failed", key=key)


async def cache_invalidate(pattern: str) -> None:
    """Invalidate cache keys matching a pattern."""
    if not redis_client:
        return
    try:
        async for key in redis_client.scan_iter(match=pattern):
            await redis_client.delete(key)
    except Exception:
        logger.warning("cache_invalidation_failed", pattern=pattern)
