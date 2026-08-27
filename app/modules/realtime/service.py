from fastapi import WebSocket


class RealtimeService:
    def __init__(self) -> None:
        # Connections are intentionally process-local until shared infrastructure is selected.
        self.connections: dict[str, set[WebSocket]] = {}

    def connect(self, user_id: str, websocket: WebSocket) -> None:
        self.connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        user_connections = self.connections.get(user_id)
        if user_connections is None:
            return
        user_connections.discard(websocket)
        if not user_connections:
            self.connections.pop(user_id, None)

    async def send_to_users(self, user_ids: list[str], event: dict) -> None:
        for user_id in user_ids:
            for connection in list(self.connections.get(user_id, set())):
                try:
                    await connection.send_json(event)
                except RuntimeError:
                    self.disconnect(user_id, connection)
