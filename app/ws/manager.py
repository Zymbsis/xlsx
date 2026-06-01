import uuid
from contextlib import asynccontextmanager

import anyio
import redis.exceptions as redis_exceptions
from fastapi import WebSocket
from redis.asyncio import Redis

from app.schemas.ws_events import WSEvent


class WebSocketManager:
    def _channel(self, session_id: uuid.UUID | None) -> str:
        return f"ws:{str(session_id)}"

    async def publish(
        self, redis: Redis, session_id: uuid.UUID | None, payload: WSEvent
    ):
        if session_id:
            await redis.publish(
                self._channel(str(session_id)), payload.model_dump_json()
            )

    @asynccontextmanager
    async def listen(self, websocket: WebSocket, redis: Redis):
        session_id = str(uuid.uuid4())
        pubsub = redis.pubsub()

        await pubsub.subscribe(self._channel(session_id))
        await websocket.send_json({"ws_session_id": session_id})

        async def _reader():
            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        await websocket.send_text(message["data"])
            except (anyio.get_cancelled_exc_class(), redis_exceptions.TimeoutError):
                pass

        async with anyio.create_task_group() as tg:
            tg.start_soon(_reader)
            try:
                yield session_id
            finally:
                tg.cancel_scope.cancel()
                await pubsub.unsubscribe(self._channel(session_id))
                await pubsub.aclose()


ws_manager = WebSocketManager()
