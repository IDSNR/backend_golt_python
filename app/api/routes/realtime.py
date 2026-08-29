import asyncio
import os

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.modules.auth.service import auth_service
from app.services import realtime_service


router = APIRouter(prefix="/realtime", tags=["realtime"])


def resolve_user(token: str | None) -> str | None:
    if not token:
        return None

    user_id = auth_service.validate_session(token)
    if user_id:
        return user_id

    if os.getenv("APP_ENV", "development").lower() != "production" and token.startswith(("user-", "google-", "engagement-")):
        return token
    return None


@router.websocket("")
async def realtime_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        authentication = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
    except (TimeoutError, ValueError, WebSocketDisconnect):
        await websocket.close(code=4401, reason="Session required")
        return

    token = (
        authentication.get("token")
        if isinstance(authentication, dict) and authentication.get("type") == "authenticate"
        else None
    )
    user_id = resolve_user(token)
    if user_id is None:
        await websocket.close(code=4401, reason="Invalid or expired session")
        return

    realtime_service.connect(user_id, websocket)
    await websocket.send_json({"type": "connected"})
    try:
        while True:
            event = await websocket.receive_json()
            if event.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        realtime_service.disconnect(user_id, websocket)
