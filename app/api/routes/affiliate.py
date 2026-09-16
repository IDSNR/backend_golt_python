from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_optional_user
from app.services import affiliate_service, content_access_service, content_service

router = APIRouter(prefix="/affiliate-links", tags=["affiliate"])


@router.post("/{offer_id}/open", status_code=status.HTTP_201_CREATED)
def open_affiliate_link(offer_id: str, current_user: str | None = Depends(get_optional_user)) -> dict:
    offer = affiliate_service.get_offer(offer_id)
    if offer is None or offer.get("status") != "active":
        raise HTTPException(status_code=404, detail="Affiliate offer not found")

    post = content_service.get_post(offer["contentId"])
    if post is None or not content_access_service.can_view_post(current_user, post):
        raise HTTPException(status_code=404, detail="Affiliate offer not found")

    try:
        opened = affiliate_service.open_offer(offer, current_user)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"open": opened}
