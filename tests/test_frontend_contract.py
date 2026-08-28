from fastapi.testclient import TestClient

from app.main import app
from conftest import auth_headers

client = TestClient(app)


def test_profiles_me_uses_bearer_auth_and_returns_profile_shape() -> None:
    response = client.get("/profiles/me", headers=auth_headers("user-frontend"))

    assert response.status_code == 200
    assert response.json()["profile"]["id"] == "user-frontend"


def test_follows_requests_use_frontend_field_names() -> None:
    client.post(
        "/follows",
        headers=auth_headers("follower-1"),
        json={"followeeProfileId": "creator-1"},
    )

    response = client.get("/follows/requests", headers=auth_headers("creator-1"))

    assert response.status_code == 200
    assert response.json()["requests"][0]["follower_profile_id"] == "follower-1"


def test_notifications_and_media_upload_match_frontend_shapes() -> None:
    notifications_response = client.get("/notifications", headers=auth_headers("user-1"))
    assert notifications_response.status_code == 200
    assert "unreadCount" in notifications_response.json()

    files = {"file": ("image.png", b"fake-image", "image/png")}
    upload_response = client.post("/media/upload", headers=auth_headers("user-1"), files=files)

    assert upload_response.status_code == 201
    assert upload_response.json()["mediaType"] == "image"
    assert upload_response.json()["url"].startswith("/media/files/")
    assert upload_response.json()["media"]["originalFilename"] == "image.png"
