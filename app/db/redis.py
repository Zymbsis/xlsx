from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.requests import HTTPConnection
from redis import asyncio as aioredis
from redis.asyncio import Redis

from app.config import settings


async def connect(app: FastAPI) -> None:
    app.state.redis = aioredis.from_url(
        settings.redis_url, decode_responses=True, socket_timeout=None
    )


async def disconnect(app: FastAPI) -> None:
    redis: Redis | None = getattr(app.state, "redis", None)

    if redis is not None:
        await redis.aclose()


def get_redis(conn: HTTPConnection) -> Redis:
    redis: Redis | None = getattr(conn.app.state, "redis", None)

    if redis is None:
        raise RuntimeError("Redis is not initialized")

    return redis


RedisDep = Annotated[Redis, Depends(get_redis)]
