from fastapi.testclient import TestClient

from app.main import app
from app.services import content_service, profile_service, social_service, story_service, subscription_service
from conftest import auth_headers


client = TestClient(app)


def create_profile(profile_id: str, *, is_private: bool) -> None:
    if profile_service.get_profile(profile_id) is None:
        profile_service.create_profile(profile_id, {
            "accountType": "creator",
            "handle": profile_id,
            "displayName": profile_id,
            "isPrivate": is_private,
        })


def test_private_creator_content_and_story_require_approved_following() -> None:
    creator_id = "privacy-private-creator"
    viewer_id = "privacy-approved-viewer"
    outsider_id = "privacy-outsider"
    create_profile(creator_id, is_private=True)
    post = content_service.create_post(creator_id, {
        "videoUrl": "https://example.com/private.mp4",
        "caption": "privacy-private-caption",
        "visibility": "public",
    })
    story = story_service.post_story(creator_id, {
        "mediaUrl": "https://example.com/private-story.mp4",
        "mediaType": "video",
    })

    public_ids = {item["id"] for item in client.get("/content").json()["content"]}
    assert post["id"] not in public_ids
    assert client.get(f"/content/{post['id']}/engagement", headers=auth_headers(viewer_id)).status_code == 404
    assert client.get("/search", params={"query": "privacy-private-caption"}).json()["posts"] == []
    assert client.post(f"/stories/{story['id']}/view", headers=auth_headers(viewer_id)).status_code == 404
    assert client.get(f"/stories/{story['id']}/viewers", headers=auth_headers(outsider_id)).status_code == 404

    request = social_service.follow(viewer_id, creator_id, followee_is_private=True)
    social_service.approve(request["id"], creator_id)

    visible_ids = {item["id"] for item in client.get("/content", headers=auth_headers(viewer_id)).json()["content"]}
    assert post["id"] in visible_ids
    assert client.post(f"/content/{post['id']}/like", headers=auth_headers(viewer_id)).status_code == 200
    assert client.post(f"/stories/{story['id']}/view", headers=auth_headers(viewer_id)).status_code == 201
    viewers = client.get(f"/stories/{story['id']}/viewers", headers=auth_headers(creator_id)).json()["viewers"]
    assert any(item["viewerProfileId"] == viewer_id for item in viewers)


def test_per_post_visibility_rules_are_applied_everywhere() -> None:
    creator_id = "privacy-public-creator"
    follower_id = "privacy-follower"
    subscriber_id = "privacy-subscriber"
    create_profile(creator_id, is_private=False)

    followers_post = content_service.create_post(creator_id, {
        "videoUrl": "https://example.com/followers.mp4",
        "visibility": "followers",
    })
    subscribers_post = content_service.create_post(creator_id, {
        "videoUrl": "https://example.com/subscribers.mp4",
        "visibility": "subscribers",
    })
    private_post = content_service.create_post(creator_id, {
        "videoUrl": "https://example.com/author-only.mp4",
        "visibility": "private",
    })

    assert client.get(f"/content/{followers_post['id']}/comments", headers=auth_headers(follower_id)).status_code == 404
    social_service.follow(follower_id, creator_id, followee_is_private=False)
    assert client.get(f"/content/{followers_post['id']}/comments", headers=auth_headers(follower_id)).status_code == 200

    assert client.get(f"/content/{subscribers_post['id']}/engagement", headers=auth_headers(subscriber_id)).status_code == 404
    subscription_service.subscribe(subscriber_id, creator_id)
    assert client.get(f"/content/{subscribers_post['id']}/engagement", headers=auth_headers(subscriber_id)).status_code == 200

    assert client.get(f"/content/{private_post['id']}/engagement", headers=auth_headers(follower_id)).status_code == 404
    assert client.get(f"/content/{private_post['id']}/engagement", headers=auth_headers(creator_id)).status_code == 200
    assert client.get(f"/profiles/handle/{creator_id}", headers=auth_headers(follower_id)).status_code == 200
    profile_posts = client.get(f"/profiles/handle/{creator_id}", headers=auth_headers(follower_id)).json()["content"]
    assert private_post["id"] not in {item["id"] for item in profile_posts}


def test_visibility_validation_and_affiliate_link_ownership() -> None:
    creator_id = "privacy-affiliate-owner"
    outsider_id = "privacy-affiliate-outsider"
    create_profile(creator_id, is_private=False)

    invalid = client.post(
        "/content",
        headers=auth_headers(creator_id),
        json={"videoUrl": "https://example.com/video.mp4", "visibility": "anyone-who-guesses"},
    )
    assert invalid.status_code == 422

    post = content_service.create_post(creator_id, {
        "videoUrl": "https://example.com/affiliate.mp4",
        "visibility": "public",
    })
    payload = {"productUrl": "https://shop.example/item"}
    assert client.post(
        f"/content/{post['id']}/affiliate-links",
        headers=auth_headers(outsider_id),
        json=payload,
    ).status_code == 404
    assert client.post(
        f"/content/{post['id']}/affiliate-links",
        headers=auth_headers(creator_id),
        json=payload,
    ).status_code == 201
