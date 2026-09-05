from fastapi.testclient import TestClient

from app.main import app
from app.services import content_service, profile_service, social_service
from conftest import auth_headers


client = TestClient(app)


def ensure_creator(profile_id: str) -> None:
    if profile_service.get_profile(profile_id) is None:
        profile_service.create_profile(profile_id, {
            "accountType": "creator",
            "handle": profile_id,
            "displayName": profile_id,
            "isPrivate": False,
        })


def test_following_feed_contains_only_accessible_posts_from_followed_creators() -> None:
    viewer_id = "feed-mode-viewer"
    followed_id = "feed-mode-followed"
    discovery_id = "feed-mode-discovery"
    ensure_creator(followed_id)
    ensure_creator(discovery_id)

    public_post = content_service.create_post(followed_id, {
        "videoUrl": "https://example.com/followed-public.mp4",
        "visibility": "public",
    })
    followers_post = content_service.create_post(followed_id, {
        "videoUrl": "https://example.com/followed-members.mp4",
        "visibility": "followers",
    })
    discovery_post = content_service.create_post(discovery_id, {
        "videoUrl": "https://example.com/discovery.mp4",
        "visibility": "public",
    })
    social_service.follow(viewer_id, followed_id, followee_is_private=False)

    response = client.get("/feed", params={"mode": "following"}, headers=auth_headers(viewer_id))

    assert response.status_code == 200
    assert response.json()["mode"] == "following"
    post_ids = {post["id"] for post in response.json()["feed"]}
    assert public_post["id"] in post_ids
    assert followers_post["id"] in post_ids
    assert discovery_post["id"] not in post_ids


def test_for_you_remains_the_default_discovery_feed() -> None:
    creator_id = "feed-mode-for-you"
    ensure_creator(creator_id)
    post = content_service.create_post(creator_id, {
        "videoUrl": "https://example.com/for-you.mp4",
        "visibility": "public",
    })

    response = client.get("/feed")

    assert response.status_code == 200
    assert response.json()["mode"] == "for_you"
    assert post["id"] in {item["id"] for item in response.json()["feed"]}


def test_following_feed_requires_sign_in() -> None:
    response = client.get("/feed", params={"mode": "following"})

    assert response.status_code == 401
