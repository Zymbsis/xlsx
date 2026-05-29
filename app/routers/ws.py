from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import settings
from app.ws.manager import ws_manager

router = APIRouter(tags=["ws"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    data = await websocket.receive_json()
    if data.get("token") != settings.api_key:
        await websocket.close(code=4003)
        return

    async with ws_manager.listen(websocket):
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
