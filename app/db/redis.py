import redis.asyncio as aioredis

from app.config import settings

_redis: aioredis.Redis | None = None


async def connect():
    global _redis
    _redis = aioredis.from_url(settings.redis_url, socket_timeout=None)


async def disconnect():
    if _redis:
        await _redis.aclose()


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis is not connected")
    return _redis
