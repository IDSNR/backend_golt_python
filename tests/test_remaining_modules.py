from fastapi.testclient import TestClient

from app.main import app
from conftest import auth_headers

client = TestClient(app)


def test_companies_route() -> None:
    response = client.post("/companies", headers=auth_headers("user-10"), json={"name": "Acme", "handle": "acme"})
    assert response.status_code == 201
    assert response.json()["company"]["handle"] == "acme"


def test_notifications_route() -> None:
    response = client.get("/notifications")
    assert response.status_code == 200
    assert response.json()["notifications"] == []


def test_purchases_route() -> None:
    assert client.post("/purchases", json={"contentId": "content-1", "amountCents": 700}).status_code == 401
    response = client.post("/purchases", headers=auth_headers("user-10"), json={"contentId": "content-1", "amountCents": 700})
    assert response.status_code == 201
    assert response.json()["purchase"]["status"] == "completed"


def test_referrals_route() -> None:
    response = client.post("/referrals", headers=auth_headers("user-2"), json={"referrerId": "user-1", "inviteeId": "spoofed-user"})
    assert response.status_code == 201
    assert response.json()["referral"]["inviteeId"] == "user-2"


def test_reports_route() -> None:
    response = client.post("/reports", headers=auth_headers("user-10"), json={"targetType": "content", "targetId": "content-1", "reason": "spam"})
    assert response.status_code == 201
    assert response.json()["report"]["reason"] == "spam"


def test_sends_route() -> None:
    assert client.post("/sends", json={"senderId": "spoofed", "recipientId": "user-2", "amountCents": 100}).status_code == 401
    response = client.post("/sends", headers=auth_headers("user-1"), json={"senderId": "spoofed", "recipientId": "user-2", "amountCents": 100})
    assert response.status_code == 201
    assert response.json()["send"]["amountCents"] == 100
    assert response.json()["send"]["senderId"] == "user-1"


def test_subscriptions_route() -> None:
    assert client.post("/subscriptions", json={"creatorId": "creator-1", "amountCents": 500}).status_code == 401
    response = client.post("/subscriptions", headers=auth_headers("subscriber-1"), json={"creatorId": "creator-1", "amountCents": 500})
    assert response.status_code == 201
    assert response.json()["subscription"]["status"] == "active"


def test_stories_route() -> None:
    response = client.post("/stories", headers=auth_headers("creator-1"), json={"creatorId": "spoofed-creator", "mediaUrl": "https://example.com/story.mp4"})
    assert response.status_code == 201
    assert response.json()["story"]["creatorId"] == "creator-1"


def test_media_upload_route() -> None:
    files = {"file": ("image.png", b"fake-image", "image/png")}
    response = client.post("/media/upload", headers=auth_headers("user-10"), files=files)
    assert response.status_code == 201
    assert response.json()["media"]["originalFilename"] == "image.png"
