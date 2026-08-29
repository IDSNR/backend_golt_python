from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Literal

from app.api.dependencies import get_current_user, get_optional_user
from app.services import content_access_service, content_service

router = APIRouter(prefix="/content", tags=["content"])


class ContentCreateRequest(BaseModel):
    videoUrl: str | None = None
    caption: str | None = None
    visibility: Literal["public", "followers", "subscribers", "private"] = "public"
    mediaItems: list[dict] | None = None


class AffiliateLinkRequest(BaseModel):
    productUrl: str
    retailer: str | None = None


@router.post("", status_code=status.HTTP_201_CREATED)
def create_content(payload: ContentCreateRequest, current_user: str = Depends(get_current_user)) -> dict:
    try:
        post = content_service.create_post(current_user, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"content": post}


@router.get("")
def list_content(current_user: str | None = Depends(get_optional_user)) -> dict:
    content = [
        post for post in content_service.list_posts()
        if content_access_service.can_view_post(current_user, post)
    ]
    return {"content": content}


@router.get("/mine")
def list_my_content(current_user: str = Depends(get_current_user)) -> dict:
    content = content_service.list_posts_by_creator(current_user)
    return {"content": content}


@router.get("/{content_id}/attribution")
def get_content_attribution(content_id: str, current_user: str | None = Depends(get_optional_user)) -> dict:
    post = content_service.get_post(content_id)
    if post is None or not content_access_service.can_view_post(current_user, post):
        raise HTTPException(status_code=404, detail="Content not found")
    from app.services import commerce_service

    attribution = commerce_service.get_content_attribution(content_id)
    return attribution


@router.post("/{content_id}/affiliate-links", status_code=status.HTTP_201_CREATED)
def create_affiliate_link(content_id: str, payload: AffiliateLinkRequest, current_user: str = Depends(get_current_user)) -> dict:
    post = content_service.get_post(content_id)
    if post is None or post["creatorId"] != current_user:
        raise HTTPException(status_code=404, detail="Content not found")
    return {
        "link": {
            "id": f"affiliate-{content_id}-{len(content_service.posts) + 1}",
            "content_id": content_id,
            "product_url": payload.productUrl,
            "retailer": payload.retailer,
            "affiliate_url": f"https://partnerhub.app/go/{content_id}",
        }
    }
