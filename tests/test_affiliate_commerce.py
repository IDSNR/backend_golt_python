from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.affiliate import AffiliateService
from app.services import affiliate_service, content_service, profile_service
from conftest import auth_headers


client = TestClient(app)


def create_profile(profile_id: str, *, is_private: bool = False) -> None:
    if profile_service.get_profile(profile_id) is None:
        profile_service.create_profile(profile_id, {
            "accountType": "creator",
            "handle": profile_id,
            "displayName": profile_id,
            "isPrivate": is_private,
        })


def test_amazon_url_is_sanitized_and_only_golt_tag_is_used() -> None:
    service = AffiliateService(
        outbound_enabled=True,
        app_environment="production",
        amazon_tags="amazon.es=golt-21",
    )
    public = service.create_offer("content-1", "creator-1", {
        "provider": "amazon",
        "title": "Camera bag",
        "productUrl": "https://www.amazon.es/dp/B000000001?tag=creator-21&ref_=abc#reviews",
    })

    assert "productUrl" not in public
    opened = service.open_offer(service.get_offer(public["id"]), "viewer-1")
    parsed = urlsplit(opened["destinationUrl"])
    assert parsed.fragment == ""
    assert parse_qs(parsed.query)["tag"] == ["golt-21"]
    assert "creator-21" not in opened["destinationUrl"]
    assert opened["commissionTrackingActive"] is True
    assert service.creator_attribution("content-1", "creator-1")["confirmedOrders"] == 0


@pytest.mark.parametrize("url", [
    "http://www.amazon.es/dp/B000000001",
    "https://amzn.to/abc123",
    "https://amazon.es.evil.example/dp/B000000001",
    "https://localhost/dp/B000000001",
    "https://127.0.0.1/dp/B000000001",
    "https://www.amazon.es/s?k=camera",
])
def test_unsafe_or_unsupported_product_links_are_rejected(url: str) -> None:
    service = AffiliateService()
    with pytest.raises(ValueError):
        service.create_offer("content-1", "creator-1", {
            "provider": "amazon",
            "title": "Camera bag",
            "productUrl": url,
        })


def test_production_outbound_links_require_an_enabled_marketplace_tag() -> None:
    service = AffiliateService(app_environment="production")
    public = service.create_offer("content-1", "creator-1", {
        "title": "Camera bag",
        "productUrl": "https://www.amazon.es/dp/B000000001",
    })
    with pytest.raises(RuntimeError):
        service.open_offer(service.get_offer(public["id"]), "viewer-1")


def test_private_offer_visibility_feed_and_click_attribution() -> None:
    creator_id = "affiliate-private-creator"
    outsider_id = "affiliate-private-outsider"
    create_profile(creator_id, is_private=True)
    post = content_service.create_post(creator_id, {
        "videoUrl": "https://example.com/affiliate-private.mp4",
        "visibility": "public",
    })
    created = client.post(
        f"/content/{post['id']}/affiliate-links",
        headers=auth_headers(creator_id),
        json={
            "provider": "amazon",
            "title": "Creator camera",
            "productUrl": "https://www.amazon.es/dp/B000000002?tag=personal-21",
        },
    )
    assert created.status_code == 201
    offer = created.json()["link"]

    assert client.get(f"/content/{post['id']}/affiliate-links").status_code == 404
    assert client.post(f"/affiliate-links/{offer['id']}/open", headers=auth_headers(outsider_id)).status_code == 404
    assert post["id"] not in {item["id"] for item in client.get("/feed").json()["feed"]}

    opened = client.post(f"/affiliate-links/{offer['id']}/open", headers=auth_headers(creator_id))
    assert opened.status_code == 201
    assert opened.json()["open"]["testMode"] is True
    assert "tag=" not in opened.json()["open"]["destinationUrl"]

    attribution = client.get(
        f"/content/{post['id']}/affiliate-attribution",
        headers=auth_headers(creator_id),
    ).json()["attribution"]
    assert attribution["clicks"] == 1
    assert attribution["testClicks"] == 1
    assert attribution["confirmedOrders"] == 0
    assert attribution["creatorCommissionCents"] == 0
    assert client.get(
        f"/content/{post['id']}/affiliate-attribution",
        headers=auth_headers(outsider_id),
    ).status_code == 404


def test_public_feed_contains_safe_offer_card_data() -> None:
    creator_id = "affiliate-public-creator"
    create_profile(creator_id)
    post = content_service.create_post(creator_id, {
        "videoUrl": "https://example.com/affiliate-public.mp4",
        "visibility": "public",
    })
    created = client.post(
        f"/content/{post['id']}/affiliate-links",
        headers=auth_headers(creator_id),
        json={
            "title": "Creator microphone",
            "productUrl": "https://www.amazon.es/dp/B000000003",
        },
    )
    assert created.status_code == 201

    feed_post = next(item for item in client.get("/feed").json()["feed"] if item["id"] == post["id"])
    assert len(feed_post["affiliateOffers"]) == 1
    assert feed_post["affiliateOffers"][0]["title"] == "Creator microphone"
    assert "productUrl" not in feed_post["affiliateOffers"][0]
