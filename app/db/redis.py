import logging
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.requests import HTTPConnection
from redis import asyncio as aioredis
from redis.asyncio import Redis

from app.config import settings
from app.core.log_messages import REDIS_CONNECTED, REDIS_DISCONNECTED
from app.exceptions.http import AppHTTPError
from app.exceptions.messages import REDIS_NOT_INITIALIZED

logger = logging.getLogger(__name__)


async def connect(app: FastAPI) -> None:
    app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True, socket_timeout=None)
    logger.info(REDIS_CONNECTED)


async def disconnect(app: FastAPI) -> None:
    redis: Redis | None = getattr(app.state, "redis", None)

    if redis is not None:
        await redis.aclose()
        logger.info(REDIS_DISCONNECTED)


def get_redis_client(conn: HTTPConnection) -> Redis:
    redis: Redis | None = getattr(conn.app.state, "redis", None)

    if redis is None:
        raise AppHTTPError.service_unavailable(REDIS_NOT_INITIALIZED)

    return redis


RedisDep = Annotated[Redis, Depends(get_redis_client)]
