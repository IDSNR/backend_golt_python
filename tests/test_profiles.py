from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_profile_rejects_invalid_account_type() -> None:
    response = client.post(
        "/profiles",
        headers={"X-User-Id": "user-1"},
        json={"accountType": "invalid", "handle": "alice", "displayName": "Alice"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "accountType must be 'standard' or 'creator'"


def test_create_profile_accepts_valid_payload() -> None:
    response = client.post(
        "/profiles",
        headers={"X-User-Id": "user-2"},
        json={"accountType": "creator", "handle": "creatorone", "displayName": "Creator One"},
    )

    assert response.status_code == 201
    assert response.json()["profile"]["handle"] == "creatorone"
    assert response.json()["profile"]["accountType"] == "creator"
