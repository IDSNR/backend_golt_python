from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_content_requires_user_header() -> None:
    response = client.post("/content", json={"videoUrl": "https://example.com/video.mp4"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing X-User-Id header"


def test_create_content_returns_post() -> None:
    response = client.post(
        "/content",
        headers={"X-User-Id": "user-3"},
        json={"videoUrl": "https://example.com/video.mp4", "caption": "hello"},
    )

    assert response.status_code == 201
    assert response.json()["content"]["creatorId"] == "user-3"
    assert response.json()["content"]["caption"] == "hello"
