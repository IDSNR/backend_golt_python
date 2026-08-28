from fastapi.testclient import TestClient

from app.main import app
from conftest import auth_headers

client = TestClient(app)


def test_follow_request_is_created() -> None:
    response = client.post("/social/follow", headers=auth_headers("user-1"), json={"followerId": "user-1", "followeeId": "user-2"})

    assert response.status_code == 201
    assert response.json()["followRequest"]["status"] == "pending"


def test_follow_approval_updates_request() -> None:
    create_response = client.post("/social/follow", headers=auth_headers("user-3"), json={"followerId": "user-3", "followeeId": "user-4"})
    request_id = create_response.json()["followRequest"]["id"]

    response = client.post("/social/follow-requests/approve", headers=auth_headers("user-4"), json={"requestId": request_id})

    assert response.status_code == 200
    assert response.json()["followRequest"]["status"] == "approved"
