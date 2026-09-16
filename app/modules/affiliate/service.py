from __future__ import annotations

from datetime import datetime, timezone
import ipaddress
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import uuid4


class AffiliateService:
    AMAZON_DOMAINS = {
        "amazon.com",
        "amazon.co.uk",
        "amazon.com.be",
        "amazon.de",
        "amazon.es",
        "amazon.fr",
        "amazon.it",
        "amazon.nl",
        "amazon.pl",
        "amazon.se",
    }
    AMAZON_DISCLOSURE = (
        "(enlace pagado) En calidad de Afiliado de Amazon, obtengo ingresos "
        "por las compras adscritas que cumplen los requisitos aplicables."
    )

    def __init__(
        self,
        *,
        outbound_enabled: bool = False,
        app_environment: str = "development",
        amazon_tags: str = "",
    ) -> None:
        self.outbound_enabled = outbound_enabled
        self.app_environment = app_environment.lower()
        self.amazon_tags = self._parse_tags(amazon_tags)
        self.offers: list[dict] = []
        self.clicks: list[dict] = []

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _parse_tags(raw: str) -> dict[str, str]:
        tags: dict[str, str] = {}
        for item in raw.split(","):
            if "=" not in item:
                continue
            domain, tag = (part.strip().lower() for part in item.split("=", 1))
            if domain and tag:
                tags[domain.removeprefix("www.")] = tag
        return tags

    @staticmethod
    def _is_private_host(host: str) -> bool:
        if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
            return True
        try:
            return ipaddress.ip_address(host).is_private or ipaddress.ip_address(host).is_loopback
        except ValueError:
            return False

    def _sanitize_amazon_url(self, raw_url: str) -> tuple[str, str]:
        parsed = urlsplit(raw_url.strip())
        if parsed.scheme != "https":
            raise ValueError("Amazon product links must use HTTPS")
        if parsed.username or parsed.password or parsed.port:
            raise ValueError("Amazon product link contains unsupported credentials or port")

        host = (parsed.hostname or "").lower().rstrip(".")
        canonical_host = host.removeprefix("www.")
        if not host or self._is_private_host(host):
            raise ValueError("Amazon product link has an unsafe host")
        if canonical_host not in self.AMAZON_DOMAINS:
            raise ValueError("Use a direct link from a supported Amazon marketplace")
        if not parsed.path or parsed.path == "/":
            raise ValueError("Link directly to an Amazon product page")

        if re.search(r"/(?:dp|gp/product)/[A-Z0-9]{10}(?:[/?]|$)", parsed.path, flags=re.IGNORECASE) is None:
            raise ValueError("Link directly to an Amazon product details page")

        # A creator supplies only the product identity. Golt owns every tracking
        # parameter so personal affiliate tags and opaque campaign data cannot
        # be smuggled through the app.
        clean_url = urlunsplit(("https", host, parsed.path, "", ""))
        return clean_url, canonical_host

    def create_offer(self, content_id: str, creator_id: str, payload: dict) -> dict:
        if payload.get("provider", "amazon") != "amazon":
            raise ValueError("Amazon is the only affiliate provider available in this release")
        product_url, marketplace = self._sanitize_amazon_url(payload.get("productUrl", ""))
        title = str(payload.get("title", "")).strip()
        if not title:
            raise ValueError("Product title is required")
        if len(title) > 160:
            raise ValueError("Product title must be 160 characters or fewer")

        now = self._now_iso()
        offer = {
            "id": f"affiliate-{uuid4()}",
            "contentId": content_id,
            "creatorId": creator_id,
            "provider": "amazon",
            "merchantName": "Amazon",
            "marketplace": marketplace,
            "title": title,
            "productUrl": product_url,
            "disclosure": self.AMAZON_DISCLOSURE,
            "createdAt": now,
            "status": "active",
        }
        self.offers.append(offer)
        return self.public_offer(offer)

    def public_offer(self, offer: dict) -> dict:
        return {
            key: value
            for key, value in offer.items()
            if key not in {"productUrl", "creatorId"}
        } | {
            "commissionTrackingActive": bool(
                self.outbound_enabled and self.amazon_tags.get(offer["marketplace"])
            ),
            "priceNotice": "Price, availability, delivery, returns, and checkout are controlled by Amazon.",
        }

    def list_content_offers(self, content_id: str) -> list[dict]:
        return [
            self.public_offer(offer)
            for offer in self.offers
            if offer["contentId"] == content_id and offer["status"] == "active"
        ]

    def get_offer(self, offer_id: str) -> dict | None:
        return next((offer for offer in self.offers if offer["id"] == offer_id), None)

    def open_offer(self, offer: dict, viewer_id: str | None) -> dict:
        tag = self.amazon_tags.get(offer["marketplace"])
        tracking_active = bool(self.outbound_enabled and tag)
        if self.app_environment == "production" and not tracking_active:
            raise RuntimeError("Affiliate outbound links are not configured for this Amazon marketplace")

        destination = offer["productUrl"]
        if tracking_active:
            parsed = urlsplit(destination)
            query = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True) if key.lower() != "tag"]
            query.append(("tag", tag))
            destination = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), ""))

        click = {
            "id": f"affiliate-click-{uuid4()}",
            "offerId": offer["id"],
            "contentId": offer["contentId"],
            "creatorId": offer["creatorId"],
            "viewerId": viewer_id,
            "openedAt": self._now_iso(),
            "testMode": not tracking_active,
        }
        self.clicks.append(click)
        return {
            "clickId": click["id"],
            "destinationUrl": destination,
            "merchantName": offer["merchantName"],
            "disclosure": offer["disclosure"],
            "testMode": click["testMode"],
            "commissionTrackingActive": tracking_active,
            "notice": (
                "Preview only. This click cannot earn commission until Golt's approved Amazon tracking ID is enabled."
                if click["testMode"]
                else "Amazon will decide whether a later order qualifies for commission."
            ),
        }

    def creator_attribution(self, content_id: str, creator_id: str) -> dict:
        matching_offers = [offer for offer in self.offers if offer["contentId"] == content_id and offer["creatorId"] == creator_id]
        offer_ids = {offer["id"] for offer in matching_offers}
        clicks = [click for click in self.clicks if click["offerId"] in offer_ids]
        return {
            "contentId": content_id,
            "offerCount": len(matching_offers),
            "clicks": len(clicks),
            "testClicks": sum(1 for click in clicks if click["testMode"]),
            "confirmedOrders": 0,
            "confirmedCommissionCents": 0,
            "creatorCommissionCents": 0,
            "settlementStatus": "provider_reports_not_connected",
            "notice": "A click is not a sale. Orders and creator commission remain zero until Amazon confirms qualifying purchases in its reports.",
        }
