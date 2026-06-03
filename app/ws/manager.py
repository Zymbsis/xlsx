import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

import anyio
import redis
from fastapi import Depends, WebSocket
from redis.asyncio import Redis

from app.db.redis import RedisDep
from app.schemas.ws_events import WSEvent


class WebSocketManager:
    def __init__(self, redis_client: Redis) -> None:
        self._redis_client = redis_client

    def _channel(self, session_id: uuid.UUID) -> str:
        return f"ws:{session_id!s}"

    async def publish(self, session_id: uuid.UUID | None, payload: WSEvent) -> None:
        if session_id:
            await self._redis_client.publish(self._channel(session_id), payload.model_dump_json())

    @asynccontextmanager
    async def listen(self, websocket: WebSocket) -> AsyncIterator[uuid.UUID]:
        session_id = uuid.uuid4()
        pubsub = self._redis_client.pubsub()

        await pubsub.subscribe(self._channel(session_id))
        await websocket.send_json({"ws_session_id": str(session_id)})

        async def _reader() -> None:
            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        await websocket.send_text(message["data"])
            except (anyio.get_cancelled_exc_class(), redis.TimeoutError):
                pass

        async with anyio.create_task_group() as tg:
            tg.start_soon(_reader)
            try:
                yield session_id
            finally:
                tg.cancel_scope.cancel()
                await pubsub.unsubscribe(self._channel(session_id))
                await pubsub.aclose()


def get_ws_manager(redis_client: RedisDep) -> WebSocketManager:
    return WebSocketManager(redis_client)


WSManagerDep = Annotated[WebSocketManager, Depends(get_ws_manager)]
