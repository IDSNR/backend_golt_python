import asyncio

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.modules.push import service as push_module
from app.modules.push.service import PushNotificationService
from app.main import app
from app.services import direct_message_service, push_notification_service


client = TestClient(app)
AUTH_USER_1 = {"Authorization": "Bearer user-1"}


def test_push_token_registration_requires_authentication_and_validates_token() -> None:
    token = "ExpoPushToken[test-token-123]"
    payload = {"token": token, "platform": "android"}

    assert client.post("/notifications/push-tokens", json=payload).status_code == 401
    assert client.post(
        "/notifications/push-tokens",
        json={"token": "not-a-token", "platform": "android"},
        headers=AUTH_USER_1,
    ).status_code == 422

    response = client.post("/notifications/push-tokens", json=payload, headers=AUTH_USER_1)
    assert response.status_code == 201
    assert push_notification_service.tokens_for_user("user-1") == [token]

    response = client.request("DELETE", "/notifications/push-tokens", json=payload, headers=AUTH_USER_1)
    assert response.status_code == 200
    assert push_notification_service.tokens_for_user("user-1") == []


def test_push_delivery_uses_expo_service_without_exposing_failure_to_messages(monkeypatch) -> None:
    captured: dict = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"data": [{"status": "ok", "id": "ticket-1"}]}

    class FakeAsyncClient:
        def __init__(self, timeout: float) -> None:
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

        async def post(self, url: str, json: list[dict], headers: dict) -> FakeResponse:
            captured.update({"url": url, "messages": json, "headers": headers})
            return FakeResponse()

    monkeypatch.setattr(push_module.httpx, "AsyncClient", FakeAsyncClient)
    service = PushNotificationService()
    service.register("user-2", "ExpoPushToken[recipient-token]", "ios")

    result = asyncio.run(service.send_to_user("user-2", "New message", "Hello", {"threadId": "thread-1"}))

    assert result == {"data": [{"status": "ok", "id": "ticket-1"}]}
    assert captured["messages"][0]["to"] == "ExpoPushToken[recipient-token]"
    assert captured["messages"][0]["data"] == {"threadId": "thread-1"}


def test_realtime_connection_rejects_missing_session() -> None:
    try:
        with client.websocket_connect("/realtime") as websocket:
            websocket.send_json({"type": "authenticate", "token": "invalid"})
            websocket.receive_json()
    except WebSocketDisconnect as exc:
        assert exc.code == 4401


def test_direct_message_is_delivered_to_connected_recipient() -> None:
    thread = direct_message_service.create_thread("user-1", "user-2", "Initial message")

    with client.websocket_connect("/realtime") as websocket:
        websocket.send_json({"type": "authenticate", "token": "user-2"})
        assert websocket.receive_json() == {"type": "connected"}

        response = client.post(
            f"/dms/{thread['id']}/messages",
            json={"content": "Live hello"},
            headers=AUTH_USER_1,
        )
        assert response.status_code == 201

        event = websocket.receive_json()
        assert event["type"] == "direct_message"
        assert event["threadId"] == thread["id"]
        assert event["message"]["content"] == "Live hello"
