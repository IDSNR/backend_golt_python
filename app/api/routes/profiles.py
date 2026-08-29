from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user, get_optional_user
from app.services import content_access_service, profile_service, content_service, social_service

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


class ProfileUpdateRequest(BaseModel):
    handle: str | None = None
    displayName: str | None = None
    bio: str | None = None
    avatarUrl: str | None = None
    bannerUrl: str | None = None
    websiteUrl: str | None = None
    location: str | None = None
    pronouns: str | None = None
    isPrivate: bool | None = None


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
    return {"profile": _enrich_profile(profile, current_user)}


@router.post("/link-token")
def create_link_token(current_user: str = Depends(get_current_user)) -> dict:
    token_payload = profile_service.create_link_token(current_user)
    return token_payload


@router.post("/me", status_code=status.HTTP_200_OK)
def update_current_profile(payload: ProfileUpdateRequest, current_user: str = Depends(get_current_user)) -> dict:
    try:
        profile = profile_service.update_profile(current_user, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"profile": _enrich_profile(profile, current_user)}


@router.get("/handle/{handle}")
def get_profile_by_handle(handle: str, current_user: str | None = Depends(get_optional_user)) -> dict:
    profile = profile_service.get_profile_by_handle(handle)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    creator_id = profile["id"]
    content = [
        post for post in content_service.list_posts_by_creator(creator_id)
        if content_access_service.can_view_post(current_user, post)
    ]

    return {"profile": _enrich_profile(profile, current_user), "content": content}


def _enrich_profile(profile: dict, viewer_id: str | None) -> dict:
    enriched = profile.copy()
    enriched.update({
        'followerCount': social_service.follower_count(profile['id']),
        'followingCount': social_service.following_count(profile['id']),
        'postCount': len(content_service.list_posts_by_creator(profile['id'])),
        'relationshipStatus': social_service.relationship_status(viewer_id, profile['id']),
    })
    return enriched
