"""WebSocket endpoint for real-time job status updates."""

from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.auth_core.security import decode_access_token

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/api/ws")
async def ws_job_updates(websocket: WebSocket) -> None:
    """WebSocket endpoint for pushing job events to connected clients.

    Authentication is done via a ``token`` query parameter containing a JWT.
    """
    # Must accept before we can close with a reason
    await websocket.accept()

    token = websocket.query_params.get("token")
    if not token:
        await websocket.send_json({"error": "Missing token"})
        await websocket.close(code=4001, reason="Missing token")
        return

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        await websocket.send_json({"error": "Invalid token"})
        await websocket.close(code=4001, reason="Invalid token")
        return

    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        await websocket.send_json({"error": "Invalid token subject"})
        await websocket.close(code=4001, reason="Invalid token subject")
        return

    manager = websocket.app.state.ws_manager
    await manager.connect(user_id, websocket)
    logger.info("WebSocket connected: user_id=%d", user_id)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user_id, websocket)
        logger.info("WebSocket disconnected: user_id=%d", user_id)
