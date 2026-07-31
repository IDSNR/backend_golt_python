from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user, get_optional_user
from app.services import profile_service, content_service, social_service

router = APIRouter(prefix="/profiles", tags=["profiles"])


class ProfileCreateRequest(BaseModel):
    accountType: str = Field(..., description="standard or creator")
    handle: str
    displayName: str
    countryCode: str | None = None
    dateOfBirth: str | None = None
    bio: str | None = None
    avatarUrl: str | None = None
    isPrivate: bool = False
    identityLinkToken: str | None = None


@router.post("", status_code=status.HTTP_201_CREATED)
def create_profile(payload: ProfileCreateRequest, current_user: str = Depends(get_current_user)) -> dict:
    try:
        profile = profile_service.create_profile(current_user, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"profile": profile}


@router.get("/me")
def get_current_profile(current_user: str = Depends(get_current_user)) -> dict:
    profile = profile_service.get_profile(current_user)
    if profile is None:
        profile = profile_service.ensure_profile(current_user)
    return {"profile": profile}


@router.post("/link-token")
def create_link_token(current_user: str = Depends(get_current_user)) -> dict:
    token_payload = profile_service.create_link_token(current_user)
    return token_payload


@router.get("/handle/{handle}")
def get_profile_by_handle(handle: str, current_user: str | None = Depends(get_optional_user)) -> dict:
    profile = profile_service.get_profile_by_handle(handle)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    creator_id = profile["id"]
    if profile.get("is_private") and current_user is not None:
        allowed = social_service.is_approved_follower(current_user, creator_id)
        content = content_service.list_posts_by_creator(creator_id) if allowed else []
    elif profile.get("is_private") and current_user is None:
        content = []
    else:
        content = content_service.list_posts_by_creator(creator_id)

    return {"profile": profile, "content": content}
