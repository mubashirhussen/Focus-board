from typing import Dict, List
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.core.security import decode_access_token
from app.models.user import User
from app.models.collaboration import WorkspaceMember

logger = logging.getLogger("focusboard.websocket")
router = APIRouter(tags=["WebSockets & Real-Time Collaboration"])

class ConnectionManager:
    def __init__(self):
        # Map workspace_id -> list of active WebSockets
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, workspace_id: int, websocket: WebSocket):
        await websocket.accept()
        if workspace_id not in self.active_connections:
            self.active_connections[workspace_id] = []
        self.active_connections[workspace_id].append(websocket)
        logger.info(f"WebSocket client connected to workspace {workspace_id}")

    def disconnect(self, workspace_id: int, websocket: WebSocket):
        if workspace_id in self.active_connections:
            if websocket in self.active_connections[workspace_id]:
                self.active_connections[workspace_id].remove(websocket)
            if not self.active_connections[workspace_id]:
                del self.active_connections[workspace_id]
        logger.info(f"WebSocket client disconnected from workspace {workspace_id}")

    async def broadcast_to_workspace(self, workspace_id: int, event_type: str, data: dict):
        """Broadcast real-time JSON event to all connected workspace members."""
        if workspace_id not in self.active_connections:
            return

        payload = json.dumps({"event": event_type, "data": data})
        stale_connections = []

        for connection in self.active_connections[workspace_id]:
            try:
                await connection.send_text(payload)
            except Exception:
                stale_connections.append(connection)

        for stale in stale_connections:
            self.disconnect(workspace_id, stale)

ws_manager = ConnectionManager()

@router.websocket("/ws/workspaces/{workspace_id}")
async def websocket_workspace_endpoint(
    websocket: WebSocket,
    workspace_id: int,
    token: str = Query(..., description="JWT Bearer Token for authorization")
):
    """
    Real-time WebSocket collaboration channel for workspaces.
    Enforces JWT authentication and verifies workspace membership before accepting.
    """
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        user_id = int(payload["sub"])
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Verify workspace membership in DB
    db: Session = SessionLocal()
    try:
        membership = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id
        ).first()

        if not membership:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    finally:
        db.close()

    # Accept authorized connection
    await ws_manager.connect(workspace_id, websocket)

    try:
        while True:
            # Listen for client heartbeat pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(workspace_id, websocket)
    except Exception as exc:
        logger.warning(f"WebSocket error in workspace {workspace_id}: {exc}")
        ws_manager.disconnect(workspace_id, websocket)
