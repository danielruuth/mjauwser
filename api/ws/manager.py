from fastapi import WebSocket
from typing import Any
import json
import uuid
import time
from ws.events import CONNECTED, DISCONNECTED


class ConnectionInfo:
    def __init__(self, ws: WebSocket, role: str, *,
                 device_type: str | None = None,
                 device_id: str | None = None,
                 device_name: str | None = None,
                 ring_id: int | None = None,
                 ring_number: int | None = None,
                 show_id: int | None = None,
                 day_id: int | None = None):
        self.id = uuid.uuid4().hex[:8]
        self.ws = ws
        self.role = role
        self.device_type = device_type
        self.device_id = device_id
        self.device_name = device_name
        self.ring_id = ring_id
        self.ring_number = ring_number
        self.show_id = show_id
        self.day_id = day_id
        self.connected_at = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "device_type": self.device_type,
            "device_id": self.device_id,
            "device_name": self.device_name,
            "ring_id": self.ring_id,
            "ring_number": self.ring_number,
            "show_id": self.show_id,
            "day_id": self.day_id,
            "connected_at": self.connected_at,
        }


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, ConnectionInfo] = {}
        self._admin_connections: dict[str, ConnectionInfo] = {}
        self._display_connections: dict[str, ConnectionInfo] = {}
        self._judge_connections: dict[str, ConnectionInfo] = {}
        self._ring_judge_map: dict[int, str] = {}

    async def connect_admin(self, ws: WebSocket) -> ConnectionInfo:
        await ws.accept()
        info = ConnectionInfo(ws, "admin")
        self._connections[info.id] = info
        self._admin_connections[info.id] = info
        await self._broadcast_connected(info)
        return info

    async def connect_display(self, ws: WebSocket, *,
                              device_type: str | None = None,
                              device_id: str | None = None,
                              device_name: str | None = None,
                              ring_id: int | None = None,
                              ring_number: int | None = None,
                              show_id: int | None = None,
                              day_id: int | None = None) -> ConnectionInfo:
        await ws.accept()
        info = ConnectionInfo(ws, "display", device_type=device_type,
                              device_id=device_id, device_name=device_name,
                              ring_id=ring_id, ring_number=ring_number,
                              show_id=show_id, day_id=day_id)
        self._connections[info.id] = info
        self._display_connections[info.id] = info
        await self._broadcast_connected(info)
        return info

    async def connect_judge(self, ws: WebSocket, ring_id: int, *,
                             ring_number: int | None = None,
                             show_id: int | None = None,
                             day_id: int | None = None) -> ConnectionInfo:
        await ws.accept()
        info = ConnectionInfo(ws, "judge", device_type="panel",
                              ring_id=ring_id, ring_number=ring_number,
                              show_id=show_id, day_id=day_id)
        self._connections[info.id] = info
        self._judge_connections[info.id] = info
        self._ring_judge_map[ring_id] = info.id
        await self._broadcast_connected(info)
        return info

    async def disconnect(self, ws: WebSocket):
        conn_id = self._find_connection_id(ws)
        if conn_id is None:
            return
        info = self._connections.pop(conn_id, None)
        if info is None:
            return
        self._admin_connections.pop(conn_id, None)
        self._display_connections.pop(conn_id, None)
        self._judge_connections.pop(conn_id, None)
        if info.role == "judge" and info.ring_id is not None:
            existing = self._ring_judge_map.get(info.ring_id)
            if existing == conn_id:
                del self._ring_judge_map[info.ring_id]
        await self._broadcast_disconnected(info)

    def _find_connection_id(self, ws: WebSocket) -> str | None:
        for conn_id, info in self._connections.items():
            if info.ws is ws:
                return conn_id
        return None

    def get_connections(self) -> list[dict[str, Any]]:
        return [info.to_dict() for info in self._connections.values()]

    async def broadcast(self, event: str, payload: dict[str, Any]):
        message = json.dumps({"event": event, "payload": payload})
        for info in list(self._connections.values()):
            try:
                await info.ws.send_text(message)
            except Exception:
                pass

    async def broadcast_to_role(self, role: str, event: str, payload: dict[str, Any], ring_id: int | None = None):
        message = json.dumps({"event": event, "payload": payload})
        targets: list[ConnectionInfo] = []
        if role == "admin":
            targets = list(self._admin_connections.values())
        elif role == "display":
            targets = list(self._display_connections.values())
        elif role == "judge" and ring_id is not None:
            conn_id = self._ring_judge_map.get(ring_id)
            if conn_id and conn_id in self._connections:
                targets = [self._connections[conn_id]]
        for info in targets:
            try:
                await info.ws.send_text(message)
            except Exception:
                pass

    async def broadcast_to_all_judges(self, event: str, payload: dict[str, Any]):
        message = json.dumps({"event": event, "payload": payload})
        for info in self._judge_connections.values():
            try:
                await info.ws.send_text(message)
            except Exception:
                pass

    async def _broadcast_connected(self, info: ConnectionInfo):
        await self._broadcast_to_all_except(info.id, CONNECTED, {"connection": info.to_dict()})

    async def _broadcast_disconnected(self, info: ConnectionInfo):
        await self._broadcast_to_all_except(info.id, DISCONNECTED, {"connection": info.to_dict()})

    async def _broadcast_to_all_except(self, exclude_id: str, event: str, payload: dict[str, Any]):
        message = json.dumps({"event": event, "payload": payload})
        for conn_id, info in self._connections.items():
            if conn_id == exclude_id:
                continue
            try:
                await info.ws.send_text(message)
            except Exception:
                pass


manager = ConnectionManager()
