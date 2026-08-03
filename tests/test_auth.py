from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_and_login_flow():
    payload = {
        "email": "demo@example.com",
        "password": "P@ssword123",
        "displayName": "Demo User",
    }

    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == payload["email"]
    assert body["user"]["displayName"] == payload["displayName"]
    assert body["token"]

    login_response = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login_response.status_code == 200
    assert login_response.json()["token"] == body["token"]


def test_duplicate_email_is_rejected():
    payload = {
        "email": "duplicate@example.com",
        "password": "P@ssword123",
        "displayName": "Duplicate User",
    }

    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/register", json=payload)
    assert second.status_code == 409
    assert "already exists" in second.json()["detail"].lower()
